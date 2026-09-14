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
# YUNG LINK CHANNEL MO - DITO NA SIYA MAG POPOST
DEFAULT_CHANNEL = "@invitenowmore" # https://t.me/invitenowmore

web_app = Flask(__name__)
@web_app.route('/')
def home(): return f"Bot alive! Owner: @{OWNER_USERNAME} -> Posting to {DEFAULT_CHANNEL} | PM Control Only!"

def run_web():
    asyncio.set_event_loop(asyncio.new_event_loop())
    web_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), use_reloader=False)

def load_data():
    if BIN_ID and BIN_KEY:
        try:
            r = requests.get(f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest", headers={"X-Master-Key": BIN_KEY}, timeout=10)
            return r.json()['record']
        except: pass
    try:
        with open(FILE,"r") as f: return json.load(f)
    except: return {"posts":[],"index":0,"channel_id":DEFAULT_CHANNEL,"owner":OWNER_ID, "owner_username": OWNER_USERNAME}

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
    if not is_owner(update):
        return await update.message.reply_text(f"❌ Only @{OWNER_USERNAME} - PM only!")
    data=load_data()
    if context.args:
        raw = context.args[0]
        # Support @username or -100 ID
        if raw.startswith("@") or raw.startswith("https://t.me/"):
            cid = raw.replace("https://t.me/", "@")
            if not cid.startswith("@"): cid = "@" + cid
        else:
            try: cid = int(raw)
            except: cid = raw
    else:
        cid = DEFAULT_CHANNEL
    data["channel_id"]=cid
    save_data(data)
    await update.message.reply_text(f"✅ Now posting to: {cid}\nLink: https://t.me/{str(cid).replace('@','')}\nPrivate PM control!")

async def add(update, context):
    if not is_owner(update): return
    data=load_data()
    txt=" ".join(context.args)
    if not txt: return await update.message.reply_text("Usage: /add your text here - 4000 chars")
    data["posts"].append(txt); save_data(data)
    await update.message.reply_text(f"✅ Added #{len(data['posts'])} Total: {len(data['posts'])}\nWill post to {data['channel_id']}")

async def list_posts(update, context):
    if not is_owner(update): return
    data=load_data()
    if not data["posts"]: return await update.message.reply_text("Empty pa - /add ka muna sa PM")
    total=len(data["posts"])
    await update.message.reply_text(f"TOTAL: {total} posts - Next: #{data['index']+1}\nChannel: {data['channel_id']}")
    for i in range(0, min(total, 40), 20):
        chunk=data["posts"][i:i+20]
        msg="\n".join([f"{i+j+1}. {p[:70]}" for j,p in enumerate(chunk)])
        await update.message.reply_text(f"{i+1}-{i+len(chunk)}:\n{msg}")

async def delete_post(update, context):
    if not is_owner(update): return
    data=load_data()
    if not context.args: return await update.message.reply_text("Use: /del 5")
    try:
        num=int(context.args[0])-1
        data["posts"].pop(num)
        if data["index"] >= len(data["posts"]): data["index"]=0
        save_data(data)
        await update.message.reply_text(f"🗑️ Deleted #{num+1} Left: {len(data['posts'])}")
    except: await update.message.reply_text("Invalid number!")

async def status(update, context):
    if not is_owner(update): return
    data=load_data()
    await update.message.reply_text(f"🤖 Status:\nOwner: @{OWNER_USERNAME}\nPosting to: {data['channel_id']}\nLink: https://t.me/{str(data['channel_id']).replace('@','')}\nTotal posts: {len(data['posts'])}\nNext: #{data['index']+1}\n\nPRIVATE PM MODE!")

async def auto_post(context):
    data=load_data()
    if not data["posts"] or not data["channel_id"]: return
    text = data["posts"][data["index"]]
    try:
        for i in range(0, len(text), 4000):
            await context.bot.send_message(data["channel_id"], text[i:i+4000])
        data["index"]=(data["index"]+1)%len(data["posts"])
        save_data(data)
        print(f"Posted to {data['channel_id']}: {text[:50]}")
    except Exception as e:
        print(f"Auto post failed to {data['channel_id']}: {e}")

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
    app.job_queue.run_repeating(auto_post, interval=5*60*60, first=10)
    print(f"Bot started - PM @{OWNER_USERNAME} - Posting to {DEFAULT_CHANNEL}")
    app.run_polling(drop_pending_updates=True)
