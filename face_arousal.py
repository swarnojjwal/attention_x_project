import os
import cv2
import mediapipe as mp

def extract_face_arousal(frames_folder):
    """Try to load MediaPipe; if it fails, return empty list."""
    if not os.path.isdir(frames_folder):
        print(f"  -> Frames folder '{frames_folder}' not found. Skipping face analysis.")
        return []

    try:
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, refine_landmarks=True)
    except (ImportError, AttributeError) as e:
        print(f"  -> MediaPipe not available or broken: {e}. Skipping face analysis.")
        return []

    def compute_arousal_score(landmarks, h, w):
        LEFT_BROW = 70
        RIGHT_BROW = 300
        LEFT_EYE_TOP = 159
        RIGHT_EYE_TOP = 386
        LIP_CORNER_LEFT = 61
        LIP_CORNER_RIGHT = 291
        LIP_TOP = 13
        LIP_BOTTOM = 14

        def get_y(idx):
            return landmarks.landmark[idx].y * h

        brow_y = (get_y(LEFT_BROW) + get_y(RIGHT_BROW)) / 2
        eye_y = (get_y(LEFT_EYE_TOP) + get_y(RIGHT_EYE_TOP)) / 2
        brow_raise = max(0, (eye_y - brow_y) / (h * 0.1))

        mouth_open = abs(get_y(LIP_TOP) - get_y(LIP_BOTTOM)) / (h * 0.1)
        smile = abs(landmarks.landmark[LIP_CORNER_LEFT].x - landmarks.landmark[LIP_CORNER_RIGHT].x) * w / (w * 0.2)

        arousal = (min(1.0, brow_raise) + min(1.0, mouth_open) + min(1.0, smile)) / 3.0
        return min(1.0, arousal)

    face_peaks = []
    for filename in sorted(os.listdir(frames_folder)):
        if not filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            continue
        try:
            ts = float(filename.split('_')[1].split('.')[0])
        except:
            print(f"Skipping {filename}: cannot extract timestamp")
            continue

        img_path = os.path.join(frames_folder, filename)
        img = cv2.imread(img_path)
        if img is None:
            continue
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        if results.multi_face_landmarks:
            h, w, _ = img.shape
            arousal = compute_arousal_score(results.multi_face_landmarks[0], h, w)
            face_peaks.append({'timestamp': ts, 'arousal': arousal})

    face_peaks = [p for p in face_peaks if p['arousal'] > 0.5]
    return face_peaks