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
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
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
    if chat_id not in user_history: user_history[chat_id] = []
    
    system_prompt = """You are GARAM GAND AI - a PREMIUM, SMART, FRIENDLY and FUNNY AI Assistant.

YOUR STYLE:
• Reply in user's language (Hindi, English, Hinglish - whatever user uses)
• Be DETAILED but not too long - give COMPLETE answers
• Use EMOJIS naturally to make replies lively 🔥💯😂👊💎⚡🎯❤️✨
• Be FRIENDLY like talking to a best friend
• Be FUNNY when appropriate - add humor naturally
• Be ACCURATE - give correct information always
• For CODING questions - give WORKING CODE with short explanation
• For KNOWLEDGE questions - give accurate facts
• For JOKES - give real funny jokes
• For SHAYARI - write original shayari
• For ADVICE - give genuine helpful advice
• For EMOTIONAL messages - show empathy and care
• Keep replies CLEAN and READABLE
• Make every reply MEMORABLE and VALUABLE"""

    messages = [{"role":"system","content":system_prompt}]
    
    for msg in user_history[chat_id][-6:]:
        role = "user" if msg["role"]=="user" else "assistant"
        messages.append({"role":role,"content":msg["content"]})
    
    messages.append({"role":"user","content":user_input})
    
    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {DEEPSEEK_API_KEY}","Content-Type":"application/json"},
            json={"model":"deepseek-chat","messages":messages,"temperature":0.85,"max_tokens":600},
            timeout=30)
        data = r.json()
        if "choices" in data: return data["choices"][0]["message"]["content"]
        err = data.get("error",{}).get("message","")
        if "Insufficient" in err: return "💰 Balance khatam! Top-up karo."
        return f"😅 Error: {err[:50]}"
    except: return "😅 Network issue! Fir se bol bhai!"

def is_allowed(uid): return uid in allowed_users

