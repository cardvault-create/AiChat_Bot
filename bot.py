import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== KEYS ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
# ==========================================

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

user_history = {}
active_groups = set()

def get_ai_reply(user_input, chat_id):
    """DeepSeek API se jawab"""
    if chat_id not in user_history:
        user_history[chat_id] = []
    
    messages = [{
        "role": "system",
        "content": "Tu GARAM GAND AI Bot hai - ek mast, funny, thoda attitude wala AI assistant. User ki language mein jawab de. Natural baat kar, robot mat lag. Har sawal ka mazedaar jawab de."
    }]
    
    # Pichle messages ka context
    history = user_history[chat_id]
    for msg in history[-6:]:
        messages.append(msg)
    
    messages.append({"role": "user", "content": user_input})
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.9,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=data, timeout=30)
        result = response.json()
        
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            error_msg = result.get("error", {}).get("message", "Unknown error")
            return f"😅 API Error: {error_msg}"
    except Exception as e:
        return f"😅 Network Error: {str(e)[:50]}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text(
        "👋 Hello! Main GARAM GAND AI Bot hoon!\n\n"
        "🔥 Har ek cheez ka reply doonga!\n"
        "📝 Text | 🖼️ Photo | 🎯 Sticker | 🎵 Voice | 🎬 Video | 📄 Document\n\n"
        "⚡ Commands:\n"
        "/start - Restart\n"
        "/clear - Memory clear\n"
        "/activate - Group ON (admin)\n"
        "/deactivate - Group OFF (admin)"
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
            await update.message.reply_text("✅ Bot ACTIVATED! Ab GROUP ke HAR message ka reply dunga!\n\nBand karne ke liye: /deactivate")
        else:
            await update.message.reply_text("❌ Sirf GROUP ADMIN use kar sakta hai!")
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
            await update.message.reply_text("🔴 Bot DEACTIVATED!\n\nWapas on: /activate")
        else:
            await update.message.reply_text("❌ Sirf GROUP ADMIN use kar sakta hai!")
    except:
        await update.message.reply_text("❌ Pehle bot ko GROUP ADMIN banao!")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text("✅ Memory clear!")

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    
    # Group check
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    # ========== DETECT MESSAGE TYPE ==========
    if message.text:
        user_input = message.text
    elif message.caption:
        user_input = f"[Media with text]: {message.caption}"
    elif message.photo:
        user_input = "🖼️ [Photo bheja gaya]"
    elif message.video:
        user_input = "🎬 [Video bheja gaya]"
    elif message.sticker:
        emoji = message.sticker.emoji or "❓"
        user_input = f"🎯 [Sticker] Emoji: {emoji}"
    elif message.voice:
        user_input = "🎵 [Voice message]"
    elif message.audio:
        user_input = "🎧 [Audio file]"
    elif message.document:
        doc_name = message.document.file_name or "unknown"
        user_input = f"📄 [Document] {doc_name}"
    elif message.animation:
        user_input = "🎞️ [GIF]"
    elif message.video_note:
        user_input = "📹 [Video note]"
    elif message.location:
        user_input = "📍 [Location]"
    elif message.contact:
        user_input = "👤 [Contact]"
    elif message.poll:
        user_input = "📊 [Poll]"
    else:
        user_input = "📨 [Message received]"

    # Typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    # AI jawab
    bot_reply = get_ai_reply(user_input, chat_id)
    
    # History save
    if chat_id not in user_history:
        user_history[chat_id] = []
    user_history[chat_id].append({"role": "user", "content": user_input})
    user_history[chat_id].append({"role": "assistant", "content": bot_reply})
    
    # Sirf last 20 messages rakho
    if len(user_history[chat_id]) > 20:
        user_history[chat_id] = user_history[chat_id][-20:]
    
    # Jawab bhejo
    await message.reply_text(bot_reply)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("=" * 50)
    print("🔥 GARAM GAND AI Bot Started! (DeepSeek)")
    print("📝 Har message ka reply dega!")
    print("=" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()
