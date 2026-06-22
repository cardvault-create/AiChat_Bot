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
    if days > 0: parts.append(f"*{days}* day{'s' if days!=1 else ''}")
    if hours > 0: parts.append(f"*{hours}* hour{'s' if hours!=1 else ''}")
    if mins > 0: parts.append(f"*{mins}* minute{'s' if mins!=1 else ''}")
    if secs > 0 and days == 0: parts.append(f"*{secs}* second{'s' if secs!=1 else ''}")
    return ", ".join(parts) if parts else "0 seconds"

def get_ai_reply(user_input, chat_id):
    if chat_id not in user_history: user_history[chat_id] = []
    
    messages = [{
        "role": "system",
        "content": """You are *GARAM GAND AI* — a PREMIUM, SMART, FUNNY assistant.

YOUR RULES:
• Give *COMPLETE* answers — never give half answers
• Use *bold* for IMPORTANT points (use ** around text)
• Use _italic_ for FUNNY parts (use _ around text)
• Use EMOJIS naturally 🔥💯😂👊💎⚡🎯❤️
• Reply in USER'S LANGUAGE
• Be DETAILED but readable
• For CODING: give WORKING code with explanation
• For KNOWLEDGE: give FULL facts
• For JOKES: give REAL funny jokes
• For ADVICE: give GENUINE help
• Make every reply PREMIUM quality
• Format with LINES and SECTIONS"""
    }]
    
    for msg in user_history[chat_id][-6:]:
        role = "user" if msg["role"]=="user" else "assistant"
        messages.append({"role":role,"content":msg["content"]})
    
    messages.append({"role":"user","content":user_input})
    
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {DEEPSEEK_API_KEY}","Content-Type":"application/json"},
            json={"model":"deepseek-chat","messages":messages,"temperature":0.85,"max_tokens":800},
            timeout=25
        )
        data = response.json()
        if "choices" in data: return data["choices"][0]["message"]["content"]
        err = data.get("error",{}).get("message","")
        if "Insufficient" in err: return "💰 *Balance Khatam!* Naya account banao ya $2 top-up karo.\n\n━━━━━━━━━━━━━━━━━━━━━━\n✨ _GARAM GAND AI_ ✨"
        return f"😅 {err[:60]}"
    except:
        return "😅 _Network issue! Fir se bol bhai!_ 💎"

def is_allowed(uid): return uid in allowed_users

