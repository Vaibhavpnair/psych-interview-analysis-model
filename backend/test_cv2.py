import cv2
import os

video_path = r"C:\Users\vaibhav\.gemini\antigravity\scratch\brake-diagnostic-system\psych-interview-system\backend\data\raw_uploads\0468af80-58e5-424f-9af7-32b824088d94.mp4"

if not os.path.exists(video_path):
    print(f"Error: File not found at {video_path}")
    exit(1)

cap = cv2.VideoCapture(video_path)
print(f"cap.isOpened(): {cap.isOpened()}")
if not cap.isOpened():
    print("Error: Could not open video.")
    exit(1)

fps = cap.get(cv2.CAP_PROP_FPS)
print(f"FPS: {fps}")

success, image = cap.read()
print(f"First frame success: {success}")
if success:
    print(f"Frame shape: {image.shape}")

cap.release()
print("Test completed.")
