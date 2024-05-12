from dotenv import load_dotenv

load_dotenv()

import os
from app.ui import show_ui
from app.ai import AI
from app.loader import Loader

openai_api_key = os.getenv("OPEN_AI_API")

ai = AI(openai_api_key, "YouTube Assistant", "YouTube Vector Store")
loader = Loader(ai)

show_ui(ai, loader)
