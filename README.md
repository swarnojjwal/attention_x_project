# AttentionX

**Automated Content Repurposing Engine**

AttentionX automatically extracts emotional highlights from long videos and converts them into vertical, captioned short clips optimized for TikTok, Instagram Reels, and YouTube Shorts.

<img width="1907" height="909" alt="image" src="https://github.com/user-attachments/assets/202ce191-23ad-45ce-b3bd-114e7b8886a4" />


## 🎥 Live Demo
https://drive.google.com/file/d/196egVuqPC5_pUMTe_0FkIwfdz1CqojJK/view?usp=sharing

---

## Features

- Multimodal emotional peak detection (audio energy + speech sentiment + optional face analysis)
- Smart vertical 9:16 cropping with centered subject and blurred background
- Karaoke-style synchronized captions
- AI-generated hooks using OpenAI or Gemini
- Fully automated pipeline from raw video to ready-to-upload clips
- ZIP export of final clips

---

## Prerequisites

- Python 3.10 or higher
- FFmpeg (installed and added to system PATH)

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/attentionx.git
   cd attentionx

Create and activate a virtual environment:Bashpython -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
Install dependencies:Bashpip install -r requirements.txt
Set up API keys (for hook generation):Create a .env file in the root directory:envGEMINI_API_KEY=your_gemini_api_key_here     # Recommended (free)
# OPENAI_API_KEY=sk-...                     # Alternative


Project Structure
attention_x_project/
├── .env                        # API keys (git-ignored)
├── audio.wav                   # Extracted audio (Stage 2 input)
├── avengers_clip.mp4           # Source video
├── detect_emotional_peaks.py   # Stage 2
├── extract_clips.py            # Stage 3
├── smart_crop_vertical.py      # Stage 4
├── add_karaoke_captions.py     # Stage 5
├── add_hook_overlay.py         # Stage 6
├── final_render.py             # Stage 7
├── emotional_clips/            # Stage 3 output
├── vertical_clips/             # Stage 4 output
├── captioned_clips/            # Stage 5 output
├── hooked_clips/               # Stage 6 output
├── final_clips/                # Stage 7 output
└── emotional_clips.zip         # Final downloadable archive

How to Use

Place your video file in the project root.
Extract audio:Bashffmpeg -i your_video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 audio.wav
Run the pipeline step by step:Bashpython detect_emotional_peaks.pyEdit extract_clips.py with the detected timestamps, then run:Bashpython extract_clips.py
python smart_crop_vertical.py
python add_karaoke_captions.py
python add_hook_overlay.py
python final_render.py
Find all final clips inside the final_clips/ folder and emotional_clips.zip.


Configuration

Toggle between Gemini and OpenAI in add_hook_overlay.py
Adjust cropping parameters in smart_crop_vertical.py
Customize caption styles in add_karaoke_captions.py


Troubleshooting

FFmpeg not found: Install FFmpeg and restart your terminal.
Module errors: Run pip install -r requirements.txt inside the virtual environment.
API issues: Use Gemini API key for free usage.


Technologies Used

Whisper (speech recognition)
MediaPipe (face detection)
FFmpeg (media processing)
OpenAI / Google Gemini (hook generation)
OpenCV + MoviePy


License
This project is for educational and personal use.
