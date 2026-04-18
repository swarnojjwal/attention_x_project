import numpy as np

def create_timeline(audio_peaks, text_peaks, face_peaks, total_duration, window_s=0.5):
    bins = np.arange(0, total_duration + window_s, window_s)
    num_bins = len(bins) - 1
    timeline = {
        'audio': np.zeros(num_bins),
        'text': np.zeros(num_bins),
        'face': np.zeros(num_bins)
    }

    for ts in audio_peaks:
        idx = np.digitize(ts, bins) - 1
        if 0 <= idx < num_bins:
            timeline['audio'][idx] = 1.0

    for p in text_peaks:
        idx = np.digitize(p['timestamp'], bins) - 1
        if 0 <= idx < num_bins:
            timeline['text'][idx] = p['score']

    for p in face_peaks:
        idx = np.digitize(p['timestamp'], bins) - 1
        if 0 <= idx < num_bins:
            timeline['face'][idx] = p['arousal']

    combined = (0.4 * timeline['audio'] +
                0.4 * timeline['text'] +
                0.2 * timeline['face'])

    bin_centers = bins[:-1] + window_s/2
    return bin_centers, combined

def non_max_suppression(timestamps, scores, min_distance_s=45):
    """Return list of indices of timestamps after suppressing neighbors."""
    order = np.argsort(scores)[::-1]          # indices sorted by score descending
    keep_indices = []
    while len(order) > 0:
        i = order[0]                         # keep this index
        keep_indices.append(i)
        # Find all indices in order that are within min_distance_s
        to_remove = [0]                      # we will remove the first element
        for j in range(1, len(order)):
            if abs(timestamps[order[j]] - timestamps[i]) < min_distance_s:
                to_remove.append(j)          # remove by position in order
        # Remove those positions (largest first to avoid index shifting)
        order = np.delete(order, to_remove)
    return keep_indices

def format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"