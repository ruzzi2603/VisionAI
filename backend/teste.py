import cv2
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
ok, frame = cap.read()
print(ok)
