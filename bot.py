import os
import asyncio
import cohere
import pytz
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== KEYS ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
# ==========================================

# ================== OWNER SETUP ==================
OWNER_USER_ID = 7614459746
# =================================================

co = cohere.Client(COHERE_API_KEY)
IST = pytz.timezone('Asia/Kolkata')

user_history = {}
active_groups = {}
allowed_users = {7614459746}  # Owner always allowed

PREMIUM_PREAMBLE = """Tu *GARAM GAND AI Bot* hai — ek *SUPER PREMIUM AI Assistant*.

*TERI PERSONALITY:*
• *Mast*, *funny*, *intelligent*, aur *KNOWLEDGEABLE*
• Har TEXT sawal ka *DETAILED* aur *ACCURATE* jawab de
• *Bold* kar important points (use ** for bold)
• _Italic_ kar emphasis aur funny parts (use _ for italic)
• Emojis use kar har line mein: 🔥💯😂👊💎⚡🎯❤️✨🤣😎🙏🌟
• User ki LANGUAGE mein jawab de
• *NATURAL* baat kar — *SMART DOST* ki tarah
• *POORA JAWAB DE* — jitna sawaal utna jawab
• Kabhi adha jawab mat dena — *FULL COMPLETE REPLY*

*TERI SPECIALITIES:*
• 💻 *CODING:* Working code with full explanation
• 📚 *KNOWLEDGE:* Science, History, Tech, GK — sab
• 😂 *FUN:* Real funny jokes, shayari, entertainment
• 💡 *ADVICE:* Genuine helpful advice
• 🎯 *ACCURACY:* 100% correct information

*TERA REPLY FORMAT:*
• *Bold* = Important words, headings, key points
• _Italic_ = Funny parts, side comments, emphasis
• Emojis = Har 2-3 line mein
• Lines & dividers = Sections separate karne ke liye
• Har reply *PREMIUM* lagna chahiye"""

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
    if days > 0: parts.append(f"*{days}* day{'s' if days!=1 else ''}")
    if hours > 0: parts.append(f"*{hours}* hour{'s' if hours!=1 else ''}")
    if mins > 0: parts.append(f"*{mins}* minute{'s' if mins!=1 else ''}")
    if secs > 0 and days == 0: parts.append(f"*{secs}* second{'s' if secs!=1 else ''}")
    return ", ".join(parts) if parts else "0 seconds"

def is_user_allowed(user_id):
    return user_id in allowed_users

def get_premium_reply(user_input, chat_id):
    if chat_id not in user_history: user_history[chat_id] = []
    history = user_history[chat_id]
    chat_history = []
    for msg in history[-6:]:
        role = "USER" if msg["role"]=="user" else "CHATBOT"
        chat_history.append({"role":role,"message":msg["content"]})
    try:
        response = co.chat(
            message=user_input,
            chat_history=chat_history,
            preamble=PREMIUM_PREAMBLE,
            temperature=0.9,
            max_tokens=1000
        )
        return response.text
    except:
        return "_😅 Fir se bol bhai!_ 💎\n\n━━━━━━━━━━━━━━━━━━━━━━\n✨ _GARAM GAND AI_ ✨"

