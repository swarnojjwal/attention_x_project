import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')  # serve static files from current folder
CORS(app)

@app.route('/')
def serve_frontend():
    """Serve the main HTML dashboard (optional)."""
    return send_from_directory('.', 'index.html')

@app.route('/api/engine/status')
def engine_status():
    return jsonify({
        "status": "ACTIVE",
        "media": {
            "name": "avengers_clip.mp4",
            "size_mb": 31.83,
            "ready": True
        },
        "activeSegment": {
            "start": "8:16",
            "end": "9:00",
            "hookText": "Three words that changed EVERYTHING. 🎵 'On your left...'",
            "energyType": "High stakes and intellectual dread"
        }
    })

@app.route('/api/clips')
def get_clips():
    clips = [
        {
            "id": 1,
            "start": "0:18",
            "end": "0:58",
            "quote": "Why Thanos was the most TERRIFYING villain ever... 😱",
            "energyType": "High stakes and intellectual dread",
            "cropAlignment": "Centered"
        },
        {
            "id": 2,
            "start": "4:35",
            "end": "5:15",
            "quote": "WE FINALLY SAW IT! Captain America lifts the hammer! 🏅‍♂️",
            "energyType": "Pure hype and cinematic payoff",
            "cropAlignment": "Centered"
        },
        {
            "id": 3,
            "start": "8:16",
            "end": "9:00",
            "quote": "The portal scene - AVENGERS ASSEMBLE! ⚡",
            "energyType": "Epic climax",
            "cropAlignment": "Centered"
        },
        {
            "id": 4,
            "start": "12:05",
            "end": "12:48",
            "quote": "I am Iron Man (snap)... devastating silence",
            "energyType": "Tragic heroism",
            "cropAlignment": "Centered"
        }
    ]
    return jsonify(clips)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)