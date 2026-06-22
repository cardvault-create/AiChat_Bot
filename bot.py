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

def get_ai_reply(user_input, history):
    """DeepSeek API se jawab lekar aaye"""
    messages = [{
        "role": "system",
        "content": "Tu ek mast, funny aur helpful AI assistant hai. Naam hai GARAM GAND AI Bot. Thoda attitude wala, thoda funny, lekin fully helpful. User ki language mein jawab de. Natural baat kar, robot mat lag."
    }]
    
    for msg in history[-5:]:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
    
    messages.append({"role": "user", "content": user_input})
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.9
    }
    
    response = requests.post(DEEPSEEK_URL, headers=headers, json=data)
    result = response.json()
    return result["choices"][0]["message"]["content"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text(
        "👋 Hello! Main GARAM GAND AI Bot hoon!\n\n"
        "🔥 Har ek cheez ka reply doonga!\n"
        "📝 Text | 🖼️ Photo | 🎵 Voice | 🎬 Video | 🎯 Sticker | 📄 Document\n\n"
        "Commands:\n"
        "/start - Restart bot\n"
        "/clear - Memory clear\n"
        "/activate - Group ON (admin only)\n"
        "/deactivate - Group OFF (admin only)"
    )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Yeh command sirf GROUP mein chalta hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.add(chat_id)
            user_history[chat_id] = []
            await update.message.reply_text("✅ Bot ACTIVATED! Ab main GROUP ke HAR message ka reply dunga!\n\nBand karne ke liye: /deactivate")
        else:
            await update.message.reply_text("❌ Sirf GROUP ADMIN yeh command use kar sakta hai!")
    except:
        await update.message.reply_text("❌ Pehle bot ko GROUP ADMIN banao!")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Yeh command sirf GROUP mein chalta hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.discard(chat_id)
            if chat_id in user_history:
                del user_history[chat_id]
            await update.message.reply_text("🔴 Bot DEACTIVATED!\n\nWapas on karne ke liye: /activate")
        else:
            await update.message.reply_text("❌ Sirf GROUP ADMIN yeh command use kar sakta hai!")
    except:
        await update.message.reply_text("❌ Pehle bot ko GROUP ADMIN banao!")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text("✅ Memory clear! Naye conversation start!")

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    
    # Group check - sirf activate groups mein reply
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    # ========== MESSAGE TYPE DETECT ==========
    if message.text:
        user_input = message.text
    elif message.caption:
        user_input = f"[Media with caption]: {message.caption}"
    elif message.photo:
        user_input = "🖼️ [Photo bheja gaya]"
    elif message.video:
        user_input = "🎬 [Video bheja gaya]"
    elif message.sticker:
        emoji = message.sticker.emoji or "❓"
        user_input = f"🎯 [Sticker bheja gaya] Emoji: {emoji}"
    elif message.voice:
        user_input = "🎵 [Voice message bheja gaya]"
    elif message.audio:
        user_input = f"🎧 [Audio bheja gaya]"
    elif message.document:
        user_input = f"📄 [Document bheja gaya] {message.document.file_name or ''}"
    elif message.animation:
        user_input = "🎞️ [GIF bheja gaya]"
    elif message.video_note:
        user_input = "📹 [Video note bheja gaya]"
    elif message.location:
        user_input = "📍 [Location bheja gaya]"
    elif message.contact:
        user_input = f"👤 [Contact bheja gaya]"
    elif message.poll:
        user_input = f"📊 [Poll bheja gaya]"
    else:
        user_input = "📨 [Kuch bheja gaya]"

    # Typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        if chat_id not in user_history:
            user_history[chat_id] = []
        
        # AI se jawab
        bot_reply = get_ai_reply(user_input, user_history[chat_id])
        
        # History save
        user_history[chat_id].append({"role": "user", "content": user_input})
        user_history[chat_id].append({"role": "assistant", "content": bot_reply})
        user_history[chat_id] = user_history[chat_id][-20:]
        
        # Jawab bhejo
        await message.reply_text(bot_reply)
        
    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text("😅 Phir se try karo, thoda error aaya!")

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
