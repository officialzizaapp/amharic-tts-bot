import os
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from dotenv import load_dotenv
import asyncio
import edge_tts

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

VOICE = "am-ET-MekdesNeural"  # ✅ Amharic Neural Voice
OUTPUT_FILE = "voice.mp3"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Selam! አማርኛ ጽሑፍ ላክ እና ድምፅ እመልስልሃለሁ 🎤"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        communicate = edge_tts.Communicate(text=text, voice=VOICE)
        await communicate.save(OUTPUT_FILE)

        await update.message.reply_voice(voice=open(OUTPUT_FILE, "rb"))

    except Exception as e:
        await update.message.reply_text("❌ Sorry, I couldn't generate audio.")
        print("TTS ERROR:", e)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
