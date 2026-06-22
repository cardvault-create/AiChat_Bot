import os
import cohere
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== KEYS ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
# ==========================================

# ================== OWNER SETUP ==================
OWNER_USER_ID = 7614459746  # 👈 APNI USER ID DALO
# =================================================

co = cohere.Client(COHERE_API_KEY)

user_history = {}
active_groups = set()
muted_users = {}  # {user_id: unmute_time}

PREMIUM_PREAMBLE = """Tu GARAM GAND AI Bot hai - ek PREMIUM AI assistant.
Mast, funny, thoda attitude wala lekin respectful.
Har sawal ka DETAILED aur ACCURATE jawab.
User ki language mein jawab de, natural baat kar.
Emojis use kar, baat entertaining rakh."""

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
    except:
        return "😅 Fir se try karo!"

# ================== MUTE SYSTEM ==================

def parse_time(time_str):
    """Time string ko minutes mein convert karo: 5m, 2h, 1d"""
    time_str = time_str.lower().strip()
    
    if time_str.endswith('m'):
        return int(time_str[:-1])
    elif time_str.endswith('h'):
        return int(time_str[:-1]) * 60
    elif time_str.endswith('d'):
        return int(time_str[:-1]) * 1440
    else:
        return int(time_str)  # Default minutes

