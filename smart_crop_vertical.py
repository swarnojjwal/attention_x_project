import cv2
import numpy as np
import mediapipe as mp
from tqdm import tqdm
import os

# ------------------------------------------------------------
# Face tracking with MediaPipe
# ------------------------------------------------------------
def get_face_center(frame, face_detector):
    """Detect largest face and return its center (x, y). Returns None if no face."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_detector.process(rgb)
    if not results.detections:
        return None
    detection = results.detections[0]
    bbox = detection.location_data.relative_bounding_box
    h, w, _ = frame.shape
    x = int(bbox.xmin * w)
    y = int(bbox.ymin * h)
    width = int(bbox.width * w)
    height = int(bbox.height * h)
    center_x = x + width // 2
    center_y = y + height // 2
    return (center_x, center_y)

def smooth_center_x(centers, window_size=5):
    """Apply moving average to X coordinates."""
    smoothed = []
    for i in range(len(centers)):
        start = max(0, i - window_size // 2)
        end = min(len(centers), i + window_size // 2 + 1)
        valid = [c[0] for c in centers[start:end] if c is not None]
        if not valid:
            smoothed.append(centers[i][0] if centers[i] else 0)
        else:
            avg = int(np.mean(valid))
            smoothed.append(avg)
    return smoothed

# ------------------------------------------------------------
# Smart crop for a single clip (works for any resolution)
# ------------------------------------------------------------
def process_clip(input_path, output_path, blur_sigma=31):
    """
    Convert any horizontal clip to vertical 9:16 with face tracking.
    - Crops a square around the face (size = original height)
    - Scales that square to 1080x1080
    - Places it on a 1080x1920 canvas with blurred background
    """
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open {input_path}")
    
    # Video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Input resolution: {orig_width}x{orig_height}, {total_frames} frames")
    
    # Square crop size = original height (makes a square from the full height)
    crop_size = orig_height
    
    # Prepare output video writer (1080x1920, 30 fps)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (1080, 1920))
    
    # Face detector
    mp_face = mp.solutions.face_detection
    face_detector = mp_face.FaceDetection(min_detection_confidence=0.5)
    
    # Step 1: Detect face centers
    print(f"Detecting faces in {total_frames} frames...")
    face_centers = []
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    for _ in tqdm(range(total_frames)):
        ret, frame = cap.read()
        if not ret:
            face_centers.append(None)
            continue
        center = get_face_center(frame, face_detector)
        face_centers.append(center)
    
    # Interpolate missing detections
    for i in range(len(face_centers)):
        if face_centers[i] is None:
            left = i - 1
            right = i + 1
            while left >= 0 and face_centers[left] is None:
                left -= 1
            while right < len(face_centers) and face_centers[right] is None:
                right += 1
            if left >= 0 and right < len(face_centers):
                ratio = (i - left) / (right - left)
                x = int(face_centers[left][0] * (1-ratio) + face_centers[right][0] * ratio)
                y = int(face_centers[left][1] * (1-ratio) + face_centers[right][1] * ratio)
                face_centers[i] = (x, y)
            elif left >= 0:
                face_centers[i] = face_centers[left]
            elif right < len(face_centers):
                face_centers[i] = face_centers[right]
            else:
                face_centers[i] = (orig_width // 2, orig_height // 2)
    
    # Smooth X coordinates
    x_coords = [c[0] for c in face_centers]
    smoothed_x = smooth_center_x([(x,0) for x in x_coords], window_size=5)
    
    # Step 2: Process each frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    print(f"Rendering vertical video to {output_path}...")
    for frame_idx in tqdm(range(total_frames)):
        ret, frame = cap.read()
        if not ret:
            break
        
        # Calculate crop X to keep face centered
        crop_x = smoothed_x[frame_idx] - crop_size // 2
        crop_x = max(0, min(crop_x, orig_width - crop_size))
        
        # Crop square (height x height)
        cropped = frame[:, crop_x:crop_x + crop_size]   # shape: (crop_size, crop_size, 3)
        
        # Resize cropped square to 1080x1080 (target square size)
        square_1080 = cv2.resize(cropped, (1080, 1080), interpolation=cv2.INTER_LANCZOS4)
        
        # Create blurred background: resize cropped to 1080x1920 and blur
        bg = cv2.resize(cropped, (1080, 1920), interpolation=cv2.INTER_LINEAR)
        bg = cv2.GaussianBlur(bg, (blur_sigma, blur_sigma), 0)
        
        # Place the sharp 1080x1080 square in the center of the background
        y_offset = (1920 - 1080) // 2   # = 420
        bg[y_offset:y_offset+1080, :] = square_1080
        
        out.write(bg)
    
    cap.release()
    out.release()
    face_detector.close()
    print(f"Done: {output_path}")

# ------------------------------------------------------------
# Batch process all clips
# ------------------------------------------------------------
def batch_process_clips(input_folder="emotional_clips", output_folder="vertical_clips"):
    """Process all MP4 files in input_folder."""
    if not os.path.isdir(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist.")
        return
    
    os.makedirs(output_folder, exist_ok=True)
    clip_files = sorted([f for f in os.listdir(input_folder) if f.endswith(".mp4")])
    if not clip_files:
        print(f"No MP4 files found in '{input_folder}'.")
        return
    
    for clip in clip_files:
        in_path = os.path.join(input_folder, clip)
        out_path = os.path.join(output_folder, clip.replace(".mp4", "_vertical.mp4"))
        print(f"\nProcessing {clip}...")
        process_clip(in_path, out_path)

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
if __name__ == "__main__":
    batch_process_clips("emotional_clips", "vertical_clips")