# ================== PERMISSION SYSTEM ==================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner naye user ko bot use karne ki permission de"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 *ADD USER USAGE:*\n\n"
            "`/adduser user_id`\n"
            "`/adduser 123456789`\n\n"
            "User ID pata karne ke liye:\n"
            "Group mein `/id` bhejo ya @userinfobot use karo",
            parse_mode="Markdown"
        )
        return
    
    try:
        new_user_id = int(context.args[0])
        if new_user_id in allowed_users:
            await update.message.reply_text(f"⚠️ User `{new_user_id}` already allowed hai!")
            return
        
        allowed_users.add(new_user_id)
        await update.message.reply_text(f"✅ *User Added!*\n\n🆔 `{new_user_id}`\n🔓 _Ab bot use kar sakta hai!_ 🎉", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Valid User ID do!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner user ki permission remove kare"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 *REMOVE USER USAGE:*\n\n"
            "`/removeuser user_id`\n"
            "`/removeuser 123456789`",
            parse_mode="Markdown"
        )
        return
    
    try:
        remove_id = int(context.args[0])
        if remove_id == OWNER_USER_ID:
            await update.message.reply_text("😎 *BOSS ko nahi hataya ja sakta!* 👑", parse_mode="Markdown")
            return
        
        if remove_id not in allowed_users:
            await update.message.reply_text(f"⚠️ User `{remove_id}` allowed list mein nahi hai!")
            return
        
        allowed_users.discard(remove_id)
        await update.message.reply_text(f"✅ *User Removed!*\n\n🆔 `{remove_id}`\n🔒 _Ab bot use nahi kar sakta_", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Valid User ID do!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allowed users ki list dikhao"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown")
        return
    
    user_list = "\n".join([f"• `{uid}` {'👑 Owner' if uid==OWNER_USER_ID else ''}" for uid in allowed_users])
    await update.message.reply_text(
        f"👥 *ALLOWED USERS:*\n\n"
        f"{user_list}\n\n"
        f"📊 *Total:* {len(allowed_users)} users\n\n"
        f"➕ Add: `/adduser ID`\n"
        f"➖ Remove: `/removeuser ID`",
        parse_mode="Markdown"
    )

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ki ID bataye"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        await update.message.reply_text(
            f"👤 *User Info:*\n\n"
            f"• Name: *{target_user.first_name}*\n"
            f"• User ID: `{target_user.id}`\n"
            f"• Is Bot: {target_user.is_bot}\n\n"
            f"📝 Chat ID: `{chat_id}`\n\n"
            f"_Is ID ko `/adduser` se allow kar sakte ho!_",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"📝 *Your Info:*\n\n"
            f"• Your ID: `{user_id}`\n"
            f"• Chat ID: `{chat_id}`\n"
            f"• Chat Type: {chat_type}",
            parse_mode="Markdown"
        )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner sab allowed users ko message bhej sakta hai"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("📝 *BROADCAST:* `/broadcast your message`\n\n_Sab allowed users ko message bhejega!_", parse_mode="Markdown")
        return
    
    msg = "📢 *BROADCAST FROM BOSS* 👑\n\n" + " ".join(context.args)
    sent = 0
    for uid in allowed_users:
        try:
            await context.bot.send_message(uid, msg, parse_mode="Markdown")
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ *Broadcast Sent!*\n\n📊 `{sent}/{len(allowed_users)}` _users ko bheja gaya!_", parse_mode="Markdown")

# ================== WELCOME SYSTEM ==================

