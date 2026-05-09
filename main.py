# ============================================================
# UltraAgent — main.py
# Entry point للـ FastAPI app على Render
# ============================================================

import structlog
from dotenv import load_dotenv

load_dotenv()

from interfaces.rest_api import app  # noqa: E402

log = structlog.get_logger()
log.info("ultraagent_starting", version="1.0.0")
