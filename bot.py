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
        "🔥 MAIN BAAT: Har ek cheez ka reply doonga!\n"
        "📝 Text | 🖼️ Photo | 🎵 Voice | 🎬 Video | 🎯 Sticker | 📄 Document\n\n"
        "⚡ Commands:\n"
        "/start - Bot restart\n"
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
            await update.message.reply_text("🔴 Bot DEACTIVATED! Ab reply nahi dega.\n\nWapas on karne ke liye: /activate")
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
    
    # Group check
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    # ========== MESSAGE TYPE DETECT ==========
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
        user_input = f"🎯 [Sticker bheja gaya] Emoji: {emoji}"
    elif message.voice:
        user_input = "🎵 [Voice message bheja gaya]"
    elif message.audio:
        user_input = f"🎧 [Audio bheja gaya] {message.audio.title or ''}"
    elif message.document:
        user_input = f"📄 [Document bheja gaya] {message.document.file_name or ''}"
    elif message.animation:
        user_input = "🎞️ [GIF bheja gaya]"
    elif message.video_note:
        user_input = "📹 [Video note bheja gaya]"
    elif message.location:
        user_input = "📍 [Location bheja gaya]"
    elif message.contact:
        user_input = f"👤 [Contact bheja gaya] {message.contact.first_name or ''}"
    elif message.poll:
        user_input = f"📊 [Poll bheja gaya] {message.poll.question}"
    else:
        user_input = "📨 [Kuch bheja gaya]"

    # Typing indicator (sirf private chat)
    if chat_type == ChatType.PRIVATE:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        if chat_id not in user_history:
            user_history[chat_id] = []
        
        # Context banaye
        prompt = """Tu ek mast, friendly aur funny AI assistant hai. 
Tu GARAM GAND AI Bot hai - thoda attitude wala, thoda funny, lekin helpful.
User ki language mein jawab de.
Natural baat kar, robot ki tarah mat lag.
Har cheez ka mazedar jawab de.\n\n"""
        
        for msg in user_history[chat_id][-10:]:
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
        print(f"Error: {e}")
        await message.reply_text("😅 Thoda sa error aaya, fir se try karo!")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("=" * 50)
    print("🔥 GARAM GAND AI Bot Started!")
    print("📝 Har message ka reply dega!")
    print("=" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()
