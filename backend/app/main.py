import time
import random
import logging
import mysql.connector
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from .db import get_connection
from .inference import predict_move

# ---- Logging setup ----
logging.basicConfig(
    level=logging.INFO,  # zet op logging.DEBUG voor meer detail
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
logger = logging.getLogger("rps_api")

app = FastAPI(title="RPS Inference API")

@app.on_event("startup")
def startup():
    logger.info("Startup: begin DB readiness check")

    deadline = time.time() + 90
    attempt = 0

    conn = None
    while True:
        attempt += 1
        try:
            logger.info("Startup: DB connect attempt %d", attempt)
            conn = get_connection()
            logger.info("Startup: DB connection OK")
            break
        except mysql.connector.Error as e:
            logger.warning("Startup: DB connect failed (attempt %d): %s", attempt, str(e))
            if time.time() > deadline:
                logger.error("Startup: DB not ready after 90s, raising error")
                raise
            time.sleep(2)

    try:
        cur = conn.cursor()
        logger.info("Startup: ensuring table exists: games")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INT AUTO_INCREMENT PRIMARY KEY,
                player_move VARCHAR(16) NOT NULL,
                computer_move VARCHAR(16) NOT NULL,
                winner VARCHAR(16) NOT NULL
            )
        """)

        logger.info("Startup: table check/create OK")
        cur.close()
    except Exception:
        logger.exception("Startup: error while creating table")
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass

@app.post("/play")
async def play(request: Request, file: UploadFile = File(...)):
    start = time.perf_counter()

    logger.info("POST /play from %s", request.client.host if request.client else "unknown")
    logger.info("Incoming file: filename=%s content_type=%s",
                file.filename, file.content_type)

    # Validate content type
    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning("Invalid file type: %s", file.content_type)
        raise HTTPException(status_code=400, detail="Invalid file")

    # Read bytes
    try:
        image_bytes = await file.read()
        logger.info("Read %d bytes from upload", len(image_bytes))
        if len(image_bytes) == 0:
            logger.warning("Uploaded file has 0 bytes")
            raise HTTPException(status_code=400, detail="Empty file")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed reading uploaded file")
        raise HTTPException(status_code=500, detail="Failed to read upload")

    # Predict move
    try:
        player_move = predict_move(image_bytes)
        logger.info("Predicted player_move=%s", player_move)
    except Exception:
        logger.exception("predict_move failed")
        raise HTTPException(status_code=500, detail="Prediction failed")

    # Pick computer move
    computer_move = random.choice(["rock", "paper", "scissors"])
    logger.info("Computer move=%s", computer_move)

    # Decide winner
    if player_move == computer_move:
        winner = "Tie"
    elif (
        (player_move == "rock" and computer_move == "scissors") or
        (player_move == "paper" and computer_move == "rock") or
        (player_move == "scissors" and computer_move == "paper")
    ):
        winner = "Player"
    else:
        winner = "Computer"

    logger.info("Winner=%s", winner)

    # DB insert
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        logger.info("DB: inserting game row")
        cur.execute(
            "INSERT INTO games (player_move, computer_move, winner) VALUES (%s, %s, %s)",
            (player_move, computer_move, winner)
        )
        conn.commit()

        inserted_id = cur.lastrowid
        logger.info("DB: insert OK (id=%s)", inserted_id)
    except mysql.connector.Error as e:
        logger.exception("DB error during insert: %s", str(e))
        raise HTTPException(status_code=500, detail="Database insert failed")
    except Exception:
        logger.exception("Unexpected error during insert")
        raise HTTPException(status_code=500, detail="Database insert failed")
    finally:
        try:
            if cur is not None:
                cur.close()
        except Exception:
            pass
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("POST /play done in %.1fms", elapsed_ms)

    return {
        "prediction": player_move,
        "computer": computer_move,
        "winner": winner
    }

@app.get("/games")
def get_games(request: Request, limit: int = 50):
    start = time.perf_counter()

    logger.info("GET /games from %s limit=%d",
                request.client.host if request.client else "unknown",
                limit)

    # Basic limit guard (handig tegen extreme queries)
    if limit < 1:
        logger.warning("Invalid limit=%d (must be >= 1)", limit)
        raise HTTPException(status_code=400, detail="limit must be >= 1")
    if limit > 500:
        logger.warning("Limit too high (%d), clamping to 500", limit)
        limit = 500

    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        logger.info("DB: selecting last %d games", limit)
        cur.execute("""
            SELECT id, player_move, computer_move, winner
            FROM games
            ORDER BY id DESC
            LIMIT %s
        """, (limit,))

        rows = cur.fetchall()
        logger.info("DB: fetched %d rows", len(rows))
    except mysql.connector.Error as e:
        logger.exception("DB error during select: %s", str(e))
        raise HTTPException(status_code=500, detail="Database query failed")
    except Exception:
        logger.exception("Unexpected error during select")
        raise HTTPException(status_code=500, detail="Database query failed")
    finally:
        try:
            if cur is not None:
                cur.close()
        except Exception:
            pass
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("GET /games done in %.1fms", elapsed_ms)

    return rows
