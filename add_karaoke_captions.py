import os
import subprocess
import json
import whisper
from tqdm import tqdm

# ------------------------------------------------------------
# Helper: extract audio from video
# ------------------------------------------------------------
def extract_audio(video_path, audio_path):
    """Extract audio (16kHz mono) from video using ffmpeg."""
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error (code {result.returncode}):")
        print(result.stderr)
        raise RuntimeError(f"FFmpeg failed to extract audio from {video_path}")

# ------------------------------------------------------------
# Word-level transcription with Whisper
# ------------------------------------------------------------
def transcribe_words(audio_path, model_size="small"):
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, word_timestamps=True)
    words = []
    for segment in result["segments"]:
        for word in segment.get("words", []):
            words.append({
                "word": word["word"].strip(),
                "start": word["start"],
                "end": word["end"]
            })
    return words

# ------------------------------------------------------------
# Generate ASS subtitle file with karaoke effects
# ------------------------------------------------------------
def generate_ass(words, output_ass_path, video_width=1080, video_height=1920):
    ass_header = f"""[Script Info]
Title: Karaoke Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,5,20,20,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    if not words:
        print("No words found, skipping ASS generation")
        return
    
    start_time = words[0]["start"]
    end_time = words[-1]["end"]
    
    karaoke_parts = []
    prev_end = start_time
    for i, w in enumerate(words):
        duration_cs = int((w["end"] - w["start"]) * 100)
        if i == 0:
            karaoke_parts.append(f"{{\\k0}}{w['word']}")
        else:
            gap_cs = int((w["start"] - prev_end) * 100)
            if gap_cs > 0:
                karaoke_parts.append(f"{{\\k{gap_cs}}} ")
            karaoke_parts.append(f"{{\\k{duration_cs}}}{w['word']}")
        prev_end = w["end"]
    
    karaoke_text = "".join(karaoke_parts)
    
    def ass_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds - int(seconds)) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
    
    dialogue_line = f"Dialogue: 0,{ass_time(start_time)},{ass_time(end_time)},Default,,0,0,0,,{karaoke_text}\n"
    
    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        f.write(dialogue_line)
    
    print(f"ASS file saved: {output_ass_path}")

# ------------------------------------------------------------
# Burn ASS subtitles into video (with audio from original clip)
# ------------------------------------------------------------
def burn_subtitles(video_path, audio_path, ass_path, output_path):
    """
    Add ASS subtitles to the video and mux in the original audio.
    Uses 'subtitles' filter (more compatible than 'ass').
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-vf", f"subtitles={ass_path}",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error (code {result.returncode}):")
        print("STDERR:", result.stderr)
        print("STDOUT:", result.stdout)
        raise RuntimeError(f"FFmpeg failed to burn subtitles for {video_path}")
    print(f"Captioned video saved: {output_path}")

# ------------------------------------------------------------
# Process a single clip
# ------------------------------------------------------------
def add_captions_to_clip(clip_path, output_dir="captioned_clips", model_size="small", horizontal_dir="emotional_clips"):
    os.makedirs(output_dir, exist_ok=True)
    basename = os.path.basename(clip_path)
    name, _ = os.path.splitext(basename)
    original_name = name.replace("_vertical", "")
    horizontal_path = os.path.join(horizontal_dir, f"{original_name}.mp4")
    
    if not os.path.exists(horizontal_path):
        print(f"Warning: Original horizontal clip {horizontal_path} not found. Trying vertical clip audio (likely fails).")
        horizontal_path = clip_path
    
    audio_path = os.path.join(output_dir, f"{name}_audio.wav")
    ass_path = os.path.join(output_dir, f"{name}_captions.ass")
    output_path = os.path.join(output_dir, f"{name}_captioned.mp4")
    
    print(f"\nProcessing {basename}...")
    
    print("  Extracting audio from original clip...")
    extract_audio(horizontal_path, audio_path)
    
    print("  Transcribing with Whisper...")
    words = transcribe_words(audio_path, model_size)
    if not words:
        print("  No words detected, skipping captioning.")
        return
    
    print("  Generating ASS karaoke file...")
    generate_ass(words, ass_path, video_width=1080, video_height=1920)
    
    print("  Burning subtitles and muxing audio...")
    burn_subtitles(clip_path, audio_path, ass_path, output_path)
    
    if os.path.exists(audio_path):
        os.remove(audio_path)
    print(f"  Done: {output_path}")

# ------------------------------------------------------------
# Batch process all vertical clips
# ------------------------------------------------------------
def batch_add_captions(input_folder="vertical_clips", output_folder="captioned_clips", model_size="small", horizontal_folder="emotional_clips"):
    os.makedirs(output_folder, exist_ok=True)
    clip_files = [f for f in os.listdir(input_folder) if f.endswith(".mp4")]
    if not clip_files:
        print(f"No MP4 files found in {input_folder}")
        return
    for clip in clip_files:
        clip_path = os.path.join(input_folder, clip)
        add_captions_to_clip(clip_path, output_folder, model_size, horizontal_folder)

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
if __name__ == "__main__":
    batch_add_captions("vertical_clips", "captioned_clips", model_size="small", horizontal_folder="emotional_clips")