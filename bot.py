import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== KEYS ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# ==========================================

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

user_history = {}
active_groups = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    if chat_type == ChatType.PRIVATE:
        user_history[chat_id] = []
        await update.message.reply_text(
            "👋 Hello! Main aapka AI assistant hoon.\n\n"
            "🔥 Sab kuch reply doonga!\n"
            "📝 Text | 🖼️ Photo | 🎵 Voice | 🎬 Video | 🎯 Sticker\n\n"
            "Commands:\n"
            "/start - Phir se shuru\n"
            "/clear - History clear\n"
            "/activate - Group ON (admin only)\n"
            "/deactivate - Group OFF (admin only)"
        )
    else:
        await update.message.reply_text("👋 Bot active! Admin /activate kare.")

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf group mein kaam karega!")
        return
    
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status in ['administrator', 'creator']:
        active_groups.add(chat_id)
        user_history[chat_id] = []
        await update.message.reply_text("✅ Bot ACTIVATED! /deactivate se band karo.")
    else:
        await update.message.reply_text("❌ Sirf admin use kar sakta hai!")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf group mein kaam karega!")
        return
    
    member = await context.bot.get_chat_member(chat_id, user_id)
    if member.status in ['administrator', 'creator']:
        active_groups.discard(chat_id)
        await update.message.reply_text("🔴 Bot DEACTIVATED! /activate se on karo.")
    else:
        await update.message.reply_text("❌ Sirf admin use kar sakta hai!")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text("✅ Memory clear!")

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    # Message type detect
    if message.text:
        user_input = message.text
    elif message.caption:
        user_input = f"[Media with caption]: {message.caption}"
    elif message.photo:
        user_input = "[Photo received]"
    elif message.video:
        user_input = "[Video received]"
    elif message.sticker:
        emoji = message.sticker.emoji or "unknown"
        user_input = f"[Sticker] {emoji}"
    elif message.voice:
        user_input = "[Voice message]"
    elif message.audio:
        user_input = f"[Audio] {message.audio.title or 'unknown'}"
    elif message.document:
        user_input = f"[Document] {message.document.file_name or 'unknown'}"
    elif message.animation:
        user_input = "[GIF]"
    elif message.location:
        user_input = f"[Location]"
    elif message.contact:
        user_input = f"[Contact] {message.contact.first_name or ''}"
    elif message.poll:
        user_input = f"[Poll] {message.poll.question}"
    else:
        user_input = "[Message received]"

    if chat_type == ChatType.PRIVATE:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        if chat_id not in user_history:
            user_history[chat_id] = []
        
        prompt = "You are a helpful AI assistant. Reply in user's language. Be natural.\n\n"
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

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("🤖 Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
