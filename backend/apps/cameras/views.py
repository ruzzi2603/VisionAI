import os
import cv2
import time
import subprocess
import psutil
from django.core import signing
from django.http import StreamingHttpResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Camera
from .serializers import CameraSerializer


class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.order_by("id")
    serializer_class = CameraSerializer
    _vision_process = None

    def _open_capture(self, camera: Camera):
        source = camera.stream_url.strip() if camera.stream_url else camera.source.strip()
        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        if source.isdigit():
            return cv2.VideoCapture(int(source), backend)
        return cv2.VideoCapture(source, backend)

    def _discover_local_indices(self, max_index: int = 3):
        backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        found = []
        for idx in range(0, max_index + 1):
            cap = cv2.VideoCapture(idx, backend)
            ok, _ = cap.read()
            cap.release()
            if ok:
                found.append(idx)
        return found

    def _mjpeg_generator(self, camera: Camera):
        cap = self._open_capture(camera)
        target_fps = 15.0
        frame_interval = 1.0 / target_fps
        jpeg_quality = 50
        stream_width = 640
        last_sent = 0.0
        try:
            while cap.isOpened():
                ok, frame = cap.read()
                if not ok:
                    break
                h, w = frame.shape[:2]
                if w > stream_width:
                    ratio = stream_width / float(w)
                    frame = cv2.resize(frame, (stream_width, int(h * ratio)))

                now = time.monotonic()
                dt = now - last_sent
                if dt < frame_interval:
                    time.sleep(frame_interval - dt)

                ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
                if not ok:
                    continue
                chunk = buffer.tobytes()
                last_sent = time.monotonic()
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + chunk + b"\r\n"
        finally:
            cap.release()

    @action(detail=True, methods=["post"])
    def ping(self, request, pk=None):
        camera = self.get_object()
        cap = self._open_capture(camera)
        ok, _ = cap.read()
        cap.release()
        camera.is_online = bool(ok)
        camera.save(update_fields=["is_online"])
        return Response({"camera_id": camera.id, "is_online": camera.is_online})

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def discover_local(self, request):
        indices = self._discover_local_indices()
        created = []
        updated = []
        for idx in indices:
            code = f"LOCAL-{idx}"
            camera, was_created = Camera.objects.get_or_create(
                camera_code=code,
                defaults={
                    "name": f"Camera Local {idx}",
                    "source": str(idx),
                    "is_online": True,
                    "location": "Notebook",
                },
            )
            if was_created:
                created.append(camera.id)
            else:
                if not camera.is_online or camera.source != str(idx):
                    camera.is_online = True
                    camera.source = str(idx)
                    camera.save(update_fields=["is_online", "source"])
                updated.append(camera.id)
        return Response(
            {
                "detected_indices": indices,
                "created_ids": created,
                "updated_ids": updated,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def live(self, request, pk=None):
        camera = self.get_object()
        sig = request.GET.get("sig")
        if not sig:
            return Response({"error": "Missing signature"}, status=status.HTTP_400_BAD_REQUEST)
        signer = signing.TimestampSigner(salt="visionguard-live")
        try:
            unsigned = signer.unsign(sig, max_age=60)
            if unsigned != str(camera.id):
                raise signing.BadSignature
        except signing.BadSignature:
            return Response({"error": "Invalid or expired signature"}, status=status.HTTP_403_FORBIDDEN)
        return StreamingHttpResponse(
            self._mjpeg_generator(camera),
            content_type="multipart/x-mixed-replace; boundary=frame",
        )

    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def signed_live_url(self, request, pk=None):
        camera = self.get_object()
        signer = signing.TimestampSigner(salt="visionguard-live")
        signed = signer.sign(str(camera.id))
        return Response(
            {
                "url": f"/api/cameras/{camera.id}/live/?sig={signed}",
                "expires_in_seconds": 60,
            }
        )

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def vision_start(self, request):
        """Inicia o programa da câmera (vision/main.py)."""
        import sys
        import os as os_module
        
        try:
            vision_dir = os_module.path.join(os_module.path.dirname(__file__), '..', '..', '..', 'vision')
            vision_main = os_module.path.join(vision_dir, 'main.py')
            
            if not os_module.path.exists(vision_main):
                return Response(
                    {"error": f"vision/main.py not found at {vision_main}"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            # Obter venv python
            venv_python = sys.executable
            
            # Iniciar processo
            process = subprocess.Popen(
                [venv_python, vision_main],
                cwd=vision_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            CameraViewSet._vision_process = process
            
            return Response(
                {
                    "status": "started",
                    "pid": process.pid,
                    "message": "Vision pipeline iniciado com sucesso",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def vision_stop(self, request):
        """Para o programa da câmera."""
        try:
            if CameraViewSet._vision_process:
                CameraViewSet._vision_process.terminate()
                try:
                    CameraViewSet._vision_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    CameraViewSet._vision_process.kill()
                CameraViewSet._vision_process = None
            
            return Response(
                {"status": "stopped", "message": "Vision pipeline parado"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def vision_status(self, request):
        """Retorna status do programa da câmera."""
        running = False
        pid = None
        
        if CameraViewSet._vision_process:
            if CameraViewSet._vision_process.poll() is None:
                running = True
                pid = CameraViewSet._vision_process.pid
            else:
                CameraViewSet._vision_process = None
        
        return Response(
            {
                "running": running,
                "pid": pid,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny])
    def heartbeat(self, request, pk=None):
        """Recebe heartbeat do pipeline de visão para marcar câmera como online."""
        camera = self.get_object()
        token = request.headers.get("X-Vision-Token", "")
        
        # Verificar token
        if not token or token != "visionguard-local-token":
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        camera.update_heartbeat()
        return Response(
            {"status": "ok", "camera_id": camera.id},
            status=status.HTTP_200_OK,
        )