# ================== OWNER PREMIUM COMMANDS ==================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ Yeh command sirf BOSS use kar sakta hai! 👑")
        return
    if not context.args:
        await update.message.reply_text("📝 Use: /adduser user_id\n\nUser ID pata karne ke liye kisi message pe reply karke /id bhejo")
        return
    try:
        allowed_users.add(int(context.args[0]))
        await update.message.reply_text(f"✅ User Added Successfully!\n\n🆔 {context.args[0]}\n🔓 Ab bot use kar sakta hai!")
    except: await update.message.reply_text("❌ Valid User ID do!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ Yeh command sirf BOSS use kar sakta hai! 👑")
        return
    if not context.args:
        await update.message.reply_text("📝 Use: /removeuser user_id")
        return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID:
            await update.message.reply_text("😎 BOSS ko remove nahi kar sakte! Aap to MALIK ho!")
            return
        allowed_users.discard(rid)
        await update.message.reply_text(f"✅ User Removed!\n\n🆔 {rid}\n🔒 Ab bot use nahi kar sakta!")
    except: await update.message.reply_text("❌ Valid User ID do!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ Sirf BOSS dekh sakta hai! 👑")
        return
    ul = "\n".join([f"• `{uid}` {'👑 BOSS' if uid==OWNER_USER_ID else '✅'}" for uid in allowed_users])
    await update.message.reply_text(
        f"👥 *ALLOWED USERS LIST*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{ul}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 Total Users: *{len(allowed_users)}*\n\n"
        f"➕ /adduser ID — Naya user add karo\n"
        f"➖ /removeuser ID — User remove karo"
    )

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        await update.message.reply_text(
            f"👤 *User Info*\n\n"
            f"• Name: {t.first_name}\n"
            f"• User ID: `{t.id}`\n"
            f"• Bot: {'Yes 🤖' if t.is_bot else 'No 👤'}"
        )
    else:
        await update.message.reply_text(
            f"🆔 *Your Info*\n\n"
            f"• Your ID: `{update.effective_user.id}`\n"
            f"• Chat ID: `{update.effective_chat.id}`"
        )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner sab allowed users ko message bhej sakta hai"""
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ Sirf BOSS! 👑")
        return
    if not context.args:
        await update.message.reply_text("📝 Use: /broadcast your message here\n\nSab allowed users ko message bhejega!")
        return
    
    msg = "📢 *BROADCAST FROM BOSS* 👑\n\n" + " ".join(context.args)
    sent = 0
    for uid in allowed_users:
        try:
            await context.bot.send_message(uid, msg)
            sent += 1
        except: pass
    
    await update.message.reply_text(f"✅ Broadcast Sent!\n\n📊 {sent}/{len(allowed_users)} users ko bheja!")

# ================== WELCOME ==================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for u in update.message.new_chat_members:
        if u.id == context.bot.id:
            await context.bot.send_message(cid, text=
                "🤖 *GARAM GAND AI JOINED!* 💎\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "👑 Admin `/activate` karo\n"
                "📢 Phir sabko PREMIUM reply milega!\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💻 Coding | 📚 Knowledge | 😂 Fun\n"
                "🔇 Mute System | ⏰ Auto Unmute\n\n"
                "🔥 _Bot ready — activate karo!_"
            )
        else:
            await context.bot.send_message(cid, text=
                f"✨ *WELCOME!* ✨\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *{u.first_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌟 _Aapka swagat hai!_ 🎉\n\n"
                f"💎 *Yahaan milega:*\n"
                f"• Premium AI Replies 🔥\n"
                f"• Coding Help 💻\n"
                f"• Knowledge 📚\n"
                f"• Mute System 🔇\n\n"
                f"📢 Kuch bhi puchho — jawab milega! 💬\n\n"
                f"🔰 _Enjoy karo!_ 🤗"
            )

# ================== MUTE ==================

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; aid = update.effective_user.id
    if ct == ChatType.PRIVATE: await update.message.reply_text("⚡ Sirf group mein chalta hai!"); return
    try:
        admins = await context.bot.get_chat_administrators(cid)
        if aid not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ Sirf Group Admin mute kar sakta hai! 👑"); return
    except: await update.message.reply_text("❌ Bot ko Admin banao pehle!"); return
    
    target, ts = None, "1h"
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if context.args: ts = " ".join(context.args)
    elif context.args and len(context.args)>=2:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user; ts = " ".join(context.args[1:])
        except: return
    else:
        await update.message.reply_text(
            "🔇 *MUTE USAGE* 🇮🇳\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📌 Reply karke:\n"
            "`/mute 10 second` | `/mute 5 minute`\n"
            "`/mute 2 hour` | `/mute 1 day`\n\n"
            "📌 Short: `25s` `5m` `2h` `1d` `30d`\n\n"
            "🇮🇳 IST | ⏰ Auto Unmute"
        ); return
    
    if not target or target.id==aid or target.is_bot: return
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
            f"🔇 *MUTED! — INDIA TIME* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {tn}\n"
            f"🆔 ID: `{target.id}`\n"
            f"👑 *Muted by:* {an}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ *Duration:* {format_time(mm)}\n\n"
            f"📅 *Muted at:*\n"
            f"   🕐 `{nw.strftime('%I:%M:%S %p')}` — {nw.strftime('%d %B %Y')}\n\n"
            f"🔓 *Unmute at:*\n"
            f"   🕐 `{ut.strftime('%I:%M:%S %p')}` — {ut.strftime('%d %B %Y')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ Auto Unmute ON hai!\n"
            f"🔊 `/unmute` reply se manual unmute"
        )
        
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await context.bot.send_message(cid, text=
                    f"✅ *AUTO UNMUTED!* 🇮🇳\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 *{tn}*\n"
                    f"⏱️ {format_time(mm)} ka mute khatam!\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💬 _Ab message kar sakta hai!_ 🎉"
                )
            except: pass
        asyncio.create_task(auto())
    except Exception as e:
        await update.message.reply_text(f"❌ Mute fail! Bot ko Ban Users permission do!\n`{str(e)[:50]}`")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    target = None
    if update.message.reply_to_message: target = update.message.reply_to_message.from_user
    elif context.args:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user
        except: return
    else: await update.message.reply_text("🔊 Reply karke `/unmute` bhejo!"); return
    if not target: return
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        nw = get_ist_now()
        await update.message.reply_text(
            f"✅ *UNMUTED!* 🇮🇳\n\n"
            f"👤 *{target.first_name}*\n"
            f"🔓 `{nw.strftime('%I:%M:%S %p, %d %B %Y')}`\n\n"
            f"💬 _Ab message kar sakta hai!_ 🎉"
        )
    except: pass

# ================== COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    
    if ct == ChatType.PRIVATE:
        if is_allowed(uid):
            user_history[cid] = []
            await update.message.reply_text(
                "💎 *GARAM GAND AI — PREMIUM MODE* 💎\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔥 *SYSTEMS ACTIVE:*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ *DeepSeek AI* (GPT-4 Level)\n"
                "✅ *Premium Text Replies*\n"
                "✅ *Coding Help* 💻\n"
                "✅ *Knowledge* 📚\n"
                "✅ *Fun & Jokes* 😂\n"
                "✅ *Mute System* 🔇\n"
                "✅ *Auto Unmute* ⏰\n"
                "✅ *User Management* 👥\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚡ *COMMANDS:*\n"
                "/start — Restart bot\n"
                "/clear — Clear memory\n"
                "/id — Get user ID\n"
                "/adduser — Add user\n"
                "/removeuser — Remove user\n"
                "/userlist — View users\n"
                "/broadcast — Message all users\n\n"
                "_Bolo boss! Kya chahiye?_ 🔥"
            )
        else:
            await update.message.reply_text(
                "🔒 *PERMISSION DENIED!*\n\n"
                "Aapke paas bot use karne ki permission nahi hai!\n"
                "Owner se contact karein."
            )
    else:
        user_history[cid] = []
        await update.message.reply_text(
            "👋 *GARAM GAND AI READY!* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 Admin `/activate` karo\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔇 `/mute` | 🔊 `/unmute` | 🆔 `/id`\n\n"
            "_Activate karo, phir enjoy karo!_ 🔥"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ Sirf GROUP mein!"); return
    try:
        admins = await context.bot.get_chat_administrators(cid)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text(
                "❌ *ADMIN ONLY!*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 STEPS:\n"
                "1️⃣ Bot ko ADMIN banao\n"
                "2️⃣ Sab permissions ON karo\n"
                "3️⃣ Phir `/activate` bhejo\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ); return
    except: await update.message.reply_text("❌ Bot ko Admin banao!"); return
    
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text(
        "✅ *GROUP ACTIVATED!* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *AB SAB ON:* 💬 AI | 🔇 Mute | ⏰ Auto | 👋 Welcome\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "❌ /deactivate — Band karo"
    )

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *OFF!* /activate se on karo")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_history[update.effective_chat.id] = []
    await update.message.reply_text("✅ Memory Clear! 💭")

# ================== HANDLER ==================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    
    if msg.new_chat_members: await welcome(update, context); return
    if ct == ChatType.PRIVATE and not is_allowed(uid): await update.message.reply_text("🔒 Permission nahi hai!"); return
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
    print("💎 GARAM GAND AI — DEEPSEEK PREMIUM")
    print(f"👑 Owner: {OWNER_USER_ID}")
    app.run_polling()

if __name__ == "__main__": main()
