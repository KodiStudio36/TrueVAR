from cv2_enumerate_cameras import enumerate_cameras
import cv2

for camera_info in enumerate_cameras(cv2.CAP_GSTREAMER):
    camera = cv2.VideoCapture(camera_info.index)
    if camera.isOpened():
        print("Camera ID:", camera_info.index)
    else:
        print("error")
    camera.release()