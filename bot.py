import os
import asyncio
import requests
import pytz
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

OWNER_USER_ID = 7614459746
IST = pytz.timezone('Asia/Kolkata')
user_history = {}
active_groups = {}
allowed_users = {7614459746}

def get_ist_now():
    return datetime.now(IST)

def parse_time(ts):
    ts = ts.lower().strip().replace(" ", "")
    if not ts: return None
    if 'seconds' in ts or ts.endswith('second') or ts.endswith('sec'):
        num = ts.replace('seconds','').replace('second','').replace('sec','')
        return float(num)/60 if num else None
    elif 'minutes' in ts or ts.endswith('minute') or ts.endswith('mins') or ts.endswith('min'):
        num = ts.replace('minutes','').replace('minute','').replace('mins','').replace('min','')
        return float(num) if num else None
    elif 'hours' in ts or ts.endswith('hour') or ts.endswith('hrs') or ts.endswith('hr'):
        num = ts.replace('hours','').replace('hour','').replace('hrs','').replace('hr','')
        return float(num)*60 if num else None
    elif 'days' in ts or ts.endswith('day'):
        num = ts.replace('days','').replace('day','')
        return float(num)*1440 if num else None
    elif ts.endswith('s'): return float(ts[:-1])/60
    elif ts.endswith('m'): return float(ts[:-1])
    elif ts.endswith('h'): return float(ts[:-1])*60
    elif ts.endswith('d'): return float(ts[:-1])*1440
    else:
        try: return float(ts)
        except: return None

def format_time(minutes):
    total_seconds = int(minutes*60)
    if total_seconds <= 0: return "0 seconds"
    days = total_seconds//86400; remaining = total_seconds%86400
    hours = remaining//3600; remaining = remaining%3600
    mins = remaining//60; secs = remaining%60
    parts = []
    if days > 0: parts.append(f"{days} day{'s' if days!=1 else ''}")
    if hours > 0: parts.append(f"{hours} hour{'s' if hours!=1 else ''}")
    if mins > 0: parts.append(f"{mins} minute{'s' if mins!=1 else ''}")
    if secs > 0 and days == 0: parts.append(f"{secs} second{'s' if secs!=1 else ''}")
    return ", ".join(parts) if parts else "0 seconds"

def get_ai_reply(user_input, chat_id):
    if chat_id not in user_history: user_history[chat_id] = []
    
    messages = [{"role":"system","content":"You are GARAM GAND AI, a premium friendly assistant. Give complete answers. Use emojis. Reply in user's language."}]
    
    for msg in user_history[chat_id][-4:]:
        role = "user" if msg["role"]=="user" else "assistant"
        messages.append({"role":role,"content":msg["content"]})
    
    messages.append({"role":"user","content":user_input})
    
    models = [
        "google/gemini-flash-1.5",
        "meta-llama/llama-3.2-3b-instruct:free",
        "google/gemma-2-9b-it:free",
        "mistralai/mistral-7b-instruct:free"
    ]
    
    for model_name in models:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization":f"Bearer {OPENROUTER_API_KEY}","Content-Type":"application/json"},
                json={"model":model_name,"messages":messages,"temperature":0.8,"max_tokens":500},
                timeout=20
            )
            data = response.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
        except:
            continue
    
    return "😅 Sab models busy hain! Fir se try karo."

