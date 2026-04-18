import librosa
from audio_peaks import detect_audio_peaks
from transcript_sentiment import transcribe_and_score
from face_arousal import extract_face_arousal
from fusion_ranking import create_timeline, non_max_suppression, format_time

def main():
    AUDIO_PATH = "audio.wav"
    FRAMES_FOLDER = "frames/"

    print("2A – Detecting audio energy spikes...")
    audio_peaks = detect_audio_peaks(AUDIO_PATH)
    print(f"Found {len(audio_peaks)} audio peaks.")

    print("2B – Transcribing and scoring text...")
    text_peaks = transcribe_and_score(AUDIO_PATH)
    print(f"Found {len(text_peaks)} text peaks.")

    print("2C – Extracting facial arousal...")
    face_peaks = extract_face_arousal(FRAMES_FOLDER)
    print(f"Found {len(face_peaks)} face peaks.")

    y, sr = librosa.load(AUDIO_PATH, sr=None)
    total_duration = len(y) / sr

    print("2D – Fusing and ranking...")
    timestamps, combined_scores = create_timeline(audio_peaks, text_peaks, face_peaks, total_duration)

    kept_indices = non_max_suppression(timestamps, combined_scores, min_distance_s=45)
    final_peaks = sorted([timestamps[i] for i in kept_indices])[:10]

    print("\n=== Final Emotional Peaks (mm:ss) ===")
    for ts in final_peaks:
        print(format_time(ts))

if __name__ == "__main__":
    main()