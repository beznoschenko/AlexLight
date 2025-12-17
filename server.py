from quart import Quart, request, jsonify, render_template
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from dotenv import load_dotenv
import os
import re
import time
from datetime import datetime, timedelta
import asyncio

# ---------- ENV ----------
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL = "SvitloOleksandriyskohoRaionu"

# ---------- APP ----------
app = Quart(__name__)

# ---------- CACHE ----------
CACHE = {}
CACHE_TIME = 120  # сек

# ---------- TELETHON ----------
client = TelegramClient("user_session", API_ID, API_HASH)


@app.before_serving
async def startup():
    if not client.is_connected():
        await client.connect()


@app.after_serving
async def shutdown():
    if client.is_connected():
        await client.disconnect()


async def get_messages(limit=50):
    if not client.is_connected():
        await client.connect()

    return await client(
        GetHistoryRequest(
            peer=CHANNEL,
            limit=limit,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0,
        )
    )


# ---------- PARSER ----------
def parse_ranges(text, queue):
    pattern = rf"Черга\s*{re.escape(queue)}\s*[:\-]\s*([0-9,\-– ]+)"
    match = re.search(pattern, text)
    if not match:
        return []

    ranges = []
    for part in match.group(1).replace("–", "-").split(","):
        try:
            start, end = part.strip().split("-")
            ranges.append([int(start), int(end)])
        except ValueError:
            continue

    return ranges


# ---------- ROUTES ----------
@app.route("/")
async def index_page():
    return await render_template("index.html")


@app.route("/health")
async def health():
    """Ендпоінт БЕЗ Telethon — ідеальний для GitHub Actions"""
    return jsonify({"status": "ok"})


@app.route("/api/schedule")
async def schedule():
    queue = request.args.get("queue")
    date_param = request.args.get("date")

    if not queue:
        return jsonify({"ranges": []})

    target_date = (
        datetime.now().date() + timedelta(days=1)
        if date_param == "tomorrow"
        else datetime.now().date()
    )

    target_str = target_date.strftime("%d.%m.%Y")
    cache_key = f"{queue}_{target_str}"
    now = time.time()

    if cache_key in CACHE and now - CACHE[cache_key]["time"] < CACHE_TIME:
        return jsonify(CACHE[cache_key]["data"])

    try:
        messages = await get_messages()
    except Exception as e:
        return jsonify({"error": "telegram_error", "details": str(e)}), 500

    latest_msg = None
    for msg in messages.messages:
        if msg.message and target_str in msg.message:
            latest_msg = msg
            break

    if not latest_msg:
        return jsonify({"ranges": []})

    ranges = parse_ranges(latest_msg.message, queue)
    if not ranges:
        return jsonify({"ranges": []})

    data = {
        "ranges": ranges,
        "sourcePost": f"https://t.me/{CHANNEL}/{latest_msg.id}",
    }

    CACHE[cache_key] = {"time": now, "data": data}
    return jsonify(data)


# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
