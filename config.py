import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_DIR = os.path.join(BASE_DIR, "users")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(USERS_DIR, exist_ok=True)

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.3

MAX_VECTOR_RESULTS = 3
MEMORY_CATEGORIES = [
    "personal",
    "profesional",
    "preferencias",
    "hechos_importantes"
]

PAGE_TITLE = "Chat Multi-Usuario con memoria Avanzada"
PAGE_ICON = "🤖"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")