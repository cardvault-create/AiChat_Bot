import google.generativeai as genai
from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== APNI KEYS YAHAN DALO ==================
TELEGRAM_TOKEN = "8865931839:AAHMaz381lylrdmeX2ESubiJj66SK386HEM"
GEMINI_API_KEY = "AIzaSyBsaJoC_aC31nSZyNFbPs3HnktkIVQ6Yt0"
# ==========================================================

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Har user/group ki conversation history
user_history = {}

# Group settings — kaunse group mein bot active hai
active_groups = set()  # Jin groups mein bot reply dega

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    if chat_type == ChatType.PRIVATE:
        user_history[chat_id] = []
        welcome_msg = (
            "👋 Hello! Main aapka AI assistant hoon.\n\n"
            "🔥 MAIN SPECIALITY: Har ek cheez ka reply doonga!\n"
            "📝 Text | 🖼️ Photo | 🎵 Voice | 🎬 Video | 🎯 Sticker | 📄 Document\n\n"
            "⚡ Mujhe group mein add karne ke liye:\n"
            "1. Bot ko group mein admin banao\n"
            "2. /activate bhejo group mein\n\n"
            "Commands:\n"
            "/start - Phir se shuru\n"
            "/clear - History clear\n"
            "/activate - Group mein bot ON karo (admin only)\n"
            "/deactivate - Group mein bot OFF karo (admin only)"
        )
        await update.message.reply_text(welcome_msg)
    else:
        await update.message.reply_text(
            "👋 Bot active hai!\n"
            "Group mein mujhe reply dilwane ke liye admin /activate command bheje."
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    # Private chat mein activate ka koi matlab nahi
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Yeh command sirf group mein kaam karti hai!")
        return
    
    # Check karo ke user admin hai ya nahi
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            active_groups.add(chat_id)
            user_history[chat_id] = []
            await update.message.reply_text(
                "✅ Bot ACTIVATED! Ab main har message ka reply dunga.\n\n"
                "Band karne ke liye: /deactivate"
            )
        else:
            await update.message.reply_text("❌ Sirf GROUP ADMIN yeh command use kar sakta hai!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Yeh command sirf group mein kaam karti hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            active_groups.discard(chat_id)
            if chat_id in user_history:
                del user_history[chat_id]
            await update.message.reply_text("🔴 Bot DEACTIVATED! Ab reply nahi dega.\nPhir se on karne ke liye: /activate")
        else:
            await update.message.reply_text("❌ Sirf GROUP ADMIN yeh command use kar sakta hai!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text("✅ Memory clear!")

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    
    # Private chat mein hamesha reply do
    # Group mein tabhi reply do jab activate ho
    if chat_type != ChatType.PRIVATE:
        if chat_id not in active_groups:
            return  # Group activate nahi hai, reply mat do
    
    # ========== MESSAGE TYPE DETECT KARO ==========
    
    if message.text:
        user_input = message.text
    elif message.caption:
        if message.photo:
            user_input = f"[Photo with caption]: {message.caption}"
        elif message.video:
            user_input = f"[Video with caption]: {message.caption}"
        elif message.document:
            doc_name = message.document.file_name if message.document.file_name else "unknown"
            user_input = f"[Document '{doc_name}' with caption]: {message.caption}"
        elif message.animation:
            user_input = f"[GIF with caption]: {message.caption}"
        else:
            user_input = f"[File with caption]: {message.caption}"
    elif message.photo:
        user_input = "[Photo received]"
    elif message.video:
        user_input = "[Video received]"
    elif message.sticker:
        emoji = message.sticker.emoji if message.sticker.emoji else "unknown"
        user_input = f"[Sticker] Emoji: {emoji}"
    elif message.voice:
        duration = message.voice.duration if message.voice.duration else 0
        user_input = f"[Voice message, {duration}s]"
    elif message.audio:
        title = message.audio.title if message.audio.title else "unknown"
        user_input = f"[Audio] {title}"
    elif message.video_note:
        user_input = "[Video note received]"
    elif message.document:
        doc_name = message.document.file_name if message.document.file_name else "unknown"
        user_input = f"[Document] {doc_name}"
    elif message.animation:
        user_input = "[GIF received]"
    elif message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        user_input = f"[Location] Lat: {lat}, Lon: {lon}"
    elif message.contact:
        name = message.contact.first_name if message.contact.first_name else "Unknown"
        user_input = f"[Contact] {name}"
    elif message.poll:
        user_input = f"[Poll] {message.poll.question}"
    else:
        user_input = "[Something received]"

    # Typing indicator (sirf private chat mein)
    if chat_type == ChatType.PRIVATE:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        if chat_id not in user_history:
            user_history[chat_id] = []
        
        prompt = """You are a friendly AI assistant in a Telegram group/chat.
Always respond in the SAME LANGUAGE the user is using.
If in a group, be concise but helpful.
If reacting to media (photo, video, sticker), describe it or react naturally.
\n\n"""
        
        # Last 10 messages ka context
        if user_history[chat_id]:
            for msg in user_history[chat_id][-10:]:
                prompt += f"{msg['role']}: {msg['content']}\n"
        
        prompt += f"user: {user_input}\nassistant:"
        
        # Gemini se jawab
        response = model.generate_content(prompt)
        bot_reply = response.text
        
        # History save
        user_history[chat_id].append({"role": "user", "content": user_input})
        user_history[chat_id].append({"role": "assistant", "content": bot_reply})
        
        if len(user_history[chat_id]) > 20:
            user_history[chat_id] = user_history[chat_id][-20:]
        
        # Jawab bhejo
        await message.reply_text(bot_reply)
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        try:
            await message.reply_text(error_msg)
        except:
            print(f"Reply error: {e}")
        print(f"Full error: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error: {context.error}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    
    # 🔥 Har ek cheez handle karega
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    app.add_error_handler(error_handler)
    
    print("=" * 60)
    print("🤖 BOT READY — Group + Private Dono Mein Kaam Karega!")
    print("📋 Group Setup Steps:")
    print("   1. BotFather se Privacy Mode DISABLE karo")
    print("   2. Bot ko Group mein Admin banao")
    print("   3. Group mein /activate bhejo")
    print("=" * 60)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