# ================== OWNER PREMIUM COMMANDS ==================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS use kar sakta hai!* 👑", parse_mode="Markdown"); return
    if not context.args:
        await update.message.reply_text("📝 *Use:* `/adduser user_id`\n\n_User ID pata karne ke liye `/id` use karo_", parse_mode="Markdown"); return
    try:
        allowed_users.add(int(context.args[0]))
        await update.message.reply_text(f"✅ *User Added Successfully!*\n\n🆔 `{context.args[0]}`\n🔓 _Ab bot use kar sakta hai!_ 🎉", parse_mode="Markdown")
    except: await update.message.reply_text("❌ _Valid User ID do!_")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args:
        await update.message.reply_text("📝 *Use:* `/removeuser user_id`", parse_mode="Markdown"); return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: await update.message.reply_text("😎 *BOSS ko remove nahi kar sakte!* 👑", parse_mode="Markdown"); return
        allowed_users.discard(rid)
        await update.message.reply_text(f"✅ *User Removed!*\n\n🆔 `{rid}`\n🔒 _Ab bot use nahi kar sakta_", parse_mode="Markdown")
    except: await update.message.reply_text("❌ _Valid ID do!_")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    ul = "\n".join([f"• `{uid}` {'👑 BOSS' if uid==OWNER_USER_ID else '✅ Allowed'}" for uid in allowed_users])
    await update.message.reply_text(
        f"👥 *ALLOWED USERS LIST*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{ul}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 *Total Users:* {len(allowed_users)}\n\n"
        f"➕ `/adduser ID` — Add user\n"
        f"➖ `/removeuser ID` — Remove user",
        parse_mode="Markdown"
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args:
        await update.message.reply_text("📝 *Use:* `/broadcast your message`\n\n_Sab allowed users ko message bhejega!_", parse_mode="Markdown"); return
    msg = "📢 *BROADCAST FROM BOSS* 👑\n\n" + " ".join(context.args)
    sent = 0
    for uid in allowed_users:
        try: await context.bot.send_message(uid, msg, parse_mode="Markdown"); sent += 1
        except: pass
    await update.message.reply_text(f"✅ *Broadcast Sent!*\n\n📊 `{sent}/{len(allowed_users)}` _users ko bheja gaya!_", parse_mode="Markdown")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        await update.message.reply_text(
            f"👤 *User Info*\n\n"
            f"• *Name:* {t.first_name}\n"
            f"• *User ID:* `{t.id}`\n"
            f"• *Bot:* {'Yes 🤖' if t.is_bot else 'No 👤'}\n\n"
            f"_Is ID ko `/adduser` se allow kar sakte ho!_",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"🆔 *Your Info*\n\n"
            f"• *User ID:* `{update.effective_user.id}`\n"
            f"• *Chat ID:* `{update.effective_chat.id}`",
            parse_mode="Markdown"
        )

# ================== WELCOME ==================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for u in update.message.new_chat_members:
        if u.id == context.bot.id:
            await context.bot.send_message(cid,
                text="🤖 *GARAM GAND AI JOINED!* 💎\n\n"
                     "━━━━━━━━━━━━━━━━━━━━━━\n"
                     "👑 Admin `/activate` karo\n"
                     "📢 Phir sabko *PREMIUM REPLY* milega!\n"
                     "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                     "💻 *Coding* | 📚 *Knowledge* | 😂 *Fun*\n"
                     "🔇 *Mute System* | ⏰ *Auto Unmute*\n\n"
                     "🔥 _Bot ready — activate karo!_",
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(cid,
                text=f"✨ *WELCOME TO THE GROUP!* ✨\n\n"
                     f"━━━━━━━━━━━━━━━━━━━━━━\n"
                     f"👤 *{u.first_name}*\n"
                     f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                     f"🌟 _Aapka swagat hai!_ 🎉\n\n"
                     f"💎 *Yahaan milega:*\n"
                     f"   • *Premium AI Replies* 🔥\n"
                     f"   • *Coding Help* 💻\n"
                     f"   • *Knowledge* 📚\n"
                     f"   • *Mute System* 🔇\n\n"
                     f"📢 _Kuch bhi puchho — jawab milega!_ 💬\n\n"
                     f"🔰 _Enjoy karo!_ 🤗",
                parse_mode="Markdown"
            )

# ================== MUTE SYSTEM ==================

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ *Sirf Group mein chalta hai!*", parse_mode="Markdown"); return
    try:
        admins = await context.bot.get_chat_administrators(cid)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ *Sirf Group Admin mute kar sakta hai!* 👑", parse_mode="Markdown"); return
    except: await update.message.reply_text("❌ *Bot ko Admin banao pehle!*", parse_mode="Markdown"); return
    
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
            "📌 *Reply karke:*\n"
            "`/mute 10 second` | `/mute 5 minute`\n"
            "`/mute 2 hour` | `/mute 1 day`\n\n"
            "📌 *Short:* `25s` `5m` `2h` `1d` `30d`\n\n"
            "🇮🇳 IST | ⏰ Auto Unmute",
            parse_mode="Markdown"
        ); return
    
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
            f"⏰ *Auto Unmute ON* hai!\n"
            f"🔊 `/unmute` reply se manual unmute",
            parse_mode="Markdown"
        )
        
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await context.bot.send_message(cid,
                    text=f"✅ *AUTO UNMUTED!* 🇮🇳\n\n"
                         f"━━━━━━━━━━━━━━━━━━━━━━\n"
                         f"👤 *{tn}*\n"
                         f"⏱️ {format_time(mm)} ka mute khatam!\n"
                         f"━━━━━━━━━━━━━━━━━━━━━━\n"
                         f"💬 _Ab message kar sakta hai!_ 🎉",
                    parse_mode="Markdown"
                )
            except: pass
        asyncio.create_task(auto())
    except Exception as e:
        await update.message.reply_text(f"❌ *Mute fail!* Bot ko Ban Users permission do!\n`{str(e)[:50]}`", parse_mode="Markdown")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    target = None
    if update.message.reply_to_message: target = update.message.reply_to_message.from_user
    elif context.args:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user
        except: return
    else: await update.message.reply_text("🔊 *Reply karke `/unmute` bhejo!*", parse_mode="Markdown"); return
    if not target: return
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        nw = get_ist_now()
        await update.message.reply_text(
            f"✅ *UNMUTED!* 🇮🇳\n\n"
            f"👤 *{target.first_name}*\n"
            f"🔓 `{nw.strftime('%I:%M:%S %p, %d %B %Y')}`\n\n"
            f"💬 _Ab message kar sakta hai!_ 🎉",
            parse_mode="Markdown"
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
                "✅ *DeepSeek V3 AI* (Best Quality)\n"
                "✅ *Premium Bold/Italic Text*\n"
                "✅ *Coding Help* 💻\n"
                "✅ *Knowledge* 📚\n"
                "✅ *Fun & Jokes* 😂\n"
                "✅ *Mute System* 🔇\n"
                "✅ *Auto Unmute* ⏰\n"
                "✅ *User Management* 👥\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚡ *OWNER COMMANDS:*\n"
                "/start — Restart bot\n"
                "/clear — Clear memory\n"
                "/id — Get user ID\n"
                "/adduser — Add user\n"
                "/removeuser — Remove user\n"
                "/userlist — View all users\n"
                "/broadcast — Message all users\n\n"
                "_Bolo boss! Kya chahiye?_ 🔥",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🔒 *PERMISSION DENIED!*\n\n"
                "_Aapke paas bot use karne ki permission nahi hai!_\n"
                "_Owner se contact karein._",
                parse_mode="Markdown"
            )
    else:
        user_history[cid] = []
        await update.message.reply_text(
            "👋 *GARAM GAND AI READY!* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 Admin `/activate` karo\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔇 `/mute` | 🔊 `/unmute` | 🆔 `/id`\n\n"
            "_Activate karo, phir enjoy karo!_ 🔥",
            parse_mode="Markdown"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ *Sirf GROUP mein!*", parse_mode="Markdown"); return
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
                "━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode="Markdown"
            ); return
    except: await update.message.reply_text("❌ *Bot ko Admin banao!*", parse_mode="Markdown"); return
    
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text(
        "✅ *GROUP ACTIVATED!* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *AB SAB ON:* 💬 AI | 🔇 Mute | ⏰ Auto | 👋 Welcome\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "❌ /deactivate — Band karo",
        parse_mode="Markdown"
    )

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *OFF!* `/activate` se on karo", parse_mode="Markdown")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_history[update.effective_chat.id] = []
    await update.message.reply_text("✅ *Memory Clear!* 💭", parse_mode="Markdown")

