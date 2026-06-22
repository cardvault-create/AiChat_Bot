import os
import asyncio
import requests
import pytz
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== KEYS ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
# ==========================================

# ================== OWNER SETUP ==================
OWNER_USER_ID = 7614459746
# =================================================

IST = pytz.timezone('Asia/Kolkata')
user_history = {}
active_groups = {}
allowed_users = {7614459746}

def get_ist_now():
    return datetime.now(IST)

def parse_time(time_str):
    time_str = time_str.lower().strip().replace(" ", "")
    if not time_str: return None
    if 'seconds' in time_str or time_str.endswith('second') or time_str.endswith('sec'):
        num = time_str.replace('seconds','').replace('second','').replace('sec','')
        return float(num)/60 if num else None
    elif 'minutes' in time_str or time_str.endswith('minute') or time_str.endswith('mins') or time_str.endswith('min'):
        num = time_str.replace('minutes','').replace('minute','').replace('mins','').replace('min','')
        return float(num) if num else None
    elif 'hours' in time_str or time_str.endswith('hour') or time_str.endswith('hrs') or time_str.endswith('hr'):
        num = time_str.replace('hours','').replace('hour','').replace('hrs','').replace('hr','')
        return float(num)*60 if num else None
    elif 'days' in time_str or time_str.endswith('day'):
        num = time_str.replace('days','').replace('day','')
        return float(num)*1440 if num else None
    elif time_str.endswith('s'): return float(time_str[:-1])/60
    elif time_str.endswith('m'): return float(time_str[:-1])
    elif time_str.endswith('h'): return float(time_str[:-1])*60
    elif time_str.endswith('d'): return float(time_str[:-1])*1440
    else:
        try: return float(time_str)
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
    """Free ChatGPT API — no key needed!"""
    if chat_id not in user_history: user_history[chat_id] = []
    
    # Build conversation
    messages = [
        {"role": "system", "content": "You are GARAM GAND AI, a friendly helpful assistant. Reply in user's language. Give accurate answers. Use emojis. Be natural and helpful."}
    ]
    
    for msg in user_history[chat_id][-4:]:
        role = "user" if msg["role"]=="user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
    
    messages.append({"role": "user", "content": user_input})
    
    # Try multiple free APIs
    return try_chatgpt_free(messages) or try_duckduckgo(messages) or "😅 Sab AI busy hain! 2 sec mein fir try karo 🙏"