async def welcome_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members:
        return
    
    chat_id = update.effective_chat.id
    
    for new_user in update.message.new_chat_members:
        if new_user.id == context.bot.id:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🤖 *GARAM GAND AI JOINED!* 💎\n\n"
                     "━━━━━━━━━━━━━━━━━━━━━━\n"
                     "👑 Admin `/activate` karo\n"
                     "📢 Phir sabko *PREMIUM REPLY* milega!\n"
                     "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                     "💻 *Coding* | 📚 *Knowledge* | 😂 *Fun*\n"
                     "🔇 *Mute System* | ⏰ *Auto Unmute*\n"
                     "👥 `/id` — User ID pata karo\n\n"
                     "🔥 _Bot ready — activate karo!_",
                parse_mode="Markdown"
            )
            continue
        
        user_name = new_user.first_name or "User"
        if new_user.last_name:
            user_name += f" {new_user.last_name}"
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✨ *WELCOME TO THE GROUP!* ✨\n\n"
                 f"━━━━━━━━━━━━━━━━━━━━━━\n"
                 f"👤 *{user_name}*\n"
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
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ *Sirf GROUP mein chalta hai!*", parse_mode="Markdown")
        return
    
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if admin_id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ *Sirf GROUP ADMIN!* 👑", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *Bot ko ADMIN banao!*", parse_mode="Markdown")
        return
    
    target_user = None
    time_str = "1h"
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        if context.args:
            time_str = " ".join(context.args)
    elif context.args and len(context.args) >= 2:
        try:
            target_id = int(context.args[0])
            target_user = (await context.bot.get_chat_member(chat_id, target_id)).user
            time_str = " ".join(context.args[1:])
        except:
            await update.message.reply_text("❌ User ID galat!")
            return
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
        )
        return
    
    if not target_user or target_user.id == admin_id or target_user.is_bot:
        return
    
    mute_minutes = parse_time(time_str)
    if mute_minutes is None or mute_minutes > 43200 or mute_minutes <= 0:
        return
    
    now_ist = get_ist_now()
    until_ist = now_ist + timedelta(minutes=mute_minutes)
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=False, can_send_audios=False, can_send_documents=False,
                can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
                can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
                can_add_web_page_previews=False, can_change_info=False,
                can_invite_users=False, can_pin_messages=False
            ),
            until_date=until_ist
        )
        
        target_name = target_user.first_name or "User"
        if target_user.last_name: target_name += f" {target_user.last_name}"
        admin_name = update.effective_user.first_name or "Admin"
        
        await update.message.reply_text(
            f"🔇 *MUTED! — INDIA TIME* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {target_name}\n"
            f"🆔 ID: `{target_user.id}`\n"
            f"👑 *Muted by:* {admin_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ *Duration:* {format_time(mute_minutes)}\n\n"
            f"📅 *Muted at:*\n"
            f"   🕐 `{now_ist.strftime('%I:%M:%S %p')}`\n"
            f"   📆 {now_ist.strftime('%d %B %Y')}\n\n"
            f"🔓 *Unmute at:*\n"
            f"   🕐 `{until_ist.strftime('%I:%M:%S %p')}`\n"
            f"   📆 {until_ist.strftime('%d %B %Y')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ Time khatam hone par *AUTO UNMUTE* hoga!\n"
            f"🔊 Ya `/unmute` reply karke manual unmute",
            parse_mode="Markdown"
        )
        
        async def auto_unmute():
            await asyncio.sleep(mute_minutes * 60)
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat_id, user_id=target_user.id,
                    permissions=ChatPermissions(
                        can_send_messages=True, can_send_audios=True, can_send_documents=True,
                        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                        can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                        can_add_web_page_previews=True, can_change_info=False,
                        can_invite_users=False, can_pin_messages=False
                    )
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ *AUTO UNMUTED!* 🇮🇳\n\n"
                         f"━━━━━━━━━━━━━━━━━━━━━━\n"
                         f"👤 *{target_name}*\n"
                         f"⏱️ {format_time(mute_minutes)} ka mute khatam!\n"
                         f"━━━━━━━━━━━━━━━━━━━━━━\n"
                         f"💬 _Ab message kar sakta hai!_ 🎉",
                    parse_mode="Markdown"
                )
            except:
                pass
        
        asyncio.create_task(auto_unmute())
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Mute fail!*\n\n"
            f"⚠️ Bot ko yeh permissions do:\n"
            f"✅ Ban Users ✅ Delete Messages\n\n"
            f"Error: `{str(e)[:80]}`",
            parse_mode="Markdown"
        )

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP* mein!", parse_mode="Markdown")
        return
    
    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        try:
            target_user = (await context.bot.get_chat_member(chat_id, int(context.args[0]))).user
        except:
            return
    else:
        await update.message.reply_text("🔊 Reply karke `/unmute` bhejo", parse_mode="Markdown")
        return
    
    if not target_user:
        return
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id, user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True, can_send_audios=True, can_send_documents=True,
                can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                can_add_web_page_previews=True, can_change_info=False,
                can_invite_users=False, can_pin_messages=False
            )
        )
        now_ist = get_ist_now()
        await update.message.reply_text(
            f"✅ *UNMUTED!* 🇮🇳\n\n"
            f"👤 *User:* {target_user.first_name}\n"
            f"🔓 *At:* `{now_ist.strftime('%I:%M:%S %p, %d %B %Y')}`\n\n"
            f"💬 _Ab message kar sakta hai!_ 🎉",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Unmute fail: `{str(e)[:80]}`")

async def mutelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔇 *MUTE HELP* 🇮🇳\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *MUTE (reply karke):*\n"
        "`/mute 10 second` | `25s`\n"
        "`/mute 5 minute` | `5m`\n"
        "`/mute 2 hour` | `2h`\n"
        "`/mute 1 day` | `1d`\n"
        "`/mute 30d` (max)\n\n"
        "📌 *UNMUTE:* `/unmute` reply\n"
        "📌 *Manual:* `/mute ID time`\n\n"
        "⏰ *Auto Unmute* ON\n"
        "👑 Admin only | 🇮🇳 IST Time",
        parse_mode="Markdown"
    )

