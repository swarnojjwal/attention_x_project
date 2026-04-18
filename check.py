from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)  # Allow all origins

@app.route('/api/process', methods=['POST'])
def process_video():
    # Simulate processing delay
    time.sleep(2)
    # Return mock clip data (replace with real pipeline later)
    clips = [
        {"id": 1, "start": "0:18", "end": "0:58", "quote": "Why Thanos was the most TERRIFYING villain ever... 😱", "energyType": "High stakes and intellectual dread", "cropAlignment": "Centered"},
        {"id": 2, "start": "4:35", "end": "5:15", "quote": "WE FINALLY SAW IT! Captain America lifts the hammer! 🏅", "energyType": "Pure hype and cinematic payoff", "cropAlignment": "Centered"},
        {"id": 3, "start": "8:16", "end": "9:00", "quote": "The portal scene - AVENGERS ASSEMBLE! ⚡", "energyType": "Epic climax", "cropAlignment": "Centered"},
        {"id": 4, "start": "12:05", "end": "12:48", "quote": "I am Iron Man (snap)... devastating silence", "energyType": "Tragic heroism", "cropAlignment": "Centered"}
    ]
    return jsonify({"status": "ok", "clips": clips})

@app.route('/api/engine/status', methods=['GET'])
def engine_status():
    return jsonify({
        "status": "ACTIVE",
        "media": {"name": "demo.mp4", "size_mb": 0, "ready": True},
        "activeSegment": {
            "start": "8:16",
            "end": "9:00",
            "hookText": "Three words that changed EVERYTHING.",
            "energyType": "High stakes and intellectual dread"
        }
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)
