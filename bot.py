from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
VOICE_ID  = os.environ.get("VOICE_ID", "amharic")  # your TTS selector, if you use it

# --- add this ---
async def on_startup(app: Application) -> None:
    # Ensure no webhook is set; drop old queued updates to avoid repeats
    await app.bot.delete_webhook(drop_pending_updates=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Selam! አማርኛ ጽሑፍ ላኩ፣ ድምፅ እመልሳለሁ 🎧")

async def echo_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return
    # ... your TTS -> audio bytes code ...
    # await update.message.reply_voice(voice=audio_bytes)  # or send_audio(...)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.post_init = on_startup    # <-- this line ensures webhook is cleared

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_tts))

    # Use long polling (single instance only)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
