import cv2
import mediapipe as mp
import os

video_path = r"C:\Users\vaibhav\.gemini\antigravity\scratch\brake-diagnostic-system\psych-interview-system\backend\data\raw_uploads\0468af80-58e5-424f-9af7-32b824088d94.mp4"

face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(video_path)
frame_count = 0
faces_found = 0

while cap.isOpened() and frame_count < 100:
    success, image = cap.read()
    if not success:
        break
    
    if frame_count % 10 == 0:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image_rgb)
        if results.multi_face_landmarks:
            faces_found += 1
            print(f"Face found at frame {frame_count}")
        else:
            print(f"No face at frame {frame_count}")
            
    frame_count += 1

cap.release()
print(f"Total frames read: {frame_count}")
print(f"Frames with faces: {faces_found}")
print("Test completed.")
