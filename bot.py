import os, json
from flask import Flask
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
FILE = "data.json"
BOT_USERNAME = "@AP91426_bot"

web_app = Flask(__name__)
@web_app.route('/')
def home():
    return "Bot alive!"
def run_web():
    web_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def load_data():
    try:
        with open(FILE, "r") as f: return json.load(f)
    except: return {"posts": [], "index": 0, "channel_id": None}
def save_data(d):
    with open(FILE, "w") as f: json.dump(d, f, indent=2)

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if context.args:
        try: channel_id = int(context.args[0])
        except: return await update.message.reply_text("Invalid ID. Use -100xxx")
    else: channel_id = update.effective_chat.id
    data["channel_id"] = channel_id
    save_data(data)
    await update.message.reply_text(f"✅ SET! ID: {channel_id}")
    try:
        await context.bot.send_message(channel_id, "✅ Bot is ACTIVE here! Will auto post every 5 hours! 🚀")
    except: pass

async def add(update, context):
    text = " ".join(context.args)
    if not text: return await update.message.reply_text("Usage: /add text")
    data = load_data(); data["posts"].append(text); save_data(data)
    await update.message.reply_text(f"Added! Total {len(data['posts'])}")

async def list_posts(update, context):
    data = load_data()
    if not data["posts"]: return await update.message.reply_text("Empty. Use /add")
    msg = "\n".join([f"{i+1}. {p}" for i,p in enumerate(data["posts"])])
    await update.message.reply_text(msg + f"\n\nNext: #{data['index']+1}")

async def handle_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if BOT_USERNAME.lower() in update.message.text.lower():
        await update.message.reply_text("Yes? I'm here! Active! Use /set, /add, /list")

async def auto_post(context):
    data = load_data()
    if not data["posts"] or not data["channel_id"]: return
    await context.bot.send_message(data["channel_id"], data["posts"][data["index"]])
    data["index"] = (data["index"]+1) % len(data["posts"])
    save_data(data)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("set", set_channel))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_posts))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_mention))
    app.job_queue.run_repeating(auto_post, interval=5*60*60, first=10)
    app.run_polling(drop_pending_updates=True)
