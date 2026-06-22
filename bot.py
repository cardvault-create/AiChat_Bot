import os
import asyncio
import requests
import pytz
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== KEYS ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
# ==========================================

# ================== OWNER SETUP ==================
OWNER_USER_ID = 7614459746
# =================================================

IST = pytz.timezone('Asia/Kolkata')

user_history = {}
active_groups = {}
allowed_users = {7614459746}

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
        return "0 seconds"
    days = total_seconds//86400
    remaining = total_seconds%86400
    hours = remaining//3600
    remaining = remaining%3600
    mins = remaining//60
    secs = remaining%60
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days!=1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours!=1 else ''}")
    if mins > 0:
        parts.append(f"{mins} minute{'s' if mins!=1 else ''}")
    if secs > 0 and days == 0:
        parts.append(f"{secs} second{'s' if secs!=1 else ''}")
    return ", ".join(parts) if parts else "0 seconds"

def get_ai_reply(user_input, chat_id):
    """DeepSeek API se reply"""
    if chat_id not in user_history:
        user_history[chat_id] = []
    
    messages = [{
        "role": "system",
        "content": "You are GARAM GAND AI, a helpful, friendly and smart assistant. Reply in user's language. Give accurate answers. Use emojis naturally. Be friendly like a smart friend. For coding give working code. Keep it simple and clean. No markdown formatting."
    }]
    
    history = user_history[chat_id]
    for msg in history[-6:]:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
    
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 600
            },
            timeout=30
        )
        
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return "😅 Fir se try karo!"
    except:
        return "😅 Network issue, fir se bol!"

def is_user_allowed(user_id):
    return user_id in allowed_users

# ================== PERMISSION ==================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ Sirf Owner!")
        return
    
    if not context.args:
        await update.message.reply_text("Use: /adduser user_id")
        return
    
    try:
        new_user_id = int(context.args[0])
        allowed_users.add(new_user_id)
        await update.message.reply_text(f"✅ User {new_user_id} added!")
    except:
        await update.message.reply_text("❌ Valid ID do!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ Sirf Owner!")
        return
    
    if not context.args:
        await update.message.reply_text("Use: /removeuser user_id")
        return
    
    try:
        remove_id = int(context.args[0])
        if remove_id == OWNER_USER_ID:
            await update.message.reply_text("❌ Owner ko nahi!")
            return
        allowed_users.discard(remove_id)
        await update.message.reply_text(f"✅ User {remove_id} removed!")
    except:
        await update.message.reply_text("❌ Valid ID do!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ Sirf Owner!")
        return
    user_list = "\n".join([f"• {uid} {'(Owner)' if uid==OWNER_USER_ID else ''}" for uid in allowed_users])
    await update.message.reply_text(f"👥 Allowed Users:\n\n{user_list}\n\nTotal: {len(allowed_users)}")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        await update.message.reply_text(f"👤 {target.first_name}\n🆔 ID: {target.id}")
    else:
        await update.message.reply_text(f"🆔 Your ID: {update.effective_user.id}")

# ================== WELCOME ==================

async def welcome_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members:
        return
    
    chat_id = update.effective_chat.id
    
    for new_user in update.message.new_chat_members:
        if new_user.id == context.bot.id:
            await context.bot.send_message(chat_id=chat_id, text="🤖 GARAM GAND AI JOINED!\n\n👑 Admin /activate karo\n📢 Phir sabko reply milega!\n\n💻 Coding | 📚 Knowledge | 😂 Fun")
            continue
        
        await context.bot.send_message(chat_id=chat_id, text=f"✨ Welcome {new_user.first_name}! 🎉\n💎 AI Replies | 🔇 Mute | ⚡ Fast")

# ================== MUTE ==================

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf group!")
        return
    
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if admin_id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ Sirf Group Admin!")
            return
    except:
        await update.message.reply_text("❌ Bot ko Admin banao!")
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
        await update.message.reply_text("🔇 /mute 10s 5m 2h 1d 30d\nReply karke!\n🇮🇳 IST | ⏰ Auto")
        return
    
    if not target_user or target_user.id == admin_id or target_user.is_bot: return
    
    mute_minutes = parse_time(time_str)
    if not mute_minutes or mute_minutes > 43200 or mute_minutes <= 0: return
    
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
        if target_user.last_name: target_name += f" {target_user.last_name}"
        admin_name = update.effective_user.first_name or "Admin"
        
        await update.message.reply_text(
            f"🔇 MUTED! 🇮🇳\n\n"
            f"👤 {target_name}\n"
            f"👑 {admin_name}\n"
            f"⏱️ {format_time(mute_minutes)}\n\n"
            f"📅 {now_ist.strftime('%I:%M:%S %p, %d %b %Y')}\n"
            f"🔓 {until_ist.strftime('%I:%M:%S %p, %d %b %Y')}\n\n"
            f"⏰ Auto Unmute ON"
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
                await context.bot.send_message(chat_id=chat_id, text=f"✅ AUTO UNMUTED! {target_name} 🎉")
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
        await update.message.reply_text("🔊 Reply karke /unmute")
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
        await update.message.reply_text(f"✅ UNMUTED! {target_user.first_name} 🎉")
    except: pass

# ================== COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        if is_user_allowed(user_id):
            user_history[chat_id] = []
            await update.message.reply_text(
                "💎 GARAM GAND AI — DeepSeek Powered!\n\n"
                "✅ Most Powerful AI\n"
                "✅ Coding Help 💻\n"
                "✅ Knowledge 📚\n"
                "✅ Fun 😂\n\n"
                "/start | /clear | /id\n\n"
                "Kuch bhi puchho! 🔥"
            )
        else:
            await update.message.reply_text("🔒 Permission nahi hai!")
    else:
        user_history[chat_id] = []
        await update.message.reply_text("👋 Ready! Admin /activate karo")

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf group!")
        return
    
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ Admin only! Bot ko Admin banao phir /activate")
            return
    except:
        await update.message.reply_text("❌ Bot ko Admin banao!")
        return
    
    active_groups[chat_id] = True
    await update.message.reply_text("✅ Activated! 🔥\n💻 Coding | 📚 Knowledge | 😂 Fun\n❌ /deactivate")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 Off! /activate")

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
    
    if chat_type == ChatType.PRIVATE and not is_user_allowed(user_id):
        await update.message.reply_text("🔒 Permission nahi hai!")
        return
    
    if chat_type != ChatType.PRIVATE and (chat_id not in active_groups or not active_groups[chat_id]):
        return
    
    if not message.text:
        return
    
    user_input = message.text
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        bot_reply = get_ai_reply(user_input, chat_id)
        
        if chat_id not in user_history:
            user_history[chat_id] = []
        user_history[chat_id].append({"role":"user","content":user_input})
        user_history[chat_id].append({"role":"assistant","content":bot_reply})
        user_history[chat_id] = user_history[chat_id][-15:]
        
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
    app.add_handler(CommandHandler("mutelist", lambda u,c: u.message.reply_text("🔇 /mute 10s 5m 2h 1d 30d\n🔊 /unmute | ⏰ Auto")))
    app.add_handler(CommandHandler("adduser", adduser))
    app.add_handler(CommandHandler("removeuser", removeuser))
    app.add_handler(CommandHandler("userlist", userlist))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("💎 GARAM GAND AI — DEEPSEEK POWERED")
    print(f"👑 Owner: {OWNER_USER_ID}")
    print("✅ DeepSeek AI | Unlimited | Most Powerful")
    app.run_polling()

if __name__ == "__main__":
    main()