# ================== MESSAGE HANDLER ==================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    
    if msg.new_chat_members: await welcome(update, context); return
    if ct == ChatType.PRIVATE and not is_allowed(uid): await msg.reply_text("🔒 *Permission nahi hai!*", parse_mode="Markdown"); return
    if ct != ChatType.PRIVATE and cid not in active_groups: return
    if not msg.text: return
    
    await context.bot.send_chat_action(chat_id=cid, action="typing")
    
    try:
        reply = get_ai_reply(msg.text, cid)
        if cid not in user_history: user_history[cid] = []
        user_history[cid].append({"role":"user","content":msg.text})
        user_history[cid].append({"role":"assistant","content":reply})
        user_history[cid] = user_history[cid][-15:]
        await msg.reply_text(reply, parse_mode="Markdown")
    except:
        await msg.reply_text("😅 _Fir se try karo!_ 💎")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("mutelist", lambda u,c: u.message.reply_text(
        "🔇 *MUTE HELP* 🇮🇳\n\n"
        "`/mute 10s` `5m` `2h` `1d` `30d`\n"
        "🔊 `/unmute` reply | ⏰ Auto",
        parse_mode="Markdown"
    )))
    app.add_handler(CommandHandler("adduser", adduser))
    app.add_handler(CommandHandler("removeuser", removeuser))
    app.add_handler(CommandHandler("userlist", userlist))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(MessageHandler(filters.ALL, handle))
    print("💎 GARAM GAND AI — ULTIMATE PREMIUM")
    print("✅ DeepSeek V3 | Bold/Italic | All Features")
    app.run_polling()

if __name__ == "__main__": main()
