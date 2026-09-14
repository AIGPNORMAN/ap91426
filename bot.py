import os, json, requests, asyncio
from flask import Flask
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = os.getenv("BOT_TOKEN")
BIN_ID = os.getenv("JSONBIN_ID")
BIN_KEY = os.getenv("JSONBIN_KEY")
FILE = "data.json"
BOT_USERNAME = "AP91426_bot"
OWNER_ID = 6742733767

web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot alive!"
def run_web():
    asyncio.set_event_loop(asyncio.new_event_loop())
    web_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), use_reloader=False)

def load_data():
    if BIN_ID and BIN_KEY:
        try:
            r=requests.get(f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest", headers={"X-Master-Key": BIN_KEY}, timeout=10)
            return r.json()['record']
        except: pass
    try:
        with open(FILE,"r") as f: return json.load(f)
    except: return {"posts":[],"index":0,"channel_id":-1004438442110,"owner":OWNER_ID}
def save_data(d):
    if BIN_ID and BIN_KEY:
        try:
            requests.put(f"https://api.jsonbin.io/v3/b/{BIN_ID}", json=d, headers={"X-Master-Key": BIN_KEY}, timeout=10)
            return
        except: pass
    with open(FILE,"w") as f: json.dump(d,f,indent=2)

async def set_channel(update, context):
    data=load_data()
    if update.effective_user.id!=OWNER_ID: return await update.message.reply_text("❌ OWNER ONLY!")
    data["channel_id"]=int(context.args[0]) if context.args else update.effective_chat.id
    save_data(data); await update.message.reply_text(f"Set {data['channel_id']}")
async def add(update, context):
    data=load_data()
    if update.effective_user.id!=OWNER_ID: return await update.message.reply_text("❌ OWNER ONLY!")
    txt=" ".join(context.args)
    if not txt: return await update.message.reply_text("Usage /add text")
    data["posts"].append(txt); save_data(data); await update.message.reply_text(f"Added #{len(data['posts'])}")
async def list_posts(update, context):
    data=load_data()
    await update.message.reply_text(f"TOTAL {len(data['posts'])}")
async def delete_post(update, context):
    data=load_data()
    try:
        data["posts"].pop(int(context.args[0])-1); save_data(data)
        await update.message.reply_text("Deleted")
    except: await update.message.reply_text("Invalid")
async def mention_reply(update, context):
    if BOT_USERNAME.lower() in (update.message.text or "").lower():
        data=load_data(); await update.message.reply_text(f"ACTIVE {len(data['posts'])}")
async def auto_post(context):
    data=load_data()
    if not data["posts"] or not data["channel_id"]: return
    await context.bot.send_message(data["channel_id"], data["posts"][data["index"]])
    data["index"]=(data["index"]+1)%len(data["posts"]); save_data(data)

if __name__=="__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("set", set_channel))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_posts))
    app.add_handler(CommandHandler("del", delete_post))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), mention_reply))
    app.job_queue.run_repeating(auto_post, interval=5*60*60, first=10)
    app.run_polling(drop_pending_updates=True)