# ================== COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        if user_id == OWNER_USER_ID:
            user_history[chat_id] = []
            await update.message.reply_text(
                "💎 *WELCOME BACK BOSS!* 💎\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔥 *PREMIUM SYSTEMS ACTIVE:*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ *Premium AI Replies* (Bold+Italic)\n"
                "✅ *Coding Help* 💻\n"
                "✅ *Knowledge* 📚\n"
                "✅ *Fun & Jokes* 😂\n"
                "✅ *Mute System* 🇮🇳\n"
                "✅ *Auto Unmute* ⏰\n"
                "✅ *Welcome System* 👋\n"
                "✅ *User Permission* 👥\n"
                "✅ *Broadcast* 📢\n"
                "✅ *Private Lock* 🔒\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚡ *OWNER COMMANDS:*\n"
                "/start — Restart bot\n"
                "/clear — Clear memory\n"
                "/activate — Group ON\n"
                "/mute — Mute user\n"
                "/unmute — Unmute user\n"
                "/adduser — Add user\n"
                "/removeuser — Remove user\n"
                "/userlist — View users\n"
                "/broadcast — Message all\n"
                "/id — Get user ID\n\n"
                "_Bolo boss! Kya chahiye?_ 🔥",
                parse_mode="Markdown"
            )
        elif is_user_allowed(user_id):
            user_history[chat_id] = []
            await update.message.reply_text(
                "✅ *Bot Use Kar Sakte Ho!*\n\n"
                "💬 Kuch bhi puchho — *PREMIUM jawab* milega!\n\n"
                "⚡ /start | /clear | /id",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🔒 *PERMISSION NAHI HAI!*\n\n"
                "_Aapke paas bot use karne ki permission nahi hai._\n"
                "_Owner se contact karein._",
                parse_mode="Markdown"
            )
    else:
        user_history[chat_id] = []
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
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ *Sirf GROUP!*", parse_mode="Markdown")
        return
    
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text(
                "❌ *ADMIN ONLY!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 *STEPS:*\n"
                "1️⃣ Bot ko *ADMIN* banao\n"
                "2️⃣ Sab *permissions ON* karo\n"
                "3️⃣ Phir `/activate` bhejo\n"
                "━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode="Markdown"
            )
            return
    except:
        await update.message.reply_text("❌ *Bot ko ADMIN banao!*", parse_mode="Markdown")
        return
    
    active_groups[chat_id] = True
    user_history[chat_id] = []
    await update.message.reply_text(
        "✅ *GROUP ACTIVATED!* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *AB SAB ON:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 *Premium AI Replies*\n"
        "🔇 *Mute System*\n"
        "⏰ *Auto Unmute*\n"
        "👋 *New User Welcome*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📢 _Sab kuch bhejo — GARAM GAND jawab dega!_ 💎\n\n"
        "❌ /deactivate — Band karo",
        parse_mode="Markdown"
    )

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *DEACTIVATED!* `/activate` se on karo", parse_mode="Markdown")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_history[update.effective_chat.id] = []
    await update.message.reply_text("✅ *Memory Clear!* 💭", parse_mode="Markdown")

# ================== MESSAGE HANDLER ==================

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    user_id = update.effective_user.id
    
    # Welcome new users
    if message.new_chat_members:
        await welcome_new_user(update, context)
        return
    
    # Private chat permission check
    if chat_type == ChatType.PRIVATE:
        if not is_user_allowed(user_id):
            await message.reply_text(
                "🔒 *PERMISSION NAHI HAI!*\n\n"
                "_Private mein sirf allowed users use kar sakte hain._\n"
                "_Owner se contact karein._",
                parse_mode="Markdown"
            )
            return
    else:
        # Group must be activated
        if chat_id not in active_groups or not active_groups[chat_id]:
            return
    
    # Sirf text reply
    if not message.text:
        return
    
    user_input = message.text
    
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        bot_reply = get_premium_reply(user_input, chat_id)
        
        if chat_id not in user_history:
            user_history[chat_id] = []
        user_history[chat_id].append({"role":"user","content":user_input})
        user_history[chat_id].append({"role":"assistant","content":bot_reply})
        user_history[chat_id] = user_history[chat_id][-20:]
        
        await message.reply_text(bot_reply, parse_mode="Markdown")
    except:
        pass

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("mutelist", mutelist))
    app.add_handler(CommandHandler("adduser", adduser))
    app.add_handler(CommandHandler("removeuser", removeuser))
    app.add_handler(CommandHandler("userlist", userlist))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("💎 ULTIMATE PREMIUM COHERE BOT — ALL FEATURES!")
    print(f"👑 Owner: {OWNER_USER_ID}")
    print("✅ Premium AI | Bold+Italic | Mute | Welcome | Broadcast | Permission")
    app.run_polling()

if __name__ == "__main__":
    main()