def format_time(minutes):
    """Minutes ko readable format mein"""
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif minutes < 1440:
        hours = minutes // 60
        mins = minutes % 60
        if mins > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} {mins} min"
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        days = minutes // 1440
        hours = (minutes % 1440) // 60
        if hours > 0:
            return f"{days} day{'s' if days != 1 else ''} {hours} hour{'s' if hours != 1 else ''}"
        return f"{days} day{'s' if days != 1 else ''}"

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ko mute karo - reply ya forward message se"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    # Sirf group mein
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP mein chalta hai!")
        return
    
    # Admin check
    try:
        member = await context.bot.get_chat_member(chat_id, admin_id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Sirf ADMIN mute kar sakta hai! 👑")
            return
    except:
        await update.message.reply_text("❌ Admin check fail!")
        return
    
    # Target user find karo
    target_user = None
    time_str = "1h"  # Default 1 hour
    
    # Reply se target lo
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        
        # Agar time diya hai command mein
        if context.args:
            time_str = context.args[0]
    
    # Agar reply nahi, to manual user ID
    elif context.args:
        if len(context.args) >= 2:
            try:
                target_id = int(context.args[0])
                target_user = await context.bot.get_chat_member(chat_id, target_id)
                target_user = target_user.user
                time_str = context.args[1]
            except:
                await update.message.reply_text("❌ Usage: /mute [user_id] [time]\nYa kisi message ko reply karke: /mute [time]")
                return
        elif len(context.args) == 1:
            # Reply bina time diya
            if update.message.reply_to_message:
                target_user = update.message.reply_to_message.from_user
                time_str = context.args[0]
            else:
                await update.message.reply_text(
                    "❌ **MUTE USAGE:**\n\n"
                    "1️⃣ Reply karke: `/mute 30m`\n"
                    "   Message pe reply karo + /mute time\n\n"
                    "2️⃣ Manual: `/mute user_id 2h`\n\n"
                    "⏰ Time: 5m = 5 min | 2h = 2 hours | 1d = 1 day"
                )
                return
    else:
        await update.message.reply_text(
            "❌ **MUTE USAGE:**\n\n"
            "1️⃣ Kisi message ko **reply** karke:\n"
            "   `/mute 10m` — 10 min mute\n"
            "   `/mute 2h` — 2 hours mute\n"
            "   `/mute 1d` — 1 day mute\n\n"
            "2️⃣ Forward message pe reply:\n"
            "   `/mute 30m`\n\n"
            "3️⃣ Manual:\n"
            "   `/mute 123456789 1h`"
        )
        return
    
    if not target_user:
        await update.message.reply_text("❌ User nahi mila!")
        return
    
    # Khud ko mute nahi
    if target_user.id == admin_id:
        await update.message.reply_text("❌ Khud ko mute nahi kar sakte! 😅")
        return
    
    # Bot ko mute nahi
    if target_user.is_bot:
        await update.message.reply_text("❌ Bot ko mute nahi kar sakte! 🤖")
        return
    
    # Time parse karo
    try:
        mute_minutes = parse_time(time_str)
    except:
        await update.message.reply_text("❌ Galat time format! Use: 5m, 2h, 1d")
        return
    
    # Max 30 days
    if mute_minutes > 43200:
        await update.message.reply_text("❌ Max 30 days mute kar sakte ho!")
        return
    
    # User ko mute karo
    until_time = datetime.utcnow() + timedelta(minutes=mute_minutes)
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_time
        )
        
        target_name = target_user.first_name or "User"
        admin_name = update.effective_user.first_name
        
        await update.message.reply_text(
            f"🔇 **MUTED!** 🔇\n\n"
            f"👤 User: {target_name}\n"
            f"⏰ Time: {format_time(mute_minutes)}\n"
            f"👑 By: {admin_name}\n\n"
            f"Unmute hoga: {until_time.strftime('%I:%M %p, %d %b %Y')}\n\n"
            f"Unmute karne ke liye: /unmute kisi message pe reply karo"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Mute nahi ho paya! Bot ko admin rights do.\nError: {str(e)[:50]}")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ko unmute karo"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP mein chalta hai!")
        return
    
    # Admin check
    try:
        member = await context.bot.get_chat_member(chat_id, admin_id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Sirf ADMIN unmute kar sakta hai!")
            return
    except:
        return
    
    target_user = None
    
    # Reply se target
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
            "❌ **UNMUTE USAGE:**\n\n"
            "Kisi message ko reply karke: `/unmute`\n"
            "Ya: `/unmute user_id`"
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
        
        target_name = target_user.first_name or "User"
        await update.message.reply_text(f"✅ **UNMUTED!** {target_name} ab message kar sakta hai! 🎉")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Unmute nahi ho paya: {str(e)[:50]}")

async def mutelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muted users list (currently not stored, but shows restricted)"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP mein chalta hai!")
        return
    
    await update.message.reply_text(
        "📋 **MUTE SYSTEM**\n\n"
        "Users check karne ke liye Group Info → Permissions dekho.\n\n"
        "⚡ **Commands:**\n"
        "/mute [time] — Reply se mute\n"
        "/unmute — Reply se unmute"
    )

# ================== ORIGINAL COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type != ChatType.PRIVATE:
        user_history[chat_id] = []
        await update.message.reply_text(
            "👋 **GARAM GAND AI Ready!**\n\n"
            "👑 Admin: /activate karo\n"
            "🔇 /mute — User mute\n"
            "🔊 /unmute — User unmute"
        )
        return
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("🔒 Private bot! Group mein add karo.")
        return
    
    user_history[chat_id] = []
    await update.message.reply_text(
        "💎 **WELCOME BOSS!** 💎\n\n"
        "/start - Restart\n/clear - Memory\n"
        "/mute - Mute user\n/unmute - Unmute"
    )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.add(chat_id)
            user_history[chat_id] = []
            await update.message.reply_text("✅ ACTIVATED! Sabko reply + mute system ON!")
        else:
            await update.message.reply_text("❌ Sirf ADMIN!")
    except:
        await update.message.reply_text("❌ Admin banao!")

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
            await update.message.reply_text("🔴 Deactivated!")
    except:
        pass

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text("✅ Memory Clear!")

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE and user_id != OWNER_USER_ID:
        await update.message.reply_text("🔒 Private bot! Group mein add karo — wahan sabko reply milega!")
        return
    
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    # Message detection
    if message.text:
        user_input = message.text
    elif message.caption:
        user_input = f"[Media]: {message.caption}"
    elif message.photo:
        user_input = "🖼️ Photo bheji"
    elif message.video:
        user_input = "🎬 Video"
    elif message.sticker:
        emoji = message.sticker.emoji or ""
        user_input = f"🎯 Sticker {emoji}"
    elif message.voice:
        user_input = "🎵 Voice"
    elif message.audio:
        user_input = "🎧 Audio"
    elif message.document:
        user_input = "📄 Document"
    elif message.animation:
        user_input = "🎞️ GIF"
    elif message.location:
        user_input = "📍 Location"
    elif message.contact:
        user_input = "👤 Contact"
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
    except:
        pass

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    
    # Mute system
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("mutelist", mutelist))
    
    # Messages
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("🔇 GARAM GAND + MUTE SYSTEM READY!")
    app.run_polling()

if __name__ == "__main__":
    main()
