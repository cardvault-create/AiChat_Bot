import os
import google.generativeai as genai
from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== KEYS (Variables se lega) ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# ==============================================================

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

user_history = {}
active_groups = set()

# ... baaki pura code same ...

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    if chat_type == ChatType.PRIVATE:
        user_history[chat_id] = []
        welcome_msg = (
            "👋 Hello! Main aapka AI assistant hoon.\n\n"
            "🔥 MAIN SPECIALITY: Har ek cheez ka reply doonga!\n"
            "📝 Text | 🖼️ Photo | 🎵 Voice | 🎬 Video | 🎯 Sticker | 📄 Document\n\n"
            "Commands:\n"
            "/start - Phir se shuru\n"
            "/clear - History clear\n"
            "/activate - Group mein bot ON karo (admin only)\n"
            "/deactivate - Group mein bot OFF karo (admin only)"
        )
        await update.message.reply_text(welcome_msg)
    else:
        await update.message.reply_text("👋 Bot active hai! Admin /activate bheje reply ke liye.")

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Yeh command sirf group mein kaam karti hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            active_groups.add(chat_id)
            user_history[chat_id] = []
            await update.message.reply_text("✅ Bot ACTIVATED! Ab main har message ka reply dunga.\nBand karne ke liye: /deactivate")
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
            await update.message.reply_text("🔴 Bot DEACTIVATED! /activate se on karo.")
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
    
    # Group mein tabhi reply jab activate ho
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    # Message type detect
    if message.text:
        user_input = message.text
    elif message.caption:
        if message.photo:
            user_input = f"[Photo]: {message.caption}"
        elif message.video:
            user_input = f"[Video]: {message.caption}"
        elif message.document:
            doc_name = message.document.file_name or "unknown"
            user_input = f"[Document '{doc_name}']: {message.caption}"
        else:
            user_input = f"[File]: {message.caption}"
    elif message.photo:
        user_input = "[Photo received]"
    elif message.video:
        user_input = "[Video received]"
    elif message.sticker:
        emoji = message.sticker.emoji or "unknown"
        user_input = f"[Sticker] Emoji: {emoji}"
    elif message.voice:
        duration = message.voice.duration or 0
        user_input = f"[Voice message, {duration}s]"
    elif message.audio:
        title = message.audio.title or "unknown"
        user_input = f"[Audio] {title}"
    elif message.document:
        doc_name = message.document.file_name or "unknown"
        user_input = f"[Document] {doc_name}"
    elif message.animation:
        user_input = "[GIF received]"
    elif message.location:
        user_input = f"[Location] {message.location.latitude}, {message.location.longitude}"
    elif message.contact:
        name = message.contact.first_name or "Unknown"
        user_input = f"[Contact] {name}"
    elif message.poll:
        user_input = f"[Poll] {message.poll.question}"
    else:
        user_input = "[Something received]"

    # Typing indicator
    if chat_type == ChatType.PRIVATE:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        if chat_id not in user_history:
            user_history[chat_id] = []
        
        prompt = "You are a helpful AI assistant. Respond in user's language. Be natural.\n\n"
        
        for msg in user_history[chat_id][-10:]:
            prompt += f"{msg['role']}: {msg['content']}\n"
        
        prompt += f"user: {user_input}\nassistant:"
        
        response = model.generate_content(prompt)
        bot_reply = response.text
        
        user_history[chat_id].append({"role": "user", "content": user_input})
        user_history[chat_id].append({"role": "assistant", "content": bot_reply})
        user_history[chat_id] = user_history[chat_id][-20:]
        
        await message.reply_text(bot_reply)
        
    except Exception as e:
        print(f"Error: {e}")
        try:
            await message.reply_text(f"❌ Error: {e}")
        except:
            pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Error: {context.error}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    app.add_error_handler(error_handler)
    
    print("🤖 Bot started!")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
