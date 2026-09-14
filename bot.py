import os, json, requests, asyncio
from flask import Flask
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
BIN_ID = os.getenv("JSONBIN_ID")
BIN_KEY = os.getenv("JSONBIN_KEY")
FILE = "data.json"
BOT_USERNAME = "AP91426_bot"
OWNER_USERNAME = "NormanLucban"
OWNER_ID = 6742733767
DEFAULT_CHANNEL = "@invitenowmore"

web_app = Flask(__name__)
@web_app.route('/')
def home(): return f"Bot alive! Owner: @{OWNER_USERNAME} -> Posting to {DEFAULT_CHANNEL}"

def run_web():
    asyncio.set_event_loop(asyncio.new_event_loop())
    web_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), use_reloader=False)

def load_data():
    if BIN_ID and BIN_KEY:
        try:
            r = requests.get(f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest", headers={"X-Master-Key": BIN_KEY}, timeout=10)
            data = r.json()['record']
            # Lagyan ng laman pag empty
            if not data.get("posts"):
                data["posts"] = [
                    "Hello! 👋 Welcome to @invitenowmore - Your Referral Link Channel!",
                    "Hello! Your opportunity is here. Click my referral link to start: 👇\n\nhttps://shareappurl.com/bbqsort/share/html?referrer=1304098\n\nComment 'HOW' or DM me after you register!",
                    "Hello everyone! Let's earn together! Join now: https://t.me/invitenowmore"
                ]
            return data
        except: pass
    try:
        with open(FILE,"r") as f:
            data = json.load(f)
            if not data.get("posts"):
                data["posts"] = ["Hello! 👋 Welcome to @invitenowmore!"]
            return data
    except:
        return {
            "posts":[
                "Hello! 👋 Welcome to @invitenowmore - Your Referral Link Channel!",
                "Hello! Your opportunity is here. Click my referral link to start: 👇\n\nhttps://shareappurl.com/bbqsort/share/html?referrer=1304098",
                "Hello! Let's earn together! Comment 'HOW' after register!"
            ],
            "index":0,
            "channel_id":DEFAULT_CHANNEL,
            "owner":OWNER_ID
        }

def save_data(d):
    if BIN_ID and BIN_KEY:
        try:
            requests.put(f"https://api.jsonbin.io/v3/b/{BIN_ID}", json=d, headers={"X-Master-Key": BIN_KEY, "Content-Type":"application/json"}, timeout=10)
            return
        except: pass
    with open(FILE,"w") as f: json.dump(d,f,indent=2)

def is_owner(update):
    user = update.effective_user
    if not user: return False
    return (user.username and user.username.lower() == OWNER_USERNAME.lower()) or user.id == OWNER_ID

async def set_channel(update, context):
    if not is_owner(update): return
    data=load_data()
    data["channel_id"]=DEFAULT_CHANNEL
    save_data(data)
    await update.message.reply_text(f"✅ Posting to {DEFAULT_CHANNEL} - https://t.me/invitenowmore")

async def add(update, context):
    if not is_owner(update): return
    data=load_data()
    txt=" ".join(context.args)
    if not txt: return await update.message.reply_text("Usage: /add Hello your text")
    data["posts"].append(txt); save_data(data)
    await update.message.reply_text(f"✅ Added #{len(data['posts'])} - Will post to {DEFAULT_CHANNEL}")

async def list_posts(update, context):
    if not is_owner(update): return
    data=load_data()
    await update.message.reply_text(f"TOTAL: {len(data['posts'])} posts -> {data['channel_id']}\nNext: #{data['index']+1}")
    for i, p in enumerate(data["posts"][:20]):
        await update.message.reply_text(f"{i+1}. {p[:100]}")

async def delete_post(update, context):
    if not is_owner(update): return
    data=load_data()
    try:
        num=int(context.args[0])-1
        data["posts"].pop(num)
        save_data(data)
        await update.message.reply_text(f"🗑️ Deleted #{num+1}")
    except: await update.message.reply_text("Use: /del 1")

async def status(update, context):
    if not is_owner(update): return
    data=load_data()
    await update.message.reply_text(f"🤖 LIVE!\nChannel: {data['channel_id']}\nPosts: {len(data['posts'])}\nNext: {data['index']+1}\n\nMay laman na HELLO! Mag popost na every 5 hrs!")

async def error_handler(update, context):
    print(f"Error ignored: {context.error}")

async def auto_post(context):
    data=load_data()
    if not data["posts"] or not data["channel_id"]: return
    text = data["posts"][data["index"]]
    try:
        for i in range(0, len(text), 4000):
            await context.bot.send_message(data["channel_id"], text[i:i+4000])
        data["index"]=(data["index"]+1)%len(data["posts"])
        save_data(data)
        print(f"✅ Posted to {data['channel_id']}")
    except Exception as e:
        print(f"Post failed (will retry): {e}")

if __name__=="__main__":
    asyncio.set_event_loop(asyncio.new_event_loop())
    threading.Thread(target=run_web, daemon=True).start()
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("set", set_channel))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_posts))
    app.add_handler(CommandHandler("del", delete_post))
    app.add_handler(CommandHandler("delete", delete_post))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("start", status))
    app.add_error_handler(error_handler)
    app.job_queue.run_repeating(auto_post, interval=5*60*60, first=10)
    print(f"Bot started with HELLO posts -> {DEFAULT_CHANNEL}")
    app.run_polling(drop_pending_updates=True)
