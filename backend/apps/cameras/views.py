import cv2
import time
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

    def _open_capture(self, camera: Camera):
        source = camera.stream_url.strip() if camera.stream_url else camera.source.strip()
        if source.isdigit():
            return cv2.VideoCapture(int(source), cv2.CAP_DSHOW)
        return cv2.VideoCapture(source)

    def _discover_local_indices(self, max_index: int = 3):
        found = []
        for idx in range(0, max_index + 1):
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            ok, _ = cap.read()
            cap.release()
            if ok:
                found.append(idx)
        return found

    def _mjpeg_generator(self, camera: Camera):
        cap = self._open_capture(camera)
        target_fps = 10.0
        frame_interval = 1.0 / target_fps
        jpeg_quality = 70
        stream_width = 960
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
