window.rpsCamera = (function () {
    let stream = null;

    async function start(videoElementId) {
        const video = document.getElementById(videoElementId);
        if (!video) throw new Error("Video element not found.");

        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "user" },
            audio: false
        });

        video.srcObject = stream;
        await video.play();
    }

    function stop() {
        if (!stream) return;
        for (const track of stream.getTracks()) track.stop();
        stream = null;
    }

    // Maakt een foto van de huidige video-frame
    // en geeft een Base64 string terug (zonder data:... prefix).
    async function captureJpegBase64(videoElementId, width, height, quality) {
        const video = document.getElementById(videoElementId);
        if (!video) throw new Error("Video element not found.");

        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, width, height);

        const blob = await new Promise(resolve => {
            canvas.toBlob(resolve, "image/jpeg", quality);
        });

        if (!blob) throw new Error("Failed to create JPEG blob.");

        const arrayBuffer = await blob.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);

        // Zet bytes om naar Base64 zodat Blazor het makkelijk kan ontvangen
        let binary = "";
        for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
        return btoa(binary);
    }

    return { start, stop, captureJpegBase64 };
})();
