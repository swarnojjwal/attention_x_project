import os
import subprocess
import whisper
from dotenv import load_dotenv
from tqdm import tqdm

# Load API keys from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
USE_GEMINI = True  # Use Gemini (free tier) – set False to use OpenAI

if not GEMINI_API_KEY and USE_GEMINI:
    raise ValueError("GEMINI_API_KEY not found in .env file. Get a free key from Google AI Studio.")
if not OPENAI_API_KEY and not USE_GEMINI:
    raise ValueError("No API key found. Set OPENAI_API_KEY or GEMINI_API_KEY in .env file")

# ------------------------------------------------------------
# Helper: extract first 5 seconds of audio from video
# ------------------------------------------------------------
def extract_first_5s_audio(video_path, audio_path):
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-ss", "0", "-t", "5",
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        audio_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)

# ------------------------------------------------------------
# Transcribe first 5 seconds with Whisper
# ------------------------------------------------------------
def transcribe_first_5s(audio_path, model_size="base"):
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path)
    return result["text"].strip()

# ------------------------------------------------------------
# Generate hook using LLM (Gemini by default)
# ------------------------------------------------------------
def generate_hook(text, max_words=5):
    prompt = f"""Summarize this into a {max_words}-word bold headline that creates curiosity.
No explanation. Examples: 'The Real Secret', '3am Rule', 'Stop Wasting Time'.
Sentence: {text}
Hook:"""
    
    try:
        if USE_GEMINI:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            hook = response.text.strip()
        else:
            import openai
            openai.api_key = OPENAI_API_KEY
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=20
            )
            hook = response.choices[0].message.content.strip()
        
        return hook.strip('"').strip("'")
    except Exception as e:
        print(f"  API error: {e}. Using fallback hook.")
        # Fallback: extract first few words from transcript
        words = text.split()[:4]
        return " ".join(words).title() if words else "Must Watch"

# ------------------------------------------------------------
# Overlay hook on video (first 2 seconds)
# ------------------------------------------------------------
def add_hook_overlay(video_path, hook_text, output_path):
    hook_escaped = hook_text.replace("'", r"\'").replace(":", r"\:")
    filter_str = (
        f"drawtext=text='{hook_escaped}':"
        f"fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
        f"fontsize=48:fontcolor=white:borderw=2:bordercolor=black:"
        f"x=(w-text_w)/2:y=50:enable='between(t,0,2)'"
    )
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", filter_str, "-c:a", "copy", output_path]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  Hook overlay added: {output_path}")

# ------------------------------------------------------------
# Process a single clip
# ------------------------------------------------------------
def add_hook_to_clip(video_path, output_dir="hooked_clips", model_size="base"):
    os.makedirs(output_dir, exist_ok=True)
    basename = os.path.basename(video_path)
    name, ext = os.path.splitext(basename)
    output_path = os.path.join(output_dir, f"{name}_hook{ext}")
    audio_path = os.path.join(output_dir, f"{name}_temp_audio.wav")
    
    print(f"\nProcessing {basename}...")
    print("  Extracting first 5 seconds of audio...")
    extract_first_5s_audio(video_path, audio_path)
    
    print("  Transcribing with Whisper...")
    transcript = transcribe_first_5s(audio_path, model_size)
    if not transcript:
        print("  No speech detected. Skipping hook.")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return
    
    print("  Generating hook using Gemini...")
    hook = generate_hook(transcript)
    print(f"  Hook: \"{hook}\"")
    
    print("  Adding hook overlay...")
    add_hook_overlay(video_path, hook, output_path)
    
    if os.path.exists(audio_path):
        os.remove(audio_path)
    print(f"  Done: {output_path}")

# ------------------------------------------------------------
# Batch process all captioned clips
# ------------------------------------------------------------
def batch_add_hooks(input_folder="captioned_clips", output_folder="hooked_clips", model_size="base"):
    if not os.path.isdir(input_folder):
        print(f"Error: Input folder '{input_folder}' not found.")
        return
    clip_files = [f for f in os.listdir(input_folder) if f.endswith(".mp4")]
    if not clip_files:
        print(f"No MP4 files found in '{input_folder}'.")
        return
    for clip in clip_files:
        clip_path = os.path.join(input_folder, clip)
        add_hook_to_clip(clip_path, output_folder, model_size)

if __name__ == "__main__":
    batch_add_hooks("captioned_clips", "hooked_clips", model_size="base")