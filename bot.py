import random
import json
import os
import string
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *

app = Client(
    "filestorebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

FSUB_FILE = "fsub_channels.json"
BATCH_DB = "batch_db.json"

batch_mode = False
batch_files = []


# ---------------- Utility ----------------

def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def generate_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


# ---------------- START ----------------

@app.on_message(filters.command("start"))
async def start(client, message):

    args = message.text.split()

    # If batch link used
    if len(args) > 1:
        batch_id = args[1]
        db = load_json(BATCH_DB)

        if batch_id in db:
            files = db[batch_id]
            for file_id in files:
                await message.reply_document(
                    file_id,
                    caption=FILE_FOOTER,
                    parse_mode="html"
                )
            return

    image = random.choice(START_IMAGES)

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📢 Updates", url="https://t.me/Hindi_Tv_Verse"),
                InlineKeyboardButton("🛠 Support", url="https://t.me/SerialVerse_support")
            ]
        ]
    )

    await message.reply_photo(
        photo=image,
        caption=START_CAPTION,
        reply_markup=buttons,
        parse_mode="html"
    )


# ---------------- BATCH START ----------------

@app.on_message(filters.command("batch") & filters.user(OWNER_ID))
async def batch_start(client, message):
    global batch_mode, batch_files
    batch_mode = True
    batch_files = []
    await message.reply_text("<b>📦 BATCH MODE ENABLED.\nForward files.\nSend /done when finished.</b>", parse_mode="html")


# ---------------- DONE ----------------

@app.on_message(filters.command("done") & filters.user(OWNER_ID))
async def batch_done(client, message):
    global batch_mode, batch_files

    if not batch_files:
        await message.reply_text("<b>❌ No files in batch.</b>", parse_mode="html")
        return

    batch_mode = False
    batch_id = generate_id()

    db = load_json(BATCH_DB)
    db[batch_id] = batch_files
    save_json(BATCH_DB, db)

    bot_username = (await app.get_me()).username
    link = f"https://t.me/{bot_username}?start={batch_id}"

    count = len(batch_files)
    batch_files = []

    await message.reply_text(
        f"<b>✅ BATCH CREATED SUCCESSFULLY!</b>\n\n"
        f"<b>📦 Files:</b> {count}\n"
        f"<b>🔗 Link:</b>\n{link}",
        parse_mode="html"
    )


# ---------------- FILE HANDLER ----------------

@app.on_message(filters.document | filters.video | filters.audio)
async def file_handler(client, message):
    global batch_mode, batch_files

    file = message.document or message.video or message.audio

    size_mb = round(file.file_size / (1024 * 1024), 2)

    caption = f"""
<b>📂 FILE NAME:</b> {file.file_name}
<b>📦 SIZE:</b> {size_mb} MB

{FILE_FOOTER}
"""

    await message.reply_document(
        file.file_id,
        caption=caption,
        parse_mode="html"
    )

    if batch_mode and message.from_user.id == OWNER_ID:
        batch_files.append(file.file_id)


app.run()
