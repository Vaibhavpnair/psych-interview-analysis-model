import numpy as np
import mediapipe as mp
import cv2

print("Starting mediapipe synthetic test...")
try:
    face_mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    )
    print("FaceMesh initialized.")

    # Create a blank white image with a "face" (just a rectangle for now to see if it crashes)
    image = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    print("Processing image...")
    results = face_mesh.process(image)
    print(f"Process completed. Results: {results.multi_face_landmarks}")
except Exception as e:
    print(f"Error: {e}")

print("Test finished.")
