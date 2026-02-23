import os
import random
import json
import string
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *

# ---------------- HEALTH SERVER ----------------

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_health_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

# ---------------- BOT INIT ----------------

app = Client(
    "filestorebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

FSUB_FILE = "fsub.json"
BATCH_DB = "batch_db.json"

batch_mode = False
batch_files = []

# ---------------- UTIL ----------------

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

# ---------------- FSUB ----------------

def load_channels():
    if not os.path.exists(FSUB_FILE):
        return []
    with open(FSUB_FILE, "r") as f:
        return json.load(f)

def save_channels(data):
    with open(FSUB_FILE, "w") as f:
        json.dump(data, f)

async def check_fsub(user_id):
    channels = load_channels()
    for ch in channels:
        try:
            member = await app.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# ---------------- START ----------------

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    args = message.text.split()

    # Batch link
    if len(args) > 1:
        batch_id = args[1]
        db = load_json(BATCH_DB)
        if batch_id in db:
            for file_id in db[batch_id]:
                await message.reply_document(
                    file_id,
                    caption=FILE_FOOTER,
                    parse_mode="html"
                )
            return

    # Normal start
    image = random.choice(START_IMAGES)

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📢 Updates", url=UPDATES_CHANNEL),
                InlineKeyboardButton("🛠 Support", url=SUPPORT_LINK)
            ]
        ]
    )

    await message.reply_photo(
        photo=image,
        caption=START_CAPTION,
        reply_markup=buttons,
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

# ---------------- BATCH ----------------

@app.on_message(filters.command("batch") & filters.user(OWNER_ID))
async def batch_start(client, message):
    global batch_mode, batch_files
    batch_mode = True
    batch_files = []
    await message.reply_text("<b>📦 BATCH MODE ENABLED</b>", parse_mode="html")

@app.on_message(filters.command("done") & filters.user(OWNER_ID))
async def batch_done(client, message):
    global batch_mode, batch_files

    if not batch_files:
        await message.reply_text("<b>❌ NO FILES</b>", parse_mode="html")
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
        f"<b>✅ BATCH CREATED</b>\n\n<b>FILES:</b> {count}\n<b>LINK:</b>\n{link}",
        parse_mode="html"
    )

# ---------------- FSUB COMMANDS ----------------

@app.on_message(filters.command("addchnl") & filters.user(OWNER_ID))
async def add_channel(client, message):
    try:
        ch = int(message.command[1])
        channels = load_channels()
        if ch not in channels:
            channels.append(ch)
            save_channels(channels)
            await message.reply_text("✅ Added")
        else:
            await message.reply_text("Already exists")
    except:
        await message.reply_text("Usage: /addchnl -100xxxx")

@app.on_message(filters.command("listchnl") & filters.user(OWNER_ID))
async def list_channel(client, message):
    channels = load_channels()
    await message.reply_text(str(channels))

@app.on_message(filters.command("delchnl") & filters.user(OWNER_ID))
async def del_channel(client, message):
    try:
        ch = int(message.command[1])
        channels = load_channels()
        if ch in channels:
            channels.remove(ch)
            save_channels(channels)
            await message.reply_text("Removed")
        else:
            await message.reply_text("Not found")
    except:
        await message.reply_text("Usage: /delchnl -100xxxx")

# ---------------- MAIN ----------------

if __name__ == "__main__":
    threading.Thread(target=run_health_server).start()
    app.start()
    print("Bot Starting...")
    app.run()
