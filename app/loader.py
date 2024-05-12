from typing import List
import re
import tempfile
from app.ai import AI
from youtube_transcript_api import YouTubeTranscriptApi


class Loader:
    def __init__(self, ai: AI):
        self.ai = ai

    def upload_youtube_transcript(self, url: str, languages: List[str] = ["en"]):
        video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
        if video_id_match:
            video_id = video_id_match.group(1)
        else:
            raise ValueError("Invalid YouTube URL")

        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        full_transcript = " ".join([entry["text"] for entry in transcript])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt") as f:
            f.write(full_transcript)
            f.flush()
            self.ai.upload_file_stream(f.name)

    def upload_pdf_file(self, uploaded_file: str):
        file_bytes = uploaded_file.getvalue()
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf") as tmpfile:
            tmpfile.write(file_bytes)
            tmpfile.flush()
            self.ai.upload_file_stream(tmpfile.name)
