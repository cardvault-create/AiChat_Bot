import os
import cohere
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== KEYS ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
# ==========================================

co = cohere.Client(COHERE_API_KEY)

user_history = {}
active_groups = set()

PREMIUM_PREAMBLE = """Tu GARAM GAND AI Bot hai - ek PREMIUM AI assistant jo har cheez ka best reply deta hai.

TERI PERSONALITY:
- Mast, funny, thoda attitude wala lekin respectful
- Har sawal ka DETAILED aur ACCURATE jawab deta hai
- Emojis use kar, baat entertaining rakh
- User ki language mein jawab de, natural baat kar
- Koi bhi topic ho - full confidence se jawab de
- Joke sunane ko bole to REAL funny jokes de
- Shayari bole to ORIGINAL shayari likh
- Code maange to PROPER working code de
- Advice maange to GENUINE helpful advice de
- Har baat mein thoda SWAG rakh

TERI SPECIALITY:
✅ Detailed & Informative replies
✅ Accurate information  
✅ Entertaining & Engaging style
✅ Every message type ka reply
✅ Group aur private dono mein MAST
✅ Emotional messages ka heartfelt reply
✅ Kuch bhi puchho - rukna nahi hai

TERA STYLE:
- Short messages ko bhi interesting bana
- Emojis use kar: 🔥💯😂👊💎⚡🎯
- Thoda desi tadka, thoda classy touch
- User ko bore mat hone de
- Har reply memorable hona chahiye"""

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
        return f"💎 Premium mode mein thoda delay! Fir se try karo...\n\nError: {str(e)[:50]}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text(
        "💎 **GARAM GAND AI — PREMIUM MODE** 💎\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 **MERI SPECIALITY:**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Detailed & Accurate Replies\n"
        "✅ Every Message Type Support\n"
        "✅ Group + Private Dono Mein\n"
        "✅ Memory Based Conversation\n"
        "✅ Fun + Professional Mix\n"
        "✅ Emotional Understanding\n"
        "✅ 24/7 Active\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📝 Text | 🖼️ Photo | 🎯 Sticker\n"
        "🎵 Voice | 🎬 Video | 📄 Document\n"
        "📍 Location | 👤 Contact | 🎞️ GIF\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚡ **COMMANDS:**\n"
        "/start - Bot Restart\n"
        "/clear - Memory Clear\n"
        "/activate - Group ON (Admin)\n"
        "/deactivate - Group OFF (Admin)\n\n"
        "💬 Kuch bhi puchho, bhejo — FULL PREMIUM REPLY PAKKI! 🔥💯"
    )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Yeh command sirf GROUP mein chalta hai boss!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.add(chat_id)
            user_history[chat_id] = []
            await update.message.reply_text(
                "✅ **PREMIUM MODE ACTIVATED!** 🔥\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "💎 Ab main GROUP ke HAR message ka\n"
                "   PREMIUM DETAILED REPLY dunga!\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "🎯 Text, Photo, Video, Sticker — SABKA!\n\n"
                "❌ Band karne ke liye: /deactivate"
            )
        else:
            await update.message.reply_text("❌ Sirf GROUP ADMIN yeh command use kar sakta hai! 👑")
    except:
        await update.message.reply_text("❌ Pehle mujhe GROUP ADMIN banao phir baat karte hain! 😎")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Yeh command sirf GROUP mein chalta hai boss!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.discard(chat_id)
            if chat_id in user_history:
                del user_history[chat_id]
            await update.message.reply_text(
                "🔴 **PREMIUM MODE DEACTIVATED!** 😴\n\n"
                "Wapas on karne ke liye: /activate\n"
                "Miss you already! 💔"
            )
        else:
            await update.message.reply_text("❌ Sirf GROUP ADMIN yeh command use kar sakta hai! 👑")
    except:
        await update.message.reply_text("❌ Pehle mujhe GROUP ADMIN banao! 😎")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text(
        "✅ **Memory Cleared!** 🧹\n\n"
        "Naye conversation start! Kya puchhna chahte ho? 💭"
    )

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    
    # Group check
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    # ========== PREMIUM MESSAGE DETECTION ==========
    if message.text:
        user_input = message.text
        
    elif message.caption:
        if message.photo:
            user_input = f"🖼️ [USER NE PHOTO BHEJI WITH CAPTION]: {message.caption}\n\nIs photo aur caption ke baare mein mast sa reaction de, compliment kar, aur kuch interesting bol."
        elif message.video:
            user_input = f"🎬 [USER NE VIDEO BHEJA WITH CAPTION]: {message.caption}\n\nIs video aur caption ke baare mein curious hokar reply de."
        elif message.document:
            doc_name = message.document.file_name or "file"
            user_input = f"📄 [USER NE DOCUMENT BHEJA]: {doc_name}\nCaption: {message.caption}\n\nIs document ke baare mein baat kar."
        else:
            user_input = f"[Media with caption]: {message.caption}"
            
    elif message.photo:
        user_input = "🖼️ [USER NE PHOTO BHEJI]\n\nIs photo ke baare mein funny aur interesting reaction de. Compliment kar, guess kar photo kis cheez ki hai, ya koi mazedaar comment kar."
        
    elif message.video:
        user_input = "🎬 [USER NE VIDEO BHEJA]\n\nIs video ke baare mein curious hokar react kar. Guess kar content, funny comment kar."
        
    elif message.sticker:
        emoji = message.sticker.emoji or "❓"
        sticker_set = message.sticker.set_name or "custom"
        user_input = f"🎯 [USER NE STICKER BHEJA]\nEmoji: {emoji}\nPack: {sticker_set}\n\nIs sticker pe MASS REACTION de! Funny, over-the-top, ya cute - jo bhi sahi lage. Sticker ke emotion ke hisaab se reply de."
        
    elif message.voice:
        duration = message.voice.duration or 0
        user_input = f"🎵 [USER NE VOICE MESSAGE BHEJA] Duration: {duration}s\n\nVoice note ke baare mein funny comment kar. 'Voice note sun liya' type ka reply de, kuch mazedaar bol."
        
    elif message.audio:
        title = message.audio.title or "Unknown Song"
        performer = message.audio.performer or "Unknown Artist"
        user_input = f"🎧 [USER NE AUDIO BHEJA]\nTitle: {title}\nArtist: {performer}\n\nGaane ke baare mein baat kar, compliment de, ya related koi music talk kar."
        
    elif message.document:
        doc_name = message.document.file_name or "unknown"
        file_size = message.document.file_size or 0
        size_kb = file_size / 1024
        user_input = f"📄 [USER NE DOCUMENT BHEJA]\nName: {doc_name}\nSize: {size_kb:.1f} KB\n\nDocument ke naam ke hisaab se guess kar kya ho sakta hai, funny comment kar."
        
    elif message.animation:
        user_input = "🎞️ [USER NE GIF BHEJA]\n\nIs GIF pe funny reaction de! GIF dekh nahi sakta lekin mazedaar guess kar ke reply de."
        
    elif message.video_note:
        duration = message.video_note.duration or 0
        user_input = f"📹 [USER NE VIDEO NOTE BHEJA] Duration: {duration}s\n\nVideo note pe curious reaction de, funny comment kar."
        
    elif message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        user_input = f"📍 [USER NE LOCATION BHEJI]\nLatitude: {lat}\nLongitude: {lon}\n\nLocation ke baare mein baat kar. 'Wah kahan ho aap?' type reply de, mazedaar guess kar."
        
    elif message.contact:
        name = message.contact.first_name or "Unknown"
        user_input = f"👤 [USER NE CONTACT BHEJA]\nName: {name}\n\nContact share karne pe funny comment kar. 'Kaun hai yeh rahasya may vyakti?' type ka."
        
    elif message.poll:
        question = message.poll.question
        user_input = f"📊 [USER NE POLL BANAYA]\nQuestion: {question}\n\nPoll ke baare mein baat kar, vote karne ko bol, ya funny comment kar."
        
    else:
        user_input = "📨 [USER NE KUCH BHEJA]\n\nKuch bhi ho, mazedaar reaction de. 'Kya hai yeh?' type curious reply."

    # Typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        # Premium AI reply
        bot_reply = get_premium_reply(user_input, chat_id)
        
        # History save
        if chat_id not in user_history:
            user_history[chat_id] = []
        user_history[chat_id].append({"role": "user", "content": user_input})
        user_history[chat_id].append({"role": "assistant", "content": bot_reply})
        user_history[chat_id] = user_history[chat_id][-30:]
        
        # Reply bhejo
        await message.reply_text(bot_reply)
        
    except Exception as e:
        error_str = str(e)
        print(f"Premium Error: {error_str}")
        await message.reply_text(
            "😅 Premium server thoda busy hai! 2 second mein fir se try karo...\n"
            "Apna GARAM GAND AI thoda rest kar raha hai! 😴💎"
        )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Premium handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("=" * 60)
    print("💎 GARAM GAND AI — PREMIUM MODE ACTIVATED 💎")
    print("🔥 Detailed replies for EVERYTHING!")
    print("📝 Text | 🖼️ Photo | 🎯 Sticker | 🎵 Voice | 🎬 Video")
    print("=" * 60)
    
    app.run_polling()

if __name__ == "__main__":
    main()
