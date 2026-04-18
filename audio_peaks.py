import librosa
import numpy as np

def detect_audio_peaks(wav_path, window_s=0.5, threshold_factor=1.5):
    """Return list of timestamps (seconds) where RMS energy exceeds threshold."""
    y, sr = librosa.load(wav_path, sr=None)
    window_len = int(window_s * sr)
    hop_len = window_len

    rms = librosa.feature.rms(y=y, frame_length=window_len, hop_length=hop_len)[0]
    timestamps = np.arange(len(rms)) * window_s

    threshold = np.mean(rms) + threshold_factor * np.std(rms)
    peak_mask = rms > threshold
    audio_peaks = timestamps[peak_mask].tolist()
    return audio_peaks