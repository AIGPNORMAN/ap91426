import os, json
from flask import Flask
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("8602421101:AAHcccYRQ-Ksp3CpdZW_P7Xzis-LCEx_qQk")
FILE = "data.json"

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    web_app.run(host='0.0.0.0', port=10000)

def load_data():
    try:
        with open(FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {"posts": [], "index": 0, "channel_id": None}

def save_data(data):
    with open(FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

async def set_channel(update, context):
    data = load_data(); data["channel_id"] = update.effective_chat.id; save_data(data)
    await update.message.reply_text(f"Channel set! I will post here.\nID: {data['channel_id']}")

async def add(update, context):
    text = " ".join(context.args)
    if not text: return await update.message.reply_text("Usage: /add your text here")
    data = load_data(); data["posts"].append(text); save_data(data)
    await update.message.reply_text(f"Added! Total posts: {len(data['posts'])}")

async def list_posts(update, context):
    data = load_data()
    if not data["posts"]: return await update.message.reply_text("Empty. Use /add to add posts.")
    msg = "\n".join([f"{i+1}. {p}" for i,p in enumerate(data["posts"])])
    msg += f"\n\nNext to post: #{data['index']+1}"
    await update.message.reply_text(msg)

async def delete_post(update, context):
    data = load_data()
    if not context.args: return await update.message.reply_text("Usage: /del 2")
    try:
        num = int(context.args[0]) - 1
        deleted = data["posts"].pop(num)
        if data["index"] >= len(data["posts"]): data["index"] = 0
        save_data(data)
        await update.message.reply_text(f"Deleted: {deleted}\nRemaining: {len(data['posts'])}")
    except:
        await update.message.reply_text("Invalid number. Check /list first.")

async def auto_post(context):
    data = load_data()
    if not data["posts"] or not data["channel_id"]: return
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
    app.add_handler(CommandHandler("del", delete_post))
    app.add_handler(CommandHandler("delete", delete_post))
    app.job_queue.run_repeating(auto_post, interval=5*60*60, first=10)
    app.run_polling()
