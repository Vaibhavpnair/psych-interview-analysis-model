try:
    import mediapipe as mp
    print("Mediapipe imported successfully.")
    face_mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    print("FaceMesh initialized successfully.")
except Exception as e:
    print(f"Error initializing Mediapipe: {e}")

print("Test completed.")
