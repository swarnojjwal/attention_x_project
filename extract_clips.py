import subprocess
import os
import sys

def extract_clips(video_path, peak_timestamps, output_folder="clips", 
                  pre_seconds=15, post_seconds=30, max_clips=10):
    """
    Extract video clips around emotional peaks.
    
    Parameters:
        video_path (str): Path to input video file (e.g., "video.mp4")
        peak_timestamps (list of float or str): Peak times in seconds or "MM:SS" format
        output_folder (str): Directory to save clips
        pre_seconds (int): Seconds before peak
        post_seconds (int): Seconds after peak
        max_clips (int): Maximum number of clips to extract (default 10)
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Convert timestamps to seconds (if they are in "MM:SS" format)
    def to_seconds(ts):
        if isinstance(ts, (int, float)):
            return float(ts)
        if isinstance(ts, str):
            parts = ts.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        raise ValueError(f"Cannot parse timestamp: {ts}")
    
    # Process only up to max_clips
    peaks_sec = [to_seconds(ts) for ts in peak_timestamps[:max_clips]]
    
    for i, peak in enumerate(peaks_sec, start=1):
        start_time = max(0, peak - pre_seconds)
        duration = pre_seconds + post_seconds   # total clip length
        
        output_path = os.path.join(output_folder, f"clip_{i:02d}.mp4")
        
        # Build ffmpeg command
        # Using -ss before -i for fast seeking (accurate enough for most cases)
        # For frame‑accurate cuts, use -ss after -i (slower) – uncomment alternative below.
        cmd = [
            "ffmpeg",
            "-ss", str(start_time),   # seek to start position
            "-i", video_path,         # input file
            "-t", str(duration),      # duration of the clip
            "-c", "copy",             # copy codec (no re‑encode, very fast)
            "-avoid_negative_ts", "make_zero",
            output_path
        ]
        
        # Optional: if you need frame‑accuracy (slower), replace "-c copy" with:
        # cmd = ["ffmpeg", "-i", video_path, "-ss", str(start_time), "-t", str(duration), "-c", "libx264", "-preset", "fast", output_path]
        
        print(f"Extracting clip {i}/{len(peaks_sec)}: peak at {peak:.1f}s -> {output_path}")
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"Error extracting clip {i}: {e.stderr.decode()}")
            continue
        
        print(f"  -> Saved {output_path}")

if __name__ == "__main__":
    # Example usage:
    # Replace these with your actual data
    PEAKS = [12.5, 34.2, 67.8, 90.0, 120.5]   # in seconds OR ["12:30", "34:12", ...]
    VIDEO_FILE = "avengers_clip.mp4"
    
    extract_clips(VIDEO_FILE, PEAKS, output_folder="emotional_clips")