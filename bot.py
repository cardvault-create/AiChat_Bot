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
OWNER_USER_ID = 1234567890  # 👈 APNI USER ID DALO
# =================================================

co = cohere.Client(COHERE_API_KEY)

user_history = {}
active_groups = set()

PREMIUM_PREAMBLE = """Tu GARAM GAND AI Bot hai - ek PREMIUM AI assistant.

TERI PERSONALITY:
- Mast, funny, thoda attitude wala lekin respectful
- Har sawal ka DETAILED aur ACCURATE jawab
- Emojis use kar, baat entertaining rakh
- User ki language mein jawab de, natural baat kar
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
        return f"😅 Fir se try karo! {str(e)[:40]}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    # Group mein koi bhi start kar sakta
    if chat_type != ChatType.PRIVATE:
        user_history[chat_id] = []
        await update.message.reply_text("👋 Bot ready! Admin /activate kare phir sab reply milega!")
        return
    
    # Private mein sirf owner
    if user_id != OWNER_USER_ID:
        await update.message.reply_text(
            "🔒 **PRIVATE BOT** 🔒\n\n"
            "❌ Ye bot sirf OWNER ke liye hai!\n"
            "👑 Private chat mein sirf owner use kar sakta hai.\n\n"
            "💡 Group mein add karo — wahan sabko reply milega!"
        )
        return
    
    user_history[chat_id] = []
    await update.message.reply_text(
        "💎 **WELCOME BACK BOSS!** 💎\n\n"
        "✅ Private: Sirf tum\n"
        "✅ Group: Sabko reply\n\n"
        "/start - Restart\n/clear - Memory\n"
        "/activate - Group ON\n/deactivate - Group OFF"
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
                "📢 Ab GROUP mein KOI BHI kuch bheje —\n"
                "   sabka PREMIUM REPLY milega!\n\n"
                "❌ Band: /deactivate"
            )
        else:
            await update.message.reply_text("❌ Sirf GROUP ADMIN yeh command use kar sakta hai!")
    except:
        await update.message.reply_text("❌ Pehle bot ko GROUP ADMIN banao!")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP mein chalta hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.discard(chat_id)
            await update.message.reply_text("🔴 Group Deactivated!")
        else:
            await update.message.reply_text("❌ Sirf GROUP ADMIN!")
    except:
        await update.message.reply_text("❌ Pehle admin banao!")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text("✅ Memory Clear!")

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    user_id = update.effective_user.id
    
    # ========== PERMISSION CHECK ==========
    # Private chat → Sirf owner allowed
    if chat_type == ChatType.PRIVATE and user_id != OWNER_USER_ID:
        await update.message.reply_text(
            "🔒 **PRIVATE BOT** 🔒\n\n"
            "Private chat mein sirf BOSS use kar sakta hai! 👑\n\n"
            "💡 Mujhe GROUP mein add karo — wahan SABKO reply milega!"
        )
        return
    
    # Group chat → Activated hona chahiye
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
        user_input = f"📄 Document {doc_name}"
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
        await message.reply_text("😅 Fir se try karo!")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("=" * 60)
    print("🔒 GARAM GAND AI — HYBRID MODE")
    print("👑 Private: Owner Only")
    print("👥 Group: Everyone (Activated)")
    print("=" * 60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
