import os, json
from flask import Flask
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
FILE = "data.json"
BOT_USERNAME = "AP91426_bot"
OWNER_ID = 6742733767

web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot alive! Owner: 6742733767 - Group: -1004438442110"
def run_web(): web_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def load_data():
    try:
        with open(FILE,"r") as f: return json.load(f)
    except: return {"posts":[],"index":0,"channel_id":-1004438442110,"owner":OWNER_ID}

def save_data(d):
    with open(FILE,"w") as f: json.dump(d,f,indent=2)

async def set_channel(update, context):
    data=load_data()
    if update.effective_user.id!= OWNER_ID:
        return await update.message.reply_text("❌ OWNER ONLY! Your ID is not authorized.")
    cid=int(context.args[0]) if context.args else update.effective_chat.id
    data["channel_id"]=cid
    data["owner"]=OWNER_ID
    save_data(data)
    await update.message.reply_text(f"✅ OWNER CONFIRMED: {OWNER_ID}\nGroup ID: {cid}\nOnly you can use commands!")

async def add(update, context):
    data=load_data()
    if update.effective_user.id!= OWNER_ID:
        return await update.message.reply_text("❌ OWNER ONLY CAN ADD!")
    txt=" ".join(context.args)
    if not txt: return await update.message.reply_text("Usage: /add@AP91426_bot your text")
    data["posts"].append(txt); save_data(data)
    await update.message.reply_text(f"✅ Added #{len(data['posts'])} Total: {len(data['posts'])} Unlimited!")

async def list_posts(update, context):
    data=load_data()
    if update.effective_user.id!= OWNER_ID:
        return await update.message.reply_text("❌ OWNER ONLY!")
    if not data["posts"]: return await update.message.reply_text("Empty list. Use /add")
    total=len(data["posts"])
    await update.message.reply_text(f"TOTAL: {total} posts - Next: #{data['index']+1} Owner: {OWNER_ID}")
    for i in range(0, total, 20):
        chunk=data["posts"][i:i+20]
        msg="\n".join([f"{i+j+1}. {p[:70]}" for j,p in enumerate(chunk)])
        await update.message.reply_text(f"{i+1}-{i+len(chunk)}:\n{msg}")

async def delete_post(update, context):
    data=load_data()
    if update.effective_user.id!= OWNER_ID:
        return await update.message.reply_text("❌ OWNER ONLY CAN DELETE!")
    if not context.args: return await update.message.reply_text("Use: /del@AP91426_bot 5")
    try:
        num=int(context.args[0])-1
        data["posts"].pop(num)
        if data["index"] >= len(data["posts"]): data["index"]=0
        save_data(data)
        await update.message.reply_text(f"🗑️ Deleted #{num+1} Left: {len(data['posts'])}")
    except: await update.message.reply_text("Invalid number!")

async def mention_reply(update, context):
    if BOT_USERNAME.lower() in (update.message.text or "").lower():
        data=load_data()
        await update.message.reply_text(f"ACTIVE! Owner: {OWNER_ID} Total: {len(data['posts'])} Next: #{data['index']+1}")

async def auto_post(context):
    data=load_data()
    if not data["posts"] or not data["channel_id"]: return
    await context.bot.send_message(data["channel_id"], data["posts"][data["index"]])
    data["index"]=(data["index"]+1)%len(data["posts"])
    save_data(data)

if __name__=="__main__":
    threading.Thread(target=run_web).start()
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("set", set_channel))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_posts))
    app.add_handler(CommandHandler("del", delete_post))
    app.add_handler(CommandHandler("delete", delete_post))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), mention_reply))
    app.job_queue.run_repeating(auto_post, interval=5*60*60, first=10)
    app.run_polling(drop_pending_updates=True)

