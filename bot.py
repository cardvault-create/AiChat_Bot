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
OWNER_USER_ID = 1234567890  # 👈 APNI USER ID DALO
# =================================================

co = cohere.Client(COHERE_API_KEY)

# India Time Zone
IST = pytz.timezone('Asia/Kolkata')

user_history = {}
active_groups = set()

PREMIUM_PREAMBLE = """Tu GARAM GAND AI Bot hai - ek PREMIUM AI assistant.
Mast, funny, thoda attitude wala lekin respectful.
Har sawal ka DETAILED aur ACCURATE jawab.
User ki language mein jawab de, natural baat kar.
Emojis use kar, baat entertaining rakh."""

# ================== TIME FUNCTIONS ==================

def get_ist_now():
    """Current India time (IST)"""
    return datetime.now(IST)

def parse_time(time_str):
    """Time string ko minutes mein convert: 25s, 5m, 2h, 1d, 90s"""
    time_str = time_str.lower().strip()
    
    if time_str.endswith('s'):
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
    """Indian style time formatting with full detail"""
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

# ================== AI FUNCTION ==================

def get_premium_reply(user_input, chat_id):
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
        return f"😅 Fir se try karo! {str(e)[:40]}"

# ================== MUTE SYSTEM ==================

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ko mute karo - India time ke saath"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP mein chalta hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, admin_id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Sirf ADMIN mute kar sakta hai! 👑")
            return
    except:
        await update.message.reply_text("❌ Admin check fail!")
        return
    
    target_user = None
    time_str = "1h"
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        if context.args:
            time_str = context.args[0]
    elif context.args:
        if len(context.args) >= 2:
            try:
                target_id = int(context.args[0])
                target_user = await context.bot.get_chat_member(chat_id, target_id)
                target_user = target_user.user
                time_str = context.args[1]
            except:
                await update.message.reply_text("❌ Usage: /mute [user_id] [time]\nYa reply karke: /mute [time]")
                return
        elif len(context.args) == 1:
            if update.message.reply_to_message:
                target_user = update.message.reply_to_message.from_user
                time_str = context.args[0]
            else:
                await update.message.reply_text(
                    "🔇 **MUTE COMMAND USAGE** 🇮🇳\n\n"
                    "📌 **Kisi message ko reply karke:**\n"
                    "`/mute 25s` — 25 seconds\n"
                    "`/mute 90s` — 90 seconds (1m 30s)\n"
                    "`/mute 5m` — 5 minutes\n"
                    "`/mute 2h` — 2 hours\n"
                    "`/mute 1d` — 1 day\n"
                    "`/mute 3d` — 3 days\n\n"
                    "📌 **Forward message pe reply:**\n"
                    "`/mute 30m`\n\n"
                    "📌 **Manual User ID se:**\n"
                    "`/mute 123456789 1h`\n\n"
                    "🇮🇳 Time: India Standard Time (IST)\n"
                    "🔊 Unmute: `/unmute` reply karke"
                )
                return
    
    if not target_user:
        await update.message.reply_text("❌ User nahi mila! Kisi message ko reply karo ya User ID do.")
        return
    
    if target_user.id == admin_id:
        await update.message.reply_text("❌ Khud ko mute nahi kar sakte! 😅")
        return
    
    if target_user.is_bot:
        await update.message.reply_text("❌ Bot ko mute nahi kar sakte! 🤖")
        return
    
    try:
        mute_minutes = parse_time(time_str)
    except:
        await update.message.reply_text("❌ Galat time format! Use: 25s, 5m, 2h, 1d, 30d")
        return
    
    if mute_minutes > 43200:
        await update.message.reply_text("❌ Max 30 days (30d) mute kar sakte ho!")
        return
    
    if mute_minutes <= 0:
        await update.message.reply_text("❌ Time 0 se zyada hona chahiye!")
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
            f"❌ Mute nahi ho paya!\n\n"
            f"⚠️ Bot ko yeh permissions chahiye:\n"
            f"✅ Ban Users\n"
            f"✅ Delete Messages\n\n"
            f"Error: {str(e)[:80]}"
        )

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ko unmute karo"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP mein chalta hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, admin_id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Sirf ADMIN unmute kar sakta hai!")
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
            "1️⃣ Kisi message ko reply karke: `/unmute`\n"
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
        await update.message.reply_text(f"❌ Unmute nahi ho paya: {str(e)[:50]}")

