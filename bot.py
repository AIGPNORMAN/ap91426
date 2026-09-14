import os, json
from flask import Flask
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
FILE = "data.json"

web_app = Flask(__name__)
@web_app.route('/')
def home():
    return "Bot alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

def load_data():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"posts": [], "index": 0, "channel_id": None}

def save_data(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if context.args:
        try:
            channel_id = int(context.args[0])
        except:
            return await update.effective_message.reply_text("Invalid ID. Must be -100xxx")
    else:
        channel_id = update.effective_chat.id

    data["channel_id"] = channel_id
    save_data(data)

    await update.effective_message.reply_text(f"✅ SET! ID: {channel_id}\nTrying to post in your channel...")

    try:
        await context.bot.send_message(chat_id=channel_id, text="✅ Bot is ACTIVE here! I will auto post every 5 hours! 🚀")
        await update.effective_message.reply_text("Check your channel! I posted ACTIVE there!")
    except Exception as e:
        await update.effective_message.reply_text(f"ID saved but I cannot post in channel. Error: {e}\nAre you sure I am admin there?")

async def add(update, context):
    text = " ".join(context.args)
    if not text:
        return await update.effective_message.reply_text("Usage: /add Your post here")
    data = load_data()
    data["posts"].append(text)
    save_data(data)
    await update.effective_message.reply_text(f"Added! Total: {len(data['posts'])}")

async def list_posts(update, context):
    data = load_data()
    if not data["posts"]:
        return await update.effective_message.reply_text("No posts yet.")
    msg = "\n".join([f"{i+1}. {p}" for i, p in enumerate(data["posts"])])
    msg += f"\n\nNext: #{data['index']+1} | Channel ID: {data['channel_id']}"
    await update.effective_message.reply_text(msg)

async def auto_post(context):
    data = load_data()
    if not data["posts"] or not data["channel_id"]:
        return
    post = data["posts"][data["index"]]
    await context.bot.send_message(chat_id=data["channel_id"], text=post)
    data["index"] = (data["index"] + 1) % len(data["posts"])
    save_data(data)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("set", set_channel))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_posts))
    app.job_queue.run_repeating(auto_post, interval=5*60*60, first=10)
    app.run_polling(drop_pending_updates=True)
