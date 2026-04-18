import whisper
from transformers import pipeline
import re

def transcribe_and_score(wav_path):
    model = whisper.load_model("small")
    result = model.transcribe(wav_path, word_timestamps=True)

    sentences = []
    for seg in result['segments']:
        sentences.append({
            'text': seg['text'].strip(),
            'start': seg['start'],
            'end': seg['end']
        })

    sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

    def get_sentiment_score(text):
        res = sentiment_pipeline(text[:512])[0]
        return 1.0 if res['label'] == 'POSITIVE' else -1.0

    for sent in sentences:
        sent['sentiment'] = get_sentiment_score(sent['text'])

    hook_patterns = [
        r"(the truth is|i realized|the thing is|what matters is)",
        r"(never|always|must|should)\s+\w+",
        r"\b(beautiful|powerful|amazing|incredible)\b"
    ]

    def hook_score_regex(text):
        score = 0
        for pat in hook_patterns:
            if re.search(pat, text, re.I):
                score += 1
        return min(score, 2)

    text_peaks = []
    prev = None
    for sent in sentences:
        shift = 0.0 if prev is None else abs(sent['sentiment'] - prev['sentiment']) / 2.0
        hook = hook_score_regex(sent['text'])
        score = 0.6 * shift + 0.4 * (hook / 2.0)
        text_peaks.append({
            'timestamp': sent['start'],
            'score': score,
            'text': sent['text']
        })
        prev = sent

    text_peaks = [p for p in text_peaks if p['score'] > 0.4]
    return text_peaks