def is_allowed(uid): return uid in allowed_users

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ Sirf BOSS!"); return
    if not context.args: await update.message.reply_text("📝 /adduser id"); return
    try: allowed_users.add(int(context.args[0])); await update.message.reply_text("✅ Added!")
    except: await update.message.reply_text("❌ Valid ID!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ Sirf BOSS!"); return
    if not context.args: await update.message.reply_text("📝 /removeuser id"); return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: await update.message.reply_text("😎 BOSS!"); return
        allowed_users.discard(rid); await update.message.reply_text("✅ Removed!")
    except: await update.message.reply_text("❌ Valid ID!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ Sirf BOSS!"); return
    ul = "\n".join([f"• {uid}" for uid in allowed_users])
    await update.message.reply_text(f"👥 Users:\n{ul}\nTotal: {len(allowed_users)}")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        await update.message.reply_text(f"🆔 {update.message.reply_to_message.from_user.id}")
    else: await update.message.reply_text(f"🆔 {update.effective_user.id}")

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members: return
    for u in update.message.new_chat_members:
        if u.id == context.bot.id:
            await context.bot.send_message(update.effective_chat.id, "🤖 Bot Ready! /activate")
        else:
            await context.bot.send_message(update.effective_chat.id, f"✨ Welcome {u.first_name}!")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ Sirf Admin!"); return
    except: await update.message.reply_text("❌ Bot ko Admin banao!"); return
    
    target, ts = None, "1h"
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if context.args: ts = " ".join(context.args)
    elif context.args and len(context.args)>=2:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user; ts = " ".join(context.args[1:])
        except: return
    else: await update.message.reply_text("🔇 /mute 10s 5m 2h 1d"); return
    
    if not target or target.id==update.effective_user.id or target.is_bot: return
    mm = parse_time(ts)
    if not mm or mm>43200 or mm<=0: return
    
    nw, ut = get_ist_now(), get_ist_now()+timedelta(minutes=mm)
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
            permissions=ChatPermissions(can_send_messages=False,can_send_audios=False,can_send_documents=False,can_send_photos=False,can_send_videos=False,can_send_video_notes=False,can_send_voice_notes=False,can_send_polls=False,can_send_other_messages=False,can_add_web_page_previews=False,can_change_info=False,can_invite_users=False,can_pin_messages=False),until_date=ut)
        
        tn = target.first_name or "User"
        if target.last_name: tn += f" {target.last_name}"
        await update.message.reply_text(f"🔇 MUTED!\n👤 {tn}\n⏱️ {format_time(mm)}\n🔓 {ut.strftime('%I:%M %p, %d %b')}\n⏰ Auto")
        
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await context.bot.send_message(cid, f"✅ AUTO UNMUTED! {tn}")
            except: pass
        asyncio.create_task(auto())
    except: pass

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not target and context.args:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user
        except: return
    if not target: await update.message.reply_text("🔊 Reply /unmute"); return
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        await update.message.reply_text(f"✅ UNMUTED! {target.first_name}")
    except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE and is_allowed(uid):
        user_history[cid] = []
        await update.message.reply_text("💎 GARAM GAND AI — OPENROUTER!\n\n✅ Unlimited AI\n✅ No Daily Limit\n✅ Always Online\n\nKuch bhi puchho! 🔥")
    elif ct == ChatType.PRIVATE: await update.message.reply_text("🔒 Permission nahi!")
    else: user_history[cid] = []; await update.message.reply_text("👋 /activate!")

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ Bot ko Admin banao!"); return
    except: await update.message.reply_text("❌ Bot ko Admin banao!"); return
    active_groups[cid] = True; await update.message.reply_text("✅ ACTIVATED!")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False; await update.message.reply_text("🔴 Off!")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_history[update.effective_chat.id] = []; await update.message.reply_text("✅ Clear!")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    if msg.new_chat_members: await welcome(update, context); return
    if ct == ChatType.PRIVATE and not is_allowed(uid): await msg.reply_text("🔒 Permission nahi!"); return
    if ct != ChatType.PRIVATE and cid not in active_groups: return
    if not msg.text: return
    await context.bot.send_chat_action(chat_id=cid, action="typing")
    try:
        reply = get_ai_reply(msg.text, cid)
        if cid not in user_history: user_history[cid] = []
        user_history[cid].append({"role":"user","content":msg.text})
        user_history[cid].append({"role":"assistant","content":reply})
        user_history[cid] = user_history[cid][-15:]
        await msg.reply_text(reply)
    except: pass

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    for cmd, fn in [("start",start),("activate",activate),("deactivate",deactivate),("clear",clear),("mute",mute_user),("unmute",unmute_user),("adduser",adduser),("removeuser",removeuser),("userlist",userlist),("id",get_id)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(MessageHandler(filters.ALL,handle))
    print("💎 OPENROUTER READY!"); app.run_polling()

if __name__ == "__main__": main()
