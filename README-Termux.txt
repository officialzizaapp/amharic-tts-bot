# Amharic Text-to-Speech Bot (Offline, Termux-ready)

This bot runs fully offline after the first model download.
It supports:
- Multiple Amharic voices (menu)
- Pitch control
- Per-user voice clone (send a 60s voice note with /setvoice)
- Works on Android (Termux) 24/7

## 1) Termux setup (copy–paste)
```
pkg update -y && pkg upgrade -y
pkg install -y python ffmpeg git libsndfile
pip install --upgrade pip
```

## 2) Get the project
- If you downloaded the ZIP: extract it to a folder in Termux.
- Or clone later from your own repo.

## 3) Install Python dependencies
```
pip install -r requirements.txt
```

> If `torch`/`torchaudio` fail on your device CPU arch, run the bot on a laptop first,
> or install prebuilt wheels for aarch64. (You can still run embeddings on a PC and copy `.npy` files into `voices/`.)

## 4) Add your token
Create `.env` in the same folder:
```
BOT_TOKEN=123456789:ABCDEF_your_token_here
```

## 5) Run
```
python bot.py
```

## Commands
- `/start` – help
- `/voice` – choose Amharic voice
- `/pitch` – set pitch (0 default)
- `/setvoice` – send a 60s voice note to clone your voice
- `/resetvoice` – remove your cloned voice

## Notes
- First run downloads models (~hundreds of MB).
- After that, bot is offline.
- On Termux, use an app like Termux:Widget or `tmux` to keep it running.
