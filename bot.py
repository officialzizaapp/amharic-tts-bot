\
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from tts_engine import amharic_tts_to_ogg
from embedder import wav_to_xvector
import numpy as np
import subprocess

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
VOICES_DIR = "voices"
os.makedirs(VOICES_DIR, exist_ok=True)

# Per-user settings in-memory (simple)
USER_SETTINGS = {}  # user_id -> {"voice": "abraham", "pitch": 0}

HELP = (
    "👋 ሰላም! አማርኛ ጽሑፍ ላኩ እና ድምፅ በመልስ ይቀበሉ.\n"
    "• /voice ድምፅ መምረጫ\n"
    "• /pitch የድምፅ ከፍታ/ጥልቀት\n"
    "• /setvoice 60 ሰከንድ ድምፅ ይላኩ ለመቅናት\n"
    "• /resetvoice ወደ ነባሪ ይመለሱ\n"
    "• በቀጥታ ጽሑፍ ካልኩ ድምፅ እመልሳለሁ\n"
)

VOICE_OPTIONS = [
    ("አብርሃም", "abraham"),
    ("አማኑኤል", "amanuel"),
    ("ሚካኤል", "mikael"),
    ("ሀና", "hana"),
    ("ሳራ", "sara"),
]

def get_user_settings(user_id: int):
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = {"voice": "abraham", "pitch": 0}
    return USER_SETTINGS[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP)

def voice_keyboard():
    buttons = [[InlineKeyboardButton(name, callback_data=f"voice:{val}") for name, val in VOICE_OPTIONS[:3]],
               [InlineKeyboardButton(name, callback_data=f"voice:{val}") for name, val in VOICE_OPTIONS[3:]],
               [InlineKeyboardButton("Back", callback_data="back:main")]]
    return InlineKeyboardMarkup(buttons)

def pitch_keyboard(current: int):
    labels = ["-4", "-2", "0", "+2", "+4"]
    vals = [-4, -2, 0, 2, 4]
    row = [InlineKeyboardButton(("✅ " if v == current else "") + f"Pitch {lab}", callback_data=f"pitch:{v}") for lab, v in zip(labels, vals)]
    return InlineKeyboardMarkup([row, [InlineKeyboardButton("Back", callback_data="back:main")]])

async def voice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ድምፅ ይምረጡ:", reply_markup=voice_keyboard())

async def pitch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    us = get_user_settings(update.effective_user.id)
    await update.message.reply_text("Pitch ይምረጡ:", reply_markup=pitch_keyboard(us["pitch"]))

async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = query.from_user.id
    us = get_user_settings(uid)

    if data.startswith("voice:"):
        us["voice"] = data.split(":",1)[1]
        await query.edit_message_text(f"✅ ድምፅ ተመረጠ: {us['voice']}")
    elif data.startswith("pitch:"):
        us["pitch"] = int(data.split(":",1)[1])
        await query.edit_message_text(f"✅ Pitch = {us['pitch']}")
    elif data.startswith("back:"):
        await query.edit_message_text("✔ ተመለስ")

async def setvoice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("እባክዎ 60 ሰከንድ ድምፅ እንደ voice note ወይም audio ይላኩ።")

async def resetvoice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    p = os.path.join(VOICES_DIR, f\"{user_id}.npy\")
    if os.path.exists(p):
        os.remove(p)
        await update.message.reply_text(\"ድምፅ ወደ ነባሪ ተመለሰ.\")
    else:
        await update.message.reply_text(\"ተቀመጠ ድምፅ የለም.\")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user_id = update.effective_user.id
    await msg.reply_text(\"ድምፅ ተቀብዬ እየሠራ ነኝ...\")

    tgfile = None
    if msg.voice:
        tgfile = await msg.voice.get_file()
    elif msg.audio:
        tgfile = await msg.audio.get_file()
    elif msg.document and msg.document.mime_type and msg.document.mime_type.startswith(\"audio/\"):
        tgfile = await msg.document.get_file()
    else:
        return

    ogg = f\"/tmp/{user_id}.ogg\"
    wav = f\"/tmp/{user_id}.wav\"
    await tgfile.download_to_drive(ogg)
    cmd = [\"ffmpeg\", \"-y\", \"-i\", ogg, \"-ac\", \"1\", \"-ar\", \"16000\", wav]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try: os.remove(ogg)
    except: pass

    try:
        emb = wav_to_xvector(wav)
        np.save(os.path.join(VOICES_DIR, f\"{user_id}.npy\"), emb)
        await msg.reply_text(\"✅ ድምፅ ተቀመጠ! ከአሁን በኋላ ቦቱ በድምፅዎ ይናገራል.\")
    except Exception as e:
        await msg.reply_text(\"❌ አልተሳካም. እባክዎ እንደገና ይሞክሩ ወይም ትልቅ ረድፍ ይላኩ.\")
        raise e
    finally:
        try: os.remove(wav)
        except: pass

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    us = get_user_settings(uid)
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.RECORD_VOICE)
    ogg = amharic_tts_to_ogg(text, user_id=uid, voice_name=us.get(\"voice\"), pitch_semitones=us.get(\"pitch\",0))
    try:
        await update.message.reply_voice(voice=open(ogg, \"rb\"))
    finally:
        try: os.remove(ogg)
        except: pass

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler(\"start\", start))
    app.add_handler(CommandHandler(\"help\", help_cmd))
    app.add_handler(CommandHandler(\"voice\", voice_cmd))
    app.add_handler(CommandHandler(\"pitch\", pitch_cmd))
    app.add_handler(CommandHandler(\"setvoice\", setvoice_cmd))
    app.add_handler(CommandHandler(\"resetvoice\", resetvoice_cmd))
    app.add_handler(CallbackQueryHandler(on_cb))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO | (filters.Document.AUDIO), handle_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == \"__main__\":
    main()
