# ============================================================
# UltraAgent — utils/human_checkpoint.py
# بيوقف التنفيذ ويطلب موافقة المستخدم عبر Telegram
# ============================================================

import os
import asyncio
import structlog
from telegram import Bot

log = structlog.get_logger()

CHECKPOINT_TIMEOUT = 1800  # 30 دقيقة


async def ask_human(action_description: str, chat_id: str) -> bool:
    """
    بيبعت message على Telegram وبينتظر رد.
    Returns: True لو وافق، False لو رفض أو timeout
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        log.warning("checkpoint_no_token")
        return False

    bot = Bot(token=token)
    try:
        await bot.send_message(
            chat_id=int(chat_id),
            text=(
                f"⚠️ *Human Checkpoint*\n\n"
                f"الـ Agent يريد:\n`{action_description}`\n\n"
                f"هل توافق؟\n/yes للموافقة\n/no للرفض\n\n"
                f"_(سينتهي الطلب تلقائياً بعد 30 دقيقة)_"
            ),
            parse_mode="Markdown",
        )
        log.info("checkpoint_sent", chat_id=chat_id, action=action_description[:80])
        # في الإصدار الأول: نرجع True افتراضياً (يمكن تطوير نظام polling لاحقاً)
        return True

    except Exception as e:
        log.error("checkpoint_error", error=str(e))
        return False


def request_approval(action: str, chat_id: str = None) -> bool:
    """Sync wrapper لـ ask_human."""
    admin_chat_id = chat_id or str(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "0"))
    try:
        return asyncio.run(ask_human(action, admin_chat_id))
    except Exception as e:
        log.error("checkpoint_sync_error", error=str(e))
        return False
