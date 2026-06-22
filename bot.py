import os
import asyncio
import cohere
import pytz
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== KEYS ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
# ==========================================

# ================== OWNER SETUP ==================
OWNER_USER_ID = 7614459746
# =================================================

co = cohere.Client(COHERE_API_KEY)
IST = pytz.timezone('Asia/Kolkata')

user_history = {}
active_groups = {}

PREMIUM_PREAMBLE = """Tu GARAM GAND AI Bot hai — PREMIUM, MAST, FUNNY AI.
• SHORT + QUICK jawab de — 1-3 line max
• Sirf TEXT question ka jawab de
• Emojis use kar: 🔥💯😂👊💎⚡🎯❤️✨
• User ki LANGUAGE mein jawab
• *Bold* = important, _Italic_ = funny
• Joke maange to chhota joke de
• Code maange to short code de
• Advice maange to short advice de
• HAR REPLY MAX 1-3 LINES"""

def get_ist_now():
    return datetime.now(IST)

def parse_time(time_str):
    time_str = time_str.lower().strip().replace(" ", "")
    if not time_str:
        return None
    
    if 'seconds' in time_str or time_str.endswith('second') or time_str.endswith('sec'):
        num = time_str.replace('seconds','').replace('second','').replace('sec','')
        return float(num)/60 if num else None
    elif 'minutes' in time_str or time_str.endswith('minute') or time_str.endswith('mins') or time_str.endswith('min'):
        num = time_str.replace('minutes','').replace('minute','').replace('mins','').replace('min','')
        return float(num) if num else None
    elif 'hours' in time_str or time_str.endswith('hour') or time_str.endswith('hrs') or time_str.endswith('hr'):
        num = time_str.replace('hours','').replace('hour','').replace('hrs','').replace('hr','')
        return float(num)*60 if num else None
    elif 'days' in time_str or time_str.endswith('day'):
        num = time_str.replace('days','').replace('day','')
        return float(num)*1440 if num else None
    elif time_str.endswith('s'):
        return float(time_str[:-1])/60
    elif time_str.endswith('m'):
        return float(time_str[:-1])
    elif time_str.endswith('h'):
        return float(time_str[:-1])*60
    elif time_str.endswith('d'):
        return float(time_str[:-1])*1440
    else:
        try:
            return float(time_str)
        except:
            return None

def format_time(minutes):
    total_seconds = int(minutes*60)
    if total_seconds <= 0:
        return "0s"
    days = total_seconds//86400
    remaining = total_seconds%86400
    hours = remaining//3600
    remaining = remaining%3600
    mins = remaining//60
    secs = remaining%60
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if mins > 0: parts.append(f"{mins}m")
    if secs > 0 and days == 0: parts.append(f"{secs}s")
    return " ".join(parts) if parts else "0s"

def get_premium_reply(user_input, chat_id):
    if chat_id not in user_history:
        user_history[chat_id] = []
    history = user_history[chat_id]
    chat_history = []
    for msg in history[-2:]:
        role = "USER" if msg["role"]=="user" else "CHATBOT"
        chat_history.append({"role":role,"message":msg["content"]})
    try:
        response = co.chat(
            message=user_input,
            chat_history=chat_history,
            preamble=PREMIUM_PREAMBLE,
            temperature=0.5,
            max_tokens=150
        )
        return response.text
    except:
        return "_😅 Fir se bol!_ 💎"

# ================== WELCOME ==================

async def welcome_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members:
        return
    
    chat_id = update.effective_chat.id
    
    for new_user in update.message.new_chat_members:
        if new_user.id == context.bot.id:
            await context.bot.send_message(chat_id=chat_id, text="🤖 *Bot Ready!* 👑 `/activate` 🔥")
            continue
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✨ *Welcome {new_user.first_name}!* 🎉\n💎 AI Reply | 🔇 Mute | ⚡ Fast"
        )

