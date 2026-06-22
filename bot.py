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
    user_history[chat_id] = []
    await update.message.reply_text(
        "👋 Hello! Main GARAM GAND AI Bot hoon!\n\n"
        "🔥 Har ek cheez ka reply doonga!\n"
        "📝 Text | 🖼️ Photo | 🎵 Voice | 🎬 Video | 🎯 Sticker | 📄 Document\n\n"
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
            if chat_id in user_history:
                del user_history[chat_id]
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
    
    # Group check
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
        
        prompt = """Tu ek mast, funny aur helpful AI assistant hai.
GARAM GAND AI Bot ke naam se jaana jaata hai.
Thoda attitude wala, thoda funny, lekin fully helpful.
User ki language mein jawab de. Natural baat kar.\n\n"""
        
        for msg in user_history[chat_id][-5:]:
            prompt += f"{msg['role']}: {msg['content']}\n"
        
        prompt += f"user: {user_input}\nassistant:"
        
        # Gemini se jawab
        response = model.generate_content(prompt)
        bot_reply = response.text
        
        # History save
        user_history[chat_id].append({"role": "user", "content": user_input})
        user_history[chat_id].append({"role": "assistant", "content": bot_reply})
        user_history[chat_id] = user_history[chat_id][-20:]
        
        # Jawab bhejo
        await message.reply_text(bot_reply)
        
    except Exception as e:
        error_text = str(e)
        print(f"Error: {error_text}")
        
        # Agar quota khatam ho gaya
        if "quota" in error_text.lower() or "rate" in error_text.lower():
            await message.reply_text("😴 Thoda rest kar raha hoon, thodi der baad try karo!")
        # Agar API key problem
        elif "api" in error_text.lower() or "key" in error_text.lower():
            await message.reply_text("🔑 API Key problem hai! Nayi key set karo.")
        else:
            await message.reply_text(f"😅 Error: {error_text[:100]}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("=" * 50)
    print("🔥 GARAM GAND AI Bot Started!")
    print("=" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()
