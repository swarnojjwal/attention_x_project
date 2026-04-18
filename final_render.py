import os
import subprocess
import json
import zipfile
from tqdm import tqdm

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
INPUT_VIDEO_FOLDER = "vertical_clips"      # Stage 4 output (1080x1920)
INPUT_ASS_FOLDER = "captioned_clips"       # Stage 5 ASS files (or same as video folder)
HOOKS_FILE = "hooks.json"                  # JSON with clip -> hook text
OUTPUT_FOLDER = "final_clips"
ZIP_NAME = "emotional_clips.zip"

# FFmpeg settings
FPS = 30
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
PIX_FMT = "yuv420p"

# Hook overlay settings
HOOK_DURATION = 2          # seconds
HOOK_FONT_SIZE = 48
HOOK_FONT_COLOR = "white"
HOOK_BORDER_COLOR = "black"
HOOK_Y_POS = 50            # pixels from top
HOOK_FONT_FILE = None      # auto-detect

# ------------------------------------------------------------
# Helper: get hook text for a clip
# ------------------------------------------------------------
def get_hook_text(clip_name):
    """Read hook from JSON file generated in Stage 6."""
    if not os.path.exists(HOOKS_FILE):
        return ""   # no hooks
    with open(HOOKS_FILE, "r") as f:
        hooks = json.load(f)
    return hooks.get(clip_name, "")

# ------------------------------------------------------------
# Build FFmpeg command with filter_complex
# ------------------------------------------------------------
def build_ffmpeg_command(video_path, ass_path, hook_text, output_path):
    """Return list of arguments for subprocess.run."""
    # Escape hook text for drawtext
    hook_text_escaped = hook_text.replace("'", r"\'").replace(":", r"\:")
    
    # Drawtext filter (hook overlay, visible only between t=0 and t=HOOK_DURATION)
    drawtext_filter = (
        f"drawtext=text='{hook_text_escaped}':"
        f"fontsize={HOOK_FONT_SIZE}:fontcolor={HOOK_FONT_COLOR}:"
        f"borderw=2:bordercolor={HOOK_BORDER_COLOR}:"
        f"x=(w-text_w)/2:y={HOOK_Y_POS}:enable='between(t,0,{HOOK_DURATION})'"
    )
    
    # ASS subtitle filter (karaoke captions)
    ass_filter = f"ass={ass_path}"
    
    # Combine filters: first drawtext then ass (order matters)
    # Use filter_complex to chain them
    filter_complex = f"{drawtext_filter},{ass_filter}"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", filter_complex,
        "-r", str(FPS),
        "-c:v", VIDEO_CODEC,
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", PIX_FMT,
        "-c:a", AUDIO_CODEC,
        "-b:a", "128k",
        output_path
    ]
    
    # Add font file if specified (for cross‑platform)
    if HOOK_FONT_FILE and os.path.exists(HOOK_FONT_FILE):
        # Insert fontfile option into drawtext filter
        # Simpler: replace drawtext_filter with one that includes fontfile
        pass
    
    return cmd

# ------------------------------------------------------------
# Process all clips
# ------------------------------------------------------------
def process_all_clips():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    # Find all vertical videos
    video_files = [f for f in os.listdir(INPUT_VIDEO_FOLDER) if f.endswith(".mp4")]
    if not video_files:
        print(f"No MP4 files found in {INPUT_VIDEO_FOLDER}")
        return
    
    final_videos = []
    for video_file in tqdm(video_files, desc="Rendering clips"):
        base_name = os.path.splitext(video_file)[0]
        video_path = os.path.join(INPUT_VIDEO_FOLDER, video_file)
        
        # Find corresponding ASS file (same name, .ass)
        ass_file = base_name + "_captions.ass"
        ass_path = os.path.join(INPUT_ASS_FOLDER, ass_file)
        if not os.path.exists(ass_path):
            # Try without "_captions"
            ass_path = os.path.join(INPUT_ASS_FOLDER, base_name + ".ass")
        if not os.path.exists(ass_path):
            print(f"Warning: No ASS file for {video_file}, skipping captions")
            ass_path = None
        
        hook = get_hook_text(base_name)
        
        output_path = os.path.join(OUTPUT_FOLDER, f"{base_name}_final.mp4")
        
        # Build command
        if ass_path:
            cmd = build_ffmpeg_command(video_path, ass_path, hook, output_path)
        else:
            # No subtitles, only hook
            cmd = build_ffmpeg_command(video_path, "null", hook, output_path)
            # Remove ASS filter
            cmd[cmd.index("-vf")+1] = drawtext_filter
        
        # Run FFmpeg
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            final_videos.append(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Error processing {video_file}: {e}")
    
    return final_videos

# ------------------------------------------------------------
# Zip all final clips
# ------------------------------------------------------------
def zip_final_clips(file_list, zip_name):
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in file_list:
            zipf.write(file, arcname=os.path.basename(file))
    print(f"Created {zip_name} with {len(file_list)} clips")

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
if __name__ == "__main__":
    print("Stage 7 – Final Rendering & Export")
    clips = process_all_clips()
    if clips:
        zip_final_clips(clips, ZIP_NAME)
        print(f"All clips saved to {OUTPUT_FOLDER} and zipped as {ZIP_NAME}")
    else:
        print("No clips processed.")