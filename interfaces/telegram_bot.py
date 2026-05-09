# ============================================================
# UltraAgent — interfaces/telegram_bot.py
# ============================================================

import os
import asyncio
import structlog
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from core.orchestrator import run_task
from memory.short_term import short_term

log = structlog.get_logger()
ADMIN_CHAT_ID = int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "0"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 أهلاً! أنا UltraAgent.\n\n"
        "أقدر أساعدك في:\n"
        "🔍 البحث على الويب\n"
        "💻 كتابة وتنفيذ كود\n"
        "🔗 Automation وHTTP calls\n"
        "📁 إدارة الملفات\n\n"
        "كلمني بأي مهمة!"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    short_term.clear(chat_id)
    await update.message.reply_text("🧹 تم مسح الجلسة.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    task = update.message.text

    # أرسل "جاري التنفيذ..."
    thinking = await update.message.reply_text("⚙️ جاري التنفيذ...")

    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, run_task, task, chat_id
        )
        await thinking.edit_text(response)
    except Exception as e:
        log.error("telegram_handler_error", error=str(e))
        await thinking.edit_text(f"❌ حدث خطأ: {str(e)[:200]}")


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN غير موجود")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("telegram_bot_starting")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
