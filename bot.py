import os
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
OWNER_USER_ID = 7614459746  # 👈 APNI USER ID YAHAN DALO (@userinfobot se pata karo)
# =================================================

co = cohere.Client(COHERE_API_KEY)

# India Time Zone
IST = pytz.timezone('Asia/Kolkata')

user_history = {}
active_groups = set()

# ================== PREMIUM AI PERSONALITY ==================

PREMIUM_PREAMBLE = """Tu GARAM GAND AI Bot hai — ek PREMIUM, MAST aur FUNNY AI assistant.

TERI PERSONALITY:
- Tu mast, funny, thoda attitude wala lekin RESPECTFUL hai
- Har sawal ka DETAILED, ACCURATE aur HELPFUL jawab deta hai
- Emojis use karta hai: 🔥💯😂👊💎⚡🎯❤️🙏
- User ki LANGUAGE mein jawab deta hai
- NATURAL baat karta hai, robot ki tarah nahi
- Joke sunane ko bole to REAL FUNNY jokes deta hai
- Shayari bole to ORIGINAL SHAYARI likhta hai
- Code maange to PROPER WORKING CODE deta hai
- Advice maange to GENUINE HELPFUL ADVICE deta hai
- Koi bhi topic ho — FULL CONFIDENCE se jawab deta hai
- Har baat mein thoda SWAG rakhta hai

TERA STYLE:
- Short messages ko bhi INTERESTING banata hai
- Desi + Classy mix
- Kabhi boring nahi hota
- Har reply MEMORABLE hota hai
- User ki feeling samajhta hai
- Funny rehna hai lekin KABHI rude nahi hona

TERI SPECIALITY:
✅ Detailed & Informative replies
✅ Accurate information
✅ Entertaining & Engaging style
✅ Every message type ka reply
✅ Group aur private dono mein MAST
✅ Emotional messages ka heartfelt reply
✅ Kuch bhi puchho — RUKNA NAHI HAI"""

# ================== TIME FUNCTIONS ==================

def get_ist_now():
    """Current India time (IST)"""
    return datetime.now(IST)

def parse_time(time_str):
    """Time string ko minutes mein convert — words aur short format dono support"""
    time_str = time_str.lower().strip().replace(" ", "")
    
    # Full words ke saath
    if time_str.endswith('seconds') or time_str.endswith('second') or time_str.endswith('sec'):
        num = time_str.replace('seconds', '').replace('second', '').replace('sec', '')
        return float(num) / 60
    elif time_str.endswith('minutes') or time_str.endswith('minute') or time_str.endswith('mins') or time_str.endswith('min'):
        num = time_str.replace('minutes', '').replace('minute', '').replace('mins', '').replace('min', '')
        return float(num)
    elif time_str.endswith('hours') or time_str.endswith('hour') or time_str.endswith('hrs') or time_str.endswith('hr'):
        num = time_str.replace('hours', '').replace('hour', '').replace('hrs', '').replace('hr', '')
        return float(num) * 60
    elif time_str.endswith('days') or time_str.endswith('day'):
        num = time_str.replace('days', '').replace('day', '')
        return float(num) * 1440
    
    # Short format
    elif time_str.endswith('s'):
        return float(time_str[:-1]) / 60
    elif time_str.endswith('m'):
        return float(time_str[:-1])
    elif time_str.endswith('h'):
        return float(time_str[:-1]) * 60
    elif time_str.endswith('d'):
        return float(time_str[:-1]) * 1440
    else:
        return float(time_str)

def format_time(minutes):
    """Time ko detailed Indian format mein dikhao"""
    total_seconds = int(minutes * 60)
    
    if total_seconds <= 0:
        return "0 seconds"
    
    days = total_seconds // 86400
    remaining = total_seconds % 86400
    hours = remaining // 3600
    remaining = remaining % 3600
    mins = remaining // 60
    secs = remaining % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if mins > 0:
        parts.append(f"{mins} minute{'s' if mins != 1 else ''}")
    if secs > 0 and days == 0:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    
    return ", ".join(parts) if parts else "0 seconds"

# ================== AI REPLY FUNCTION ==================

def get_premium_reply(user_input, chat_id):
    """Premium AI reply generate karo"""
    if chat_id not in user_history:
        user_history[chat_id] = []
    
    history = user_history[chat_id]
    chat_history = []
    for msg in history[-10:]:
        role = "USER" if msg["role"] == "user" else "CHATBOT"
        chat_history.append({"role": role, "message": msg["content"]})
    
    try:
        response = co.chat(
            message=user_input,
            chat_history=chat_history,
            preamble=PREMIUM_PREAMBLE,
            temperature=0.95,
            max_tokens=600
        )
        return response.text
    except Exception as e:
        return f"💎 Premium mode mein thoda delay, fir se try karo bhai! 😅\n\n_{str(e)[:50]}_"

