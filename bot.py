import os
import cohere
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== KEYS ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
# ==========================================

# ================== OWNER SETUP ==================
# Apna Telegram User ID yahan dalo
OWNER_USER_ID = 7614459746  # 👈 APNI USER ID YAHAN DALO
# =================================================

co = cohere.Client(COHERE_API_KEY)

user_history = {}
active_groups = set()

# Allowed users (Owner + jinko permission do)
allowed_users = {OWNER_USER_ID}  # Sirf owner allowed by default

PREMIUM_PREAMBLE = """Tu GARAM GAND AI Bot hai - ek PREMIUM AI assistant jo sirf apne OWNER ke liye kaam karta hai.

TERI PERSONALITY:
- Mast, funny, thoda attitude wala lekin respectful
- Har sawal ka DETAILED aur ACCURATE jawab
- Emojis use kar, baat entertaining rakh
- Owner ki language mein jawab de
- Owner ko "Boss" ya "Sir" bulake respect de
- Joke sunane ko bole to REAL funny jokes de
- Shayari bole to ORIGINAL shayari likh
- Code maange to PROPER working code de
- Har baat mein thoda SWAG rakh"""

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
        return f"💎 Premium mode mein thoda delay! Fir se try karo..."

def is_allowed(user_id):
    """Check if user is allowed"""
    return user_id in allowed_users

async def check_permission(update: Update) -> bool:
    """Check if user has permission to use bot"""
    user_id = update.effective_user.id
    
    if not is_allowed(user_id):
        # Unauthorized user
        await update.message.reply_text(
            "🔒 **ACCESS DENIED!** 🔒\n\n"
            "❌ Sorry, yeh bot PRIVATE hai!\n"
            "👑 Sirf OWNER hi use kar sakta hai.\n\n"
            "💎 Agar tum owner ho to /verify karo."
        )
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if not is_allowed(user_id):
        await update.message.reply_text(
            "🔒 **PRIVATE BOT** 🔒\n\n"
            "Ye bot sirf owner ke liye hai!\n"
            "Agar owner ho to /verify karo.\n\n"
            "😎 - GARAM GAND AI"
        )
        return
    
    user_history[chat_id] = []
    user = update.effective_user
    await update.message.reply_text(
        f"💎 **WELCOME BACK BOSS!** 💎\n\n"
        f"👑 Owner: **{user.first_name}**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 **PREMIUM FEATURES:**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Detailed & Accurate Replies\n"
        "✅ Every Message Type Support\n"
        "✅ Memory Based Conversation\n"
        "✅ Fun + Professional Mix\n"
        "✅ 100% Private & Secure\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📝 Text | 🖼️ Photo | 🎯 Sticker\n"
        "🎵 Voice | 🎬 Video | 📄 Document\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚡ **OWNER COMMANDS:**\n"
        "/start - Bot Restart\n"
        "/clear - Memory Clear\n"
        "/adduser [ID] - User Add Karo\n"
        "/removeuser [ID] - User Remove\n"
        "/users - Allowed Users List\n"
        "/activate - Group ON\n"
        "/deactivate - Group OFF\n\n"
        "💬 Bolo boss, kya chahiye? 🔥"
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner verify karne ke liye"""
    user_id = update.effective_user.id
    
    if user_id == OWNER_USER_ID:
        allowed_users.add(user_id)
        await update.message.reply_text("✅ **Verified! Welcome back Boss!** 👑💎")
    else:
        await update.message.reply_text("❌ Tum owner nahi ho! Sirf owner /verify kar sakta hai!")

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """New user allow karo"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ Sirf OWNER yeh command use kar sakta hai! 👑")
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /adduser [user_id]\nExample: /adduser 123456789")
        return
    
    try:
        new_user_id = int(context.args[0])
        allowed_users.add(new_user_id)
        await update.message.reply_text(f"✅ User `{new_user_id}` added! Ab wo bot use kar sakta hai! 🎉")
    except:
        await update.message.reply_text("❌ Valid user ID do! Example: /adduser 123456789")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User remove karo"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ Sirf OWNER yeh command use kar sakta hai! 👑")
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /removeuser [user_id]")
        return
    
    try:
        remove_id = int(context.args[0])
        if remove_id == OWNER_USER_ID:
            await update.message.reply_text("❌ Owner ko remove nahi kar sakte! 😎")
            return
        allowed_users.discard(remove_id)
        await update.message.reply_text(f"✅ User `{remove_id}` removed!")
    except:
        await update.message.reply_text("❌ Valid user ID do!")

async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allowed users dikhao"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ Sirf OWNER yeh command use kar sakta hai! 👑")
        return
    
    user_list = "\n".join([f"• `{uid}`" for uid in allowed_users])
    await update.message.reply_text(f"👥 **ALLOWED USERS:**\n\n{user_list}\n\nTotal: {len(allowed_users)} users")

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ Sirf OWNER group activate kar sakta hai! 👑")
        return
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP mein chalta hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.add(chat_id)
            user_history[chat_id] = []
            await update.message.reply_text(
                "✅ **GROUP ACTIVATED BOSS!** 🔥\n\n"
                "Ab main group mein reply dunga!\n"
                "Lekin sirf allowed users ko hi! 🔒"
            )
        else:
            await update.message.reply_text("❌ Pehle admin banao!")
    except:
        await update.message.reply_text("❌ Pehle admin banao!")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ Sirf OWNER deactivate kar sakta hai! 👑")
        return
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP mein chalta hai!")
        return
    
    active_groups.discard(chat_id)
    await update.message.reply_text("🔴 Group Deactivated!")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        return
    
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text("✅ Memory Clear Boss!")

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    user_id = update.effective_user.id
    
    # Permission check
    if not is_allowed(user_id):
        await update.message.reply_text(
            "🔒 **ACCESS DENIED!** 🔒\n\n"
            "Ye bot PRIVATE hai — Sirf OWNER use kar sakta hai! 👑\n\n"
            "Apna bot banana hai? Contact @EgoFather_Ai_Bot"
        )
        return
    
    # Group check
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    # ========== MESSAGE DETECTION ==========
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
        user_input = "🖼️ Photo bheji hai boss!"
    elif message.video:
        user_input = "🎬 Video bheja hai boss!"
    elif message.sticker:
        emoji = message.sticker.emoji or ""
        user_input = f"🎯 Sticker bheja {emoji}"
    elif message.voice:
        user_input = "🎵 Voice message bheja hai boss!"
    elif message.audio:
        user_input = "🎧 Audio bheja hai boss!"
    elif message.document:
        user_input = f"📄 Document bheja hai boss!"
    elif message.animation:
        user_input = "🎞️ GIF bheja hai boss!"
    elif message.video_note:
        user_input = "📹 Video note bheja hai boss!"
    elif message.location:
        user_input = "📍 Location bheji hai boss!"
    elif message.contact:
        user_input = "👤 Contact bheja hai boss!"
    elif message.poll:
        user_input = "📊 Poll banaya hai boss!"
    else:
        user_input = "📨 Kuch bheja hai boss!"

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
        await message.reply_text("😅 Thoda error aaya boss, fir se try karo!")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Owner commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify", verify))
    app.add_handler(CommandHandler("adduser", adduser))
    app.add_handler(CommandHandler("removeuser", removeuser))
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    
    # Message handler
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("=" * 60)
    print("🔒 GARAM GAND AI — OWNER ONLY MODE")
    print(f"👑 Owner ID: {OWNER_USER_ID}")
    print("=" * 60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