def try_chatgpt_free(messages):
    """Try free ChatGPT API"""
    try:
        # Use free endpoint
        response = requests.post(
            "https://chatgpt-api.shn.hk/v1/",
            json={
                "messages": messages,
                "model": "gpt-3.5-turbo"
            },
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content")
        return None
    except:
        return None

def try_duckduckgo(messages):
    """Try DuckDuckGo AI chat"""
    try:
        # Get last user message
        user_msg = messages[-1]["content"] if messages else ""
        
        response = requests.post(
            "https://duckduckgo.com/duckchat/v1/chat",
            headers={
                "Content-Type": "application/json",
                "x-vqd-accept": "1"
            },
            json={
                "model": "gpt-3.5-turbo-0125",
                "messages": messages
            },
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("message", "")
        return None
    except:
        return None

def is_allowed(uid): return uid in allowed_users

# ================== PERMISSION ==================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ Sirf BOSS!"); return
    if not context.args: await update.message.reply_text("📝 /adduser user_id\n🆔 /id se ID pata karo"); return
    try: allowed_users.add(int(context.args[0])); await update.message.reply_text(f"✅ User {context.args[0]} added!")
    except: await update.message.reply_text("❌ Valid ID do!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ Sirf BOSS!"); return
    if not context.args: await update.message.reply_text("📝 /removeuser user_id"); return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: await update.message.reply_text("😎 BOSS ko nahi!"); return
        allowed_users.discard(rid); await update.message.reply_text(f"✅ User {rid} removed!")
    except: await update.message.reply_text("❌ Valid ID do!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ Sirf BOSS!"); return
    ul = "\n".join([f"• `{uid}` {'👑' if uid==OWNER_USER_ID else '✅'}" for uid in allowed_users])
    await update.message.reply_text(f"👥 Allowed Users:\n\n{ul}\n\nTotal: {len(allowed_users)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ Sirf BOSS!"); return
    if not context.args: await update.message.reply_text("📝 /broadcast message"); return
    msg = "📢 Broadcast from BOSS 👑\n\n" + " ".join(context.args)
    s = 0
    for uid in allowed_users:
        try: await context.bot.send_message(uid, msg); s += 1
        except: pass
    await update.message.reply_text(f"✅ {s}/{len(allowed_users)} users ko bheja!")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        await update.message.reply_text(f"👤 {t.first_name}\n🆔 `{t.id}`")
    else: await update.message.reply_text(f"🆔 Your ID: `{update.effective_user.id}`")

# ================== WELCOME ==================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for u in update.message.new_chat_members:
        if u.id == context.bot.id:
            await context.bot.send_message(cid, text="🤖 GARAM GAND AI JOINED!\n\n👑 /activate karo\n📢 Premium Reply Milega!\n💻 Coding | 📚 Knowledge | 😂 Fun")
        else:
            await context.bot.send_message(cid, text=f"✨ Welcome {u.first_name}! 🎉\n💎 AI Replies | 🔇 Mute | ⚡ Fast")

# ================== MUTE ==================

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ Sirf group!"); return
    try:
        admins = await context.bot.get_chat_administrators(cid)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ Sirf Admin!"); return
    except: await update.message.reply_text("❌ Bot ko Admin banao!"); return
    
    target, ts = None, "1h"
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if context.args: ts = " ".join(context.args)
    elif context.args and len(context.args)>=2:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user; ts = " ".join(context.args[1:])
        except: return
    else: await update.message.reply_text("🔇 /mute 10s 5m 2h 1d 30d\nReply karke! 🇮🇳 ⏰ Auto"); return
    
    if not target or target.id==update.effective_user.id or target.is_bot: return
    mm = parse_time(ts)
    if not mm or mm>43200 or mm<=0: return
    
    nw, ut = get_ist_now(), get_ist_now()+timedelta(minutes=mm)
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
            permissions=ChatPermissions(can_send_messages=False,can_send_audios=False,can_send_documents=False,can_send_photos=False,can_send_videos=False,can_send_video_notes=False,can_send_voice_notes=False,can_send_polls=False,can_send_other_messages=False,can_add_web_page_previews=False,can_change_info=False,can_invite_users=False,can_pin_messages=False),
            until_date=ut)
        
        tn = target.first_name or "User"
        if target.last_name: tn += f" {target.last_name}"
        an = update.effective_user.first_name or "Admin"
        
        await update.message.reply_text(
            f"🔇 MUTED! 🇮🇳\n\n"
            f"👤 {tn}\n👑 {an}\n⏱️ {format_time(mm)}\n\n"
            f"📅 {nw.strftime('%I:%M %p, %d %b')}\n"
            f"🔓 {ut.strftime('%I:%M %p, %d %b')}\n\n"
            f"⏰ Auto Unmute ON"
        )
        
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await context.bot.send_message(cid, text=f"✅ AUTO UNMUTED! {tn} 🎉")
            except: pass
        asyncio.create_task(auto())
    except: pass

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    target = None
    if update.message.reply_to_message: target = update.message.reply_to_message.from_user
    elif context.args:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user
        except: return
    else: await update.message.reply_text("🔊 Reply karke /unmute"); return
    if not target: return
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        await update.message.reply_text(f"✅ UNMUTED! {target.first_name} 🎉")
    except: pass

# ================== COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    
    if ct == ChatType.PRIVATE:
        if is_allowed(uid):
            user_history[cid] = []
            await update.message.reply_text(
                "💎 GARAM GAND AI — FREE & PREMIUM!\n\n"
                "✅ ChatGPT Level AI\n"
                "✅ 100% FREE\n"
                "✅ No API Key\n"
                "✅ Coding 💻\n"
                "✅ Knowledge 📚\n"
                "✅ Fun 😂\n\n"
                "👑 Owner Commands:\n"
                "/adduser | /removeuser | /userlist\n"
                "/broadcast | /id\n\n"
                "Kuch bhi puchho! 🔥"
            )
        else: await update.message.reply_text("🔒 Permission nahi hai!")
    else: user_history[cid] = []; await update.message.reply_text("👋 Ready! Admin /activate karo")

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        admins = await context.bot.get_chat_administrators(cid)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ Admin only! Bot ko Admin banao phir /activate"); return
    except: await update.message.reply_text("❌ Bot ko Admin banao!"); return
    active_groups[cid] = True; await update.message.reply_text("✅ ACTIVATED! 🔥\n💻 Coding | 📚 Knowledge | 😂 Fun\n❌ /deactivate")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False; await update.message.reply_text("🔴 Off! /activate")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_history[update.effective_chat.id] = []; await update.message.reply_text("✅ Clear!")

# ================== HANDLER ==================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    
    if msg.new_chat_members: await welcome(update, context); return
    if ct == ChatType.PRIVATE and not is_allowed(uid): await update.message.reply_text("🔒 Permission nahi!"); return
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
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("mutelist", lambda u,c: u.message.reply_text("🔇 /mute 10s 5m 2h 1d 30d\n🔊 /unmute | ⏰ Auto")))
    app.add_handler(CommandHandler("adduser", adduser))
    app.add_handler(CommandHandler("removeuser", removeuser))
    app.add_handler(CommandHandler("userlist", userlist))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(MessageHandler(filters.ALL, handle))
    print("💎 GARAM GAND AI — FREE & WORKING!")
    print("✅ No API Key | 100% Free | Always Online")
    app.run_polling()

if __name__ == "__main__": main()