# ================== MUTE ==================

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP*!")
        return
    
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if admin_id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ Sirf *ADMIN*! 👑")
            return
    except:
        await update.message.reply_text("❌ Bot ko *ADMIN* banao!")
        return
    
    target_user = None
    time_str = "1h"
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        if context.args:
            time_str = " ".join(context.args)
    elif context.args and len(context.args) >= 2:
        try:
            target_id = int(context.args[0])
            target_user = (await context.bot.get_chat_member(chat_id, target_id)).user
            time_str = " ".join(context.args[1:])
        except:
            await update.message.reply_text("❌ ID galat!")
            return
    else:
        await update.message.reply_text("🔇 `/mute 10s` `5m` `2h` `1d` `30d`\n🇮🇳 IST | ⏰ Auto")
        return
    
    if not target_user: return
    if target_user.id == admin_id: return
    if target_user.is_bot: return
    
    mute_minutes = parse_time(time_str)
    if mute_minutes is None: return
    if mute_minutes > 43200: return
    if mute_minutes <= 0: return
    
    now_ist = get_ist_now()
    until_ist = now_ist + timedelta(minutes=mute_minutes)
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id, user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=False, can_send_audios=False, can_send_documents=False,
                can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
                can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
                can_add_web_page_previews=False, can_change_info=False,
                can_invite_users=False, can_pin_messages=False
            ),
            until_date=until_ist
        )
        
        target_name = target_user.first_name or "User"
        admin_name = update.effective_user.first_name or "Admin"
        
        await update.message.reply_text(
            f"🔇 *MUTED!* 🇮🇳\n"
            f"👤 {target_name} | 👑 {admin_name}\n"
            f"⏱️ {format_time(mute_minutes)}\n"
            f"🔓 `{until_ist.strftime('%I:%M %p, %d %b')}`\n"
            f"⏰ Auto ON"
        )
        
        async def auto_unmute():
            await asyncio.sleep(mute_minutes * 60)
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat_id, user_id=target_user.id,
                    permissions=ChatPermissions(
                        can_send_messages=True, can_send_audios=True, can_send_documents=True,
                        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                        can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                        can_add_web_page_previews=True, can_change_info=False,
                        can_invite_users=False, can_pin_messages=False
                    )
                )
                await context.bot.send_message(chat_id=chat_id, text=f"✅ *UNMUTED!* {target_name} 💬")
            except: pass
        
        asyncio.create_task(auto_unmute())
        
    except:
        pass

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    
    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        try:
            target_user = (await context.bot.get_chat_member(chat_id, int(context.args[0]))).user
        except: return
    else:
        await update.message.reply_text("🔊 Reply karke `/unmute`")
        return
    
    if not target_user: return
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id, user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True, can_send_audios=True, can_send_documents=True,
                can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                can_add_web_page_previews=True, can_change_info=False,
                can_invite_users=False, can_pin_messages=False
            )
        )
        await update.message.reply_text(f"✅ *UNMUTED!* {target_user.first_name} 💬")
    except: pass

# ================== COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE and user_id == OWNER_USER_ID:
        user_history[chat_id] = []
        await update.message.reply_text("💎 *BOSS!* ⚡\n✅ Fast AI | 🔇 Mute | ⏰ Auto\n/start | /clear | /activate\n_Bolo!_ 🔥")
    elif chat_type == ChatType.PRIVATE:
        await update.message.reply_text("🔒 *PRIVATE!* Group mein add karo.")
    else:
        user_history[chat_id] = []
        await update.message.reply_text("👋 `/activate` karo! 🔥")

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP*!")
        return
    
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ *ADMIN ONLY!*\n1️⃣ Admin banao\n2️⃣ /activate")
            return
    except:
        await update.message.reply_text("❌ Bot ko ADMIN banao!")
        return
    
    active_groups[chat_id] = True
    await update.message.reply_text("✅ *ON!* 🔥\n💬 AI Reply | 🔇 Mute | ⏰ Auto\n❌ /deactivate")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *OFF!* /activate")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_history[update.effective_chat.id] = []
    await update.message.reply_text("✅ Clear!")

# ================== MESSAGE HANDLER ==================

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    user_id = update.effective_user.id
    
    if message.new_chat_members:
        await welcome_new_user(update, context)
        return
    
    # ========== SIRF TEXT ALLOWED ==========
    if not message.text:
        return  # Photo, Video, Sticker, Voice, sab IGNORE
    
    # Private + Group check
    if chat_type == ChatType.PRIVATE and user_id != OWNER_USER_ID:
        await update.message.reply_text("🔒 Group mein add karo!")
        return
    
    if chat_type != ChatType.PRIVATE and (chat_id not in active_groups or not active_groups[chat_id]):
        return
    
    user_input = message.text
    
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        bot_reply = get_premium_reply(user_input, chat_id)
        
        if chat_id not in user_history:
            user_history[chat_id] = []
        user_history[chat_id].append({"role":"user","content":user_input})
        user_history[chat_id].append({"role":"assistant","content":bot_reply})
        user_history[chat_id] = user_history[chat_id][-10:]
        
        await message.reply_text(bot_reply)
    except:
        pass

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("mutelist", lambda u,c: u.message.reply_text("🔇 `/mute 10s` `5m` `2h` `1d`\n🔊 `/unmute`")))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("⚡ GARAM GAND AI — TEXT ONLY")
    print("✅ Sirf Text | 1-2 Sec | Short Reply")
    app.run_polling()

if __name__ == "__main__":
    main()
