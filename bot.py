import os
import logging
from gtts import gTTS
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

# --- Load environment variables (.env on Render → Environment) ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Logging (helps you debug from Render → Logs) ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Selam! አማርኛ ጽሑፍ ላክ፤ ድምፅ እመልስልሃለሁ. "
        "Send Amharic text and I'll reply with audio 🎧"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Just send any Amharic sentence.\n"
        "ምሳሌ: ሰላም እንዴት ነህ?"
    )

# --- Text → Speech handler ---
async def tts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = (update.message.text or "").strip()
        if not text:
            return

        # Create mp3 with gTTS (supports Amharic with lang='am')
        tts = gTTS(text=text, lang="am")
        out_file = "voice.mp3"
        tts.save(out_file)

        # Send as audio (works without ffmpeg)
        await update.message.reply_audio(
            audio=open(out_file, "rb"),
            title="Amharic TTS",
            filename="voice.mp3",
            caption="✅ ተዘጋጅቷል"
        )

    except Exception as e:
        logger.exception("TTS error: %s", e)
        await update.message.reply_text("❌ Sorry, I couldn't generate audio.")

# --- Main ---
def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Set it in your Render Environment.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # any text message → TTS
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tts_handler))

    # start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