# ================== MUTE SYSTEM ==================

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ko mute karo — koi bhi time format support"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    # Sirf group
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Yeh command sirf **GROUP** mein chalta hai mere bhai!")
        return
    
    # Admin check
    try:
        member = await context.bot.get_chat_member(chat_id, admin_id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Sirf **GROUP ADMIN** mute kar sakta hai! 👑")
            return
    except:
        await update.message.reply_text("❌ Admin check fail! Bot ko admin rights do.")
        return
    
    target_user = None
    time_str = "1h"  # Default 1 hour
    
    # Target user dhundo
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        if context.args:
            time_str = " ".join(context.args)  # "10 second" jaisa multi-word support
    elif context.args:
        # Manual user ID
        if len(context.args) >= 2:
            try:
                target_id = int(context.args[0])
                target_user = await context.bot.get_chat_member(chat_id, target_id)
                target_user = target_user.user
                time_str = " ".join(context.args[1:])
            except:
                await update.message.reply_text("❌ User ID galat hai ya user group mein nahi hai!")
                return
        else:
            await update.message.reply_text(
                "🔇 **MUTE COMMAND USAGE** 🇮🇳\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 **Reply karke (EASIEST):**\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "1️⃣ User ke message pe **reply** karo\n"
                "2️⃣ `/mute 10 second` bhejo\n"
                "3️⃣ `/mute 5 minute` bhejo\n"
                "4️⃣ `/mute 2 hour` bhejo\n"
                "5️⃣ `/mute 1 day` bhejo\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 **Short format bhi chalega:**\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "`/mute 25s` — 25 seconds\n"
                "`/mute 5m` — 5 minutes\n"
                "`/mute 2h` — 2 hours\n"
                "`/mute 1d` — 1 day\n"
                "`/mute 30d` — 30 days (max)\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 **Manual User ID se:**\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "`/mute 123456789 10 minute`\n\n"
                "🇮🇳 **Time: India (IST) accurate!**\n"
                "🔊 Unmute: `/unmute` reply karke"
            )
            return
    
    if not target_user:
        await update.message.reply_text("❌ User nahi mila! Kisi message ko **reply** karo ya User ID do.")
        return
    
    # Khud ko mute nahi
    if target_user.id == admin_id:
        await update.message.reply_text("😅 Khud ko mute karke kya milega bhai? Soch le!")
        return
    
    # Bot ko mute nahi
    if target_user.is_bot:
        await update.message.reply_text("🤖 Bot ko mute nahi kar sakte! Machines se dosti karo!")
        return
    
    # Time parse karo
    try:
        mute_minutes = parse_time(time_str)
    except:
        await update.message.reply_text(
            "❌ **Time format galat hai!** 😕\n\n"
            "✅ Sahi examples:\n"
            "`/mute 10 second`\n`/mute 5 minute`\n`/mute 2 hour`\n`/mute 1 day`\n"
            "`/mute 25s` `/mute 5m` `/mute 2h` `/mute 1d`"
        )
        return
    
    # Max 30 days
    if mute_minutes > 43200:
        await update.message.reply_text("❌ Max **30 days** tak mute kar sakte ho bhai!")
        return
    
    if mute_minutes <= 0:
        await update.message.reply_text("❌ Time **0 se zyada** hona chahiye!")
        return
    
    # India time calculate
    now_ist = get_ist_now()
    until_ist = now_ist + timedelta(minutes=mute_minutes)
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_ist
        )
        
        target_name = target_user.first_name or "Unknown"
        if target_user.last_name:
            target_name += f" {target_user.last_name}"
        
        admin_name = update.effective_user.first_name or "Admin"
        
        await update.message.reply_text(
            f"🔇 **MUTED! — INDIA TIME** 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **User:** {target_name}\n"
            f"🆔 User ID: `{target_user.id}`\n"
            f"👑 **Muted by:** {admin_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ **Duration:** {format_time(mute_minutes)}\n\n"
            f"📅 **Muted at:**\n"
            f"   🕐 `{now_ist.strftime('%I:%M:%S %p')}`\n"
            f"   📆 {now_ist.strftime('%d %B %Y')}\n\n"
            f"🔓 **Unmute hoga:**\n"
            f"   🕐 `{until_ist.strftime('%I:%M:%S %p')}`\n"
            f"   📆 {until_ist.strftime('%d %B %Y')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔊 Unmute karne ke liye:\n"
            f"   User ke message pe reply karke `/unmute` bhejo"
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ **Mute nahi ho paya!**\n\n"
            f"⚠️ Zaroori permissions:\n"
            f"✅ Ban Users\n"
            f"✅ Delete Messages\n\n"
            f"Error: `{str(e)[:80]}`"
        )

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ko unmute karo"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf **GROUP** mein chalta hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, admin_id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Sirf **GROUP ADMIN** unmute kar sakta hai! 👑")
            return
    except:
        return
    
    target_user = None
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        try:
            target_id = int(context.args[0])
            target_user = await context.bot.get_chat_member(chat_id, target_id)
            target_user = target_user.user
        except:
            await update.message.reply_text("❌ User ID galat hai!")
            return
    else:
        await update.message.reply_text(
            "🔊 **UNMUTE USAGE**\n\n"
            "1️⃣ Kisi message ko **reply** karke: `/unmute`\n"
            "2️⃣ Manual: `/unmute user_id`"
        )
        return
    
    if not target_user:
        await update.message.reply_text("❌ User nahi mila!")
        return
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
        )
        
        now_ist = get_ist_now()
        target_name = target_user.first_name or "User"
        
        await update.message.reply_text(
            f"✅ **UNMUTED!** 🇮🇳\n\n"
            f"👤 **User:** {target_name}\n"
            f"🔓 **Unmuted at:**\n"
            f"   🕐 `{now_ist.strftime('%I:%M:%S %p')}`\n"
            f"   📆 {now_ist.strftime('%d %B %Y')}\n\n"
            f"💬 Ab message kar sakta hai! 🎉"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Unmute nahi ho paya: `{str(e)[:50]}`")

async def mutelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute help guide"""
    await update.message.reply_text(
        "🔇 **MUTE SYSTEM — COMPLETE GUIDE** 🇮🇳\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **MUTE KAISE KAREIN:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ **Reply karke (BEST):**\n"
        "   User ke message pe reply karo\n"
        "   Phir bolo:\n"
        "   `/mute 10 second`\n"
        "   `/mute 5 minute`\n"
        "   `/mute 2 hour`\n"
        "   `/mute 1 day`\n\n"
        "2️⃣ **Short format:**\n"
        "   `/mute 25s` — 25 seconds\n"
        "   `/mute 5m` — 5 minutes\n"
        "   `/mute 2h` — 2 hours\n"
        "   `/mute 1d` — 1 day\n"
        "   `/mute 30d` — 30 days (max)\n\n"
        "3️⃣ **Forward message pe:**\n"
        "   Forward msg reply + `/mute 30 minute`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **UNMUTE KAISE KAREIN:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Reply karke: `/unmute`\n"
        "Manual: `/unmute user_id`\n\n"
        "🇮🇳 **India Time (IST) accurate!**\n"
        "👑 **Sirf Group Admin use kar sakta hai**"
    )

# ================== BASIC COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    # Group chat
    if chat_type != ChatType.PRIVATE:
        user_history[chat_id] = []
        await update.message.reply_text(
            "👋 **GARAM GAND AI BOT READY!** 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 **Admin Commands:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "/activate — Bot ON karo\n"
            "/mute — User mute karo\n"
            "/unmute — User unmute karo\n"
            "/mutelist — Mute help\n\n"
            "💬 Activate ke baad sab messages\n"
            "   ka PREMIUM REPLY milega! 🔥"
        )
        return
    
    # Private chat — owner only
    if user_id != OWNER_USER_ID:
        await update.message.reply_text(
            "🔒 **PRIVATE BOT** 🔒\n\n"
            "Ye bot sirf **OWNER** ke liye hai!\n\n"
            "💡 **Group mein add karo** —\n"
            "   wahan sabko reply milega!\n"
            "   Mute system bhi kaam karega! 🇮🇳"
        )
        return
    
    # Owner private chat
    user_history[chat_id] = []
    await update.message.reply_text(
        "💎 **WELCOME BACK BOSS!** 💎\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 **PREMIUM SYSTEMS ACTIVE:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Premium AI Replies\n"
        "✅ Mute System (IST) 🇮🇳\n"
        "✅ Seconds/Minutes/Hours/Days\n"
        "✅ Private Lock 🔒\n"
        "✅ Group Support 👥\n"
        "✅ Sab Media Reply\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ **COMMANDS:**\n"
        "/start — Restart bot\n"
        "/clear — Memory clear\n"
        "/activate — Group ON\n"
        "/deactivate — Group OFF\n"
        "/mute — User mute\n"
        "/unmute — User unmute\n"
        "/mutelist — Mute help\n\n"
        "💬 Bolo boss, kya chahiye? 🔥"
    )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf **GROUP** mein chalta hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.add(chat_id)
            user_history[chat_id] = []
            await update.message.reply_text(
                "✅ **GROUP ACTIVATED!** 🔥\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📢 Ab group mein **KOI BHI**\n"
                "   kuch bhi bhejega —\n"
                "   **PREMIUM REPLY** milega!\n\n"
                "🔇 **Mute System:**\n"
                "   `/mute 10 second`\n"
                "   `/mute 5 minute`\n"
                "   `/mute 2 hour`\n"
                "   `/mute 1 day`\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ Band karne: /deactivate"
            )
        else:
            await update.message.reply_text("❌ Sirf **GROUP ADMIN** use kar sakta hai! 👑")
    except:
        await update.message.reply_text("❌ Pehle bot ko **GROUP ADMIN** banao!")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf **GROUP** mein chalta hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.discard(chat_id)
            await update.message.reply_text("🔴 **Group Deactivated!** Wapas on: /activate")
    except:
        pass

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text("✅ **Memory Clear!** Naye conversation start! 💭")

# ================== MESSAGE HANDLER ==================

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    user_id = update.effective_user.id
    
    # Private chat — sirf owner
    if chat_type == ChatType.PRIVATE and user_id != OWNER_USER_ID:
        await update.message.reply_text(
            "🔒 **PRIVATE BOT** 🔒\n\n"
            "Private mein sirf **OWNER** use kar sakta hai! 👑\n\n"
            "💡 Mujhe **GROUP** mein add karo —\n"
            "   wahan **SABKO** reply milega!\n"
            "   Mute system bhi ON hoga! 🇮🇳"
        )
        return
    
    # Group — activated hona chahiye
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    # ========== MESSAGE TYPE DETECTION ==========
    if message.text:
        user_input = message.text
    elif message.caption:
        if message.photo:
            user_input = f"🖼️ [PHOTO]: {message.caption}"
        elif message.video:
            user_input = f"🎬 [VIDEO]: {message.caption}"
        elif message.document:
            user_input = f"📄 [DOCUMENT]: {message.caption}"
        elif message.animation:
            user_input = f"🎞️ [GIF]: {message.caption}"
        else:
            user_input = f"[Media]: {message.caption}"
    elif message.photo:
        user_input = "🖼️ Photo bheji hai — iska mazedaar reaction de"
    elif message.video:
        user_input = "🎬 Video bheja hai — iska mazedaar reaction de"
    elif message.sticker:
        emoji = message.sticker.emoji or ""
        user_input = f"🎯 Sticker bheja hai {emoji} — ispe funny reaction de"
    elif message.voice:
        user_input = "🎵 Voice message bheja hai — funny comment kar"
    elif message.audio:
        user_input = "🎧 Audio file bheji hai — music pe baat kar"
    elif message.document:
        doc_name = message.document.file_name or "file"
        user_input = f"📄 Document bheja hai: {doc_name} — iske baare mein bol"
    elif message.animation:
        user_input = "🎞️ GIF bheja hai — mazedaar reaction de"
    elif message.video_note:
        user_input = "📹 Video note bheja hai — funny comment kar"
    elif message.location:
        user_input = "📍 Location bheji hai — puchho kahan ho"
    elif message.contact:
        user_input = "👤 Contact share kiya hai — mazedaar comment kar"
    elif message.poll:
        user_input = "📊 Poll banaya hai — vote karne ko bol"
    else:
        user_input = "📨 Kuch bheja hai — curious reaction de"

    # Typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        # Premium AI reply
        bot_reply = get_premium_reply(user_input, chat_id)
        
        # History save
        if chat_id not in user_history:
            user_history[chat_id] = []
        user_history[chat_id].append({"role": "user", "content": user_input})
        user_history[chat_id].append({"role": "assistant", "content": bot_reply})
        user_history[chat_id] = user_history[chat_id][-30:]
        
        # Reply bhejo
        await message.reply_text(bot_reply)
        
    except Exception as e:
        print(f"Error: {e}")
        # Silent fail — bot crash nahi hoga

# ================== MAIN ==================

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Basic commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    
    # Mute system
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("mutelist", mutelist))
    
    # All messages
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("=" * 60)
    print("💎 GARAM GAND AI — ULTIMATE PREMIUM BOT")
    print("🇮🇳 India Time (IST) Mute System")
    print("🔇 /mute 10s | /mute 5m | /mute 2h | /mute 1d")
    print("🔊 /unmute")
    print("👑 Owner Only Private Chat")
    print("👥 Group — Sabko Reply")
    print("=" * 60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
