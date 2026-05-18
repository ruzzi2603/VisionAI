import { useEffect, useRef } from "react";

export default function MJPEGStream({ src, alt = "MJPEG Stream" }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!src) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let isRunning = true;

    const fetchStream = async () => {
      try {
        const response = await fetch(src);
        if (!response.ok) {
          console.error("Stream error:", response.status);
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (isRunning) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Extract JPEG from multipart
          const boundary = "--frame";
          const parts = buffer.split(boundary);

          for (let i = 1; i < parts.length - 1; i++) {
            const part = parts[i];
            const jpegStart = part.indexOf("\r\n\r\n");
            if (jpegStart === -1) continue;

            const jpegEnd = parts[i + 1].indexOf("\r\n");
            if (jpegEnd === -1) continue;

            const jpegData = part.substring(jpegStart + 4);
            const jpegBytes = new Uint8Array(
              jpegData.split("").map((c) => c.charCodeAt(0))
            );

            const blob = new Blob([jpegBytes], { type: "image/jpeg" });
            const url = URL.createObjectURL(blob);
            const img = new Image();

            img.onload = () => {
              canvas.width = img.width;
              canvas.height = img.height;
              ctx.drawImage(img, 0, 0);
              URL.revokeObjectURL(url);
            };

            img.src = url;
          }

          buffer = parts[parts.length - 1];
        }
      } catch (error) {
        console.error("MJPEG stream error:", error);
      }
    };

    fetchStream();

    return () => {
      isRunning = false;
    };
  }, [src]);

  return (
    <canvas
      ref={canvasRef}
      alt={alt}
      className="w-full rounded-lg border border-cyan-500/40 bg-slate-950"
      style={{ minHeight: "400px" }}
    />
  );
}
