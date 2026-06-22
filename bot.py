import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== KEYS ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")  # 👈 Naya variable
# ==========================================

# DeepSeek API URL
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

user_history = {}
active_groups = set()

def get_ai_reply(user_input, history):
    messages = [{"role": "system", "content": "Tu ek mast, funny aur helpful AI assistant hai. Thoda attitude wala, thoda funny. User ki language mein jawab de."}]
    
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
        "messages": messages
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
        "📝 Text | 🖼️ Photo | 🎵 Voice | 🎬 Video | 🎯 Sticker\n\n"
        "/start - Restart\n/clear - Memory clear\n"
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
            await update.message.reply_text("✅ Bot ACTIVATED! Ab GROUP ke HAR message ka reply dunga!")
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
            await update.message.reply_text("🔴 Bot DEACTIVATED!")
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
    
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    if message.text:
        user_input = message.text
    elif message.caption:
        user_input = f"[Media]: {message.caption}"
    elif message.photo:
        user_input = "🖼️ [Photo]"
    elif message.video:
        user_input = "🎬 [Video]"
    elif message.sticker:
        emoji = message.sticker.emoji or "❓"
        user_input = f"🎯 [Sticker] {emoji}"
    elif message.voice:
        user_input = "🎵 [Voice]"
    elif message.audio:
        user_input = "🎧 [Audio]"
    elif message.document:
        user_input = f"📄 [File] {message.document.file_name or ''}"
    elif message.animation:
        user_input = "🎞️ [GIF]"
    elif message.location:
        user_input = "📍 [Location]"
    elif message.contact:
        user_input = "👤 [Contact]"
    elif message.poll:
        user_input = f"📊 [Poll]"
    else:
        user_input = "📨 [Message]"

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        if chat_id not in user_history:
            user_history[chat_id] = []
        
        bot_reply = get_ai_reply(user_input, user_history[chat_id])
        
        user_history[chat_id].append({"role": "user", "content": user_input})
        user_history[chat_id].append({"role": "assistant", "content": bot_reply})
        user_history[chat_id] = user_history[chat_id][-20:]
        
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
    
    print("=" * 50)
    print("🔥 GARAM GAND AI Bot Started! (DeepSeek)")
    print("=" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()
