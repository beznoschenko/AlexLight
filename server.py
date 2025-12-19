from quart import Quart, request, jsonify, render_template
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from dotenv import load_dotenv
import os
import re
import time
from datetime import datetime, timedelta

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL = "SvitloOleksandriyskohoRaionu"

app = Quart(__name__)
CACHE = {}
CACHE_TIME = 120  # сек

client = TelegramClient("render_user_session_v1", API_ID, API_HASH)

async def start_client():
    if not client.is_connected():
        await client.connect()


@app.before_serving
async def startup():
    await start_client()

# --- отримання останніх повідомлень ---
async def get_messages(limit=50):
    return await client(GetHistoryRequest(
        peer=CHANNEL,
        limit=limit,
        offset_date=None,
        offset_id=0,
        max_id=0,
        min_id=0,
        add_offset=0,
        hash=0
    ))

# --- парсинг діапазонів для черги ---
def parse_ranges(text, queue):
    pattern = rf"Черга\s*{re.escape(queue)}\s*[:\-]\s*([0-9,\-– ]+)"
    match = re.search(pattern, text)
    if not match:
        return []
    ranges = []
    for part in match.group(1).replace("–","-").split(","):
        try:
            start, end = part.strip().split("-")
            ranges.append([int(start), int(end)])
        except:
            pass
    return ranges

# --- головна сторінка ---
@app.route("/")
async def index_page():
    return await render_template("index.html")

# --- API: графік ---
@app.route("/api/schedule")
async def schedule():
    queue = request.args.get("queue")
    date_param = request.args.get("date")  # "today" або "tomorrow"
    if not queue:
        return jsonify({"ranges": []})

    if date_param == "tomorrow":
        target_date = datetime.now().date() + timedelta(days=1)
    else:
        target_date = datetime.now().date()

    target_str = target_date.strftime("%d.%m.%Y")
    cache_key = f"{queue}_{target_str}"
    now = time.time()

    if cache_key in CACHE and now - CACHE[cache_key]["time"] < CACHE_TIME:
        return jsonify(CACHE[cache_key]["data"])

    messages = await get_messages()

    # шукаємо останнє повідомлення з потрібною датою в тексті
    latest_msg = None
    for msg in messages.messages:
        if msg.message and target_str in msg.message:
            latest_msg = msg
            break

    if latest_msg:
        ranges = parse_ranges(latest_msg.message, queue)
        if ranges:
            data = {
                "ranges": ranges,
                "sourcePost": f"https://t.me/{CHANNEL}/{latest_msg.id}"
            }
            CACHE[cache_key] = {"time": now, "data": data}
            return jsonify(data)

    return jsonify({"ranges": []})

# --- запуск ---
if __name__ == "__main__":
    app.run(port=5000, debug=True)


