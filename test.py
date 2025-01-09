from cv2_enumerate_cameras import enumerate_cameras
import cv2

for camera_info in enumerate_cameras(cv2.CAP_GSTREAMER):
    # Open a connection to the camera

    camera = cv2.VideoCapture(camera_info.index)  # Use 0 or your specific camera ID

    # Check if the camera opened successfully
    if not camera.isOpened():
        print("Error: Could not open camera.")
    else:
        print("eee")
        # Get resolution
        width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Get framerate
        fps = camera.get(cv2.CAP_PROP_FPS)
        
        # Get format (FourCC code)
        fourcc = int(camera.get(cv2.CAP_PROP_FOURCC))
        format = (
            chr((fourcc & 0xFF)) +
            chr((fourcc >> 8) & 0xFF) +
            chr((fourcc >> 16) & 0xFF) +
            chr((fourcc >> 24) & 0xFF)
        )
        
        print(f"Resolution: {width}x{height}")
        print(f"Framerate: {fps} FPS")
        print(f"Format: {format}")

    # Release the camera
    camera.release()