async def mutelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute help dikhao"""
    await update.message.reply_text(
        "🔇 **MUTE SYSTEM HELP** 🇮🇳\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **MUTE KARNA:**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ **Reply karke:**\n"
        "   Kisi message ko reply karo\n"
        "   `/mute 25s` — 25 seconds\n"
        "   `/mute 5m` — 5 minutes\n"
        "   `/mute 2h` — 2 hours\n"
        "   `/mute 1d` — 1 day\n\n"
        "2️⃣ **Forward message pe:**\n"
        "   Forward msg pe reply + `/mute 30m`\n\n"
        "3️⃣ **Manual ID se:**\n"
        "   `/mute 123456789 1h`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **UNMUTE KARNA:**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Reply karke: `/unmute`\n"
        "Manual: `/unmute user_id`\n\n"
        "🇮🇳 **Time: India (IST)**\n"
        "👑 **Sirf Admin use kar sakta hai**"
    )

# ================== ORIGINAL COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type != ChatType.PRIVATE:
        user_history[chat_id] = []
        await update.message.reply_text(
            "👋 **GARAM GAND AI Ready!** 🇮🇳\n\n"
            "👑 Admin: /activate karo\n"
            "🔇 /mute — User mute (IST time)\n"
            "🔊 /unmute — User unmute\n"
            "📋 /mutelist — Mute help\n\n"
            "💬 Activate ke baad sab messages ka reply milega!"
        )
        return
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text(
            "🔒 **PRIVATE BOT** 🔒\n\n"
            "Ye bot sirf OWNER ke liye hai!\n"
            "Group mein add karo — wahan sabko reply milega!"
        )
        return
    
    user_history[chat_id] = []
    await update.message.reply_text(
        "💎 **WELCOME BACK BOSS!** 💎\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 **SYSTEMS ACTIVE:**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ AI Replies (Premium)\n"
        "✅ Mute System (IST Time) 🇮🇳\n"
        "✅ Private Lock 🔒\n"
        "✅ Group Support 👥\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ **COMMANDS:**\n"
        "/start - Restart\n"
        "/clear - Memory clear\n"
        "/activate - Group ON\n"
        "/deactivate - Group OFF\n"
        "/mute - Mute user\n"
        "/unmute - Unmute user\n"
        "/mutelist - Mute help\n\n"
        "🇮🇳 India Time Zone Ready!"
    )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP mein chalta hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.add(chat_id)
            user_history[chat_id] = []
            await update.message.reply_text(
                "✅ **GROUP ACTIVATED!** 🔥\n\n"
                "📢 Sabko AI reply milega!\n"
                "🔇 Mute system bhi ON hai!\n\n"
                "👑 Admin Commands:\n"
                "/mute — Mute user\n"
                "/unmute — Unmute user\n"
                "/deactivate — Band karo"
            )
        else:
            await update.message.reply_text("❌ Sirf GROUP ADMIN!")
    except:
        await update.message.reply_text("❌ Pehle bot ko GROUP ADMIN banao!")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.discard(chat_id)
            await update.message.reply_text("🔴 Group Deactivated!")
    except:
        pass

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE and user_id != OWNER_USER_ID:
        return
    
    user_history[chat_id] = []
    await update.message.reply_text("✅ Memory Clear!")

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    user_id = update.effective_user.id
    
    # Private chat — owner only
    if chat_type == ChatType.PRIVATE and user_id != OWNER_USER_ID:
        await update.message.reply_text(
            "🔒 **PRIVATE BOT** 🔒\n\n"
            "Private mein sirf OWNER use kar sakta hai! 👑\n\n"
            "💡 Mujhe GROUP mein add karo —\n"
            "   wahan SABKO reply milega!\n"
            "   Mute system bhi kaam karega! 🇮🇳"
        )
        return
    
    # Group check
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    # Message detection
    if message.text:
        user_input = message.text
    elif message.caption:
        if message.photo:
            user_input = f"🖼️ [PHOTO]: {message.caption}"
        elif message.video:
            user_input = f"🎬 [VIDEO]: {message.caption}"
        elif message.document:
            user_input = f"📄 [DOC]: {message.caption}"
        else:
            user_input = f"[Media]: {message.caption}"
    elif message.photo:
        user_input = "🖼️ Photo bheji hai"
    elif message.video:
        user_input = "🎬 Video bheja hai"
    elif message.sticker:
        emoji = message.sticker.emoji or ""
        user_input = f"🎯 Sticker {emoji}"
    elif message.voice:
        user_input = "🎵 Voice message"
    elif message.audio:
        user_input = "🎧 Audio"
    elif message.document:
        doc_name = message.document.file_name or ""
        user_input = f"📄 Document: {doc_name}"
    elif message.animation:
        user_input = "🎞️ GIF"
    elif message.video_note:
        user_input = "📹 Video note"
    elif message.location:
        user_input = "📍 Location"
    elif message.contact:
        user_input = "👤 Contact"
    elif message.poll:
        user_input = "📊 Poll"
    else:
        user_input = "📨 Message"

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        bot_reply = get_premium_reply(user_input, chat_id)
        
        if chat_id not in user_history:
            user_history[chat_id] = []
        user_history[chat_id].append({"role": "user", "content": user_input})
        user_history[chat_id].append({"role": "assistant", "content": bot_reply})
        user_history[chat_id] = user_history[chat_id][-30:]
        
        await message.reply_text(bot_reply)
        
    except Exception as e:
        print(f"Error: {e}")

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
    print("🇮🇳 GARAM GAND AI + MUTE SYSTEM (IST)")
    print("🔇 Mute: /mute 25s, /mute 5m, /mute 2h, /mute 1d")
    print("🔊 Unmute: /unmute")
    print("=" * 60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
