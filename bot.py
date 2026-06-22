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
OWNER_USERNAME = "@BeStChEaT_OwNeR"
OWNER_NAME = "BEST CHEAT OWNER"
BOT_USERNAME = "@BeStChEaT_OwNeR"
# =================================================

co = cohere.Client(COHERE_API_KEY)

IST = pytz.timezone('Asia/Kolkata')

user_history = {}
active_groups = set()

# ================== PREMIUM STYLISH AI ==================

PREMIUM_PREAMBLE = f"""Tu *GARAM GAND AI Bot* hai — ek *PREMIUM*, *MAST* aur *FUNNY* AI assistant.
Tu {OWNER_NAME} ({OWNER_USERNAME}) ka bot hai.

*TERI PERSONALITY:*
• *Mast*, *funny*, thoda *attitude* wala lekin *RESPECTFUL*
• Har sawal ka *DETAILED*, *ACCURATE* aur *HELPFUL* jawab
• Emojis use kar: 🔥💯😂👊💎⚡🎯❤️🙏🌟✨
• User ki *LANGUAGE* mein jawab de
• *NATURAL* baat kar, robot ki tarah nahi
• Joke sunane ko bole to *REAL FUNNY jokes* de
• Shayari bole to *ORIGINAL SHAYARI* likh
• Code maange to *PROPER WORKING code* de
• Advice maange to *GENUINE HELPFUL advice* de
• Koi bhi topic — *FULL CONFIDENCE* se jawab
• Har baat mein thoda *SWAG*
• *Desi + Classy* mix
• Kabhi boring nahi hona
• Har reply *MEMORABLE* hona chahiye

*TERA REPLY STYLE:*
• *Bold* text use kar important cheeze highlight karne ke liye
• _Italic_ text use kar funny aur stylish feel ke liye
• Emojis ke saath text aur mast lagna chahiye
• Har reply *PREMIUM* aur *STYLISH* dikhna chahiye
• Spacing aur formatting achi honi chahiye
• Reply padhne mein *MAZA* aana chahiye
• Har reply ke end mein apne *OWNER* ka credit dena:

━━━━━━━━━━━━━━━━━━━━━━
👑 *Owner:* {OWNER_NAME}
📩 {OWNER_USERNAME}
━━━━━━━━━━━━━━━━━━━━━━"""

def get_ist_now():
    return datetime.now(IST)

def parse_time(time_str):
    time_str = time_str.lower().strip().replace(" ", "")
    
    if not time_str:
        return None
    
    if 'seconds' in time_str or time_str.endswith('second') or time_str.endswith('sec'):
        num = time_str.replace('seconds', '').replace('second', '').replace('sec', '')
        return float(num) / 60 if num else None
    elif 'minutes' in time_str or time_str.endswith('minute') or time_str.endswith('mins') or time_str.endswith('min'):
        num = time_str.replace('minutes', '').replace('minute', '').replace('mins', '').replace('min', '')
        return float(num) if num else None
    elif 'hours' in time_str or time_str.endswith('hour') or time_str.endswith('hrs') or time_str.endswith('hr'):
        num = time_str.replace('hours', '').replace('hour', '').replace('hrs', '').replace('hr', '')
        return float(num) * 60 if num else None
    elif 'days' in time_str or time_str.endswith('day'):
        num = time_str.replace('days', '').replace('day', '')
        return float(num) * 1440 if num else None
    elif time_str.endswith('s'):
        return float(time_str[:-1]) / 60
    elif time_str.endswith('m'):
        return float(time_str[:-1])
    elif time_str.endswith('h'):
        return float(time_str[:-1]) * 60
    elif time_str.endswith('d'):
        return float(time_str[:-1]) * 1440
    else:
        try:
            return float(time_str)
        except:
            return None

def format_time(minutes):
    total_seconds = int(minutes * 60)
    
    if total_seconds <= 0:
        return "0 seconds"
    
    days = total_seconds // 86400
    remaining = total_seconds % 86400
    hours = remaining // 3600
    remaining = remaining % 3600
    mins = remaining // 60
    secs = remaining % 60
    
    parts = []
    if days > 0:
        parts.append(f"*{days}* day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"*{hours}* hour{'s' if hours != 1 else ''}")
    if mins > 0:
        parts.append(f"*{mins}* minute{'s' if mins != 1 else ''}")
    if secs > 0 and days == 0:
        parts.append(f"*{secs}* second{'s' if secs != 1 else ''}")
    
    return ", ".join(parts) if parts else "0 seconds"

def get_premium_reply(user_input, chat_id):
    if chat_id not in user_history:
        user_history[chat_id] = []
    
    history = user_history[chat_id]
    chat_history = []
    for msg in history[-8:]:
        role = "USER" if msg["role"] == "user" else "CHATBOT"
        chat_history.append({"role": role, "message": msg["content"]})
    
    try:
        response = co.chat(
            message=user_input,
            chat_history=chat_history,
            preamble=PREMIUM_PREAMBLE,
            temperature=0.95,
            max_tokens=500
        )
        return response.text
    except:
        return f"_😅 Thoda sa ruk ja bhai, fir se bol!_ 💎\n\n━━━━━━━━━━━━━━━━━━━━━━\n👑 *Owner:* {OWNER_NAME}\n📩 {OWNER_USERNAME}\n━━━━━━━━━━━━━━━━━━━━━━"

# ================== WELCOME NEW USERS ==================

async def welcome_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    if chat_type == ChatType.PRIVATE:
        return
    
    if update.message.new_chat_members:
        for new_user in update.message.new_chat_members:
            if new_user.id == context.bot.id:
                continue
            
            user_name = new_user.first_name or "User"
            if new_user.last_name:
                user_name += f" {new_user.last_name}"
            
            welcome_text = (
                f"✨ *WELCOME TO THE GROUP!* ✨\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *{user_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌟 _Aapka swagat hai hamare group mein!_ 🎉\n\n"
                f"💎 Yahaan aapko milega:\n"
                f"   • *Premium AI Replies* 🔥\n"
                f"   • *Mast Mazaak* 😂\n"
                f"   • *Full Entertainment* ⚡\n"
                f"   • *Mute System* 🔇\n\n"
                f"🤖 *Bot:* {BOT_USERNAME}\n"
                f"👑 *Owner:* {OWNER_NAME}\n"
                f"📩 {OWNER_USERNAME}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📢 Kuch bhi puchho, bhejo —\n"
                f"   *GARAM GAND AI* jawab dega! 💬\n\n"
                f"🔰 _Group mein enjoy karo!_ 🤗"
            )
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=welcome_text,
                parse_mode="Markdown"
            )

# ================== MUTE SYSTEM ==================

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP* mein chalta hai!", parse_mode="Markdown")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, admin_id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Sirf *GROUP ADMIN* mute kar sakta hai! 👑", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ Bot ko *admin rights* do pehle!", parse_mode="Markdown")
        return
    
    target_user = None
    time_str = "1h"
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        if context.args:
            time_str = " ".join(context.args)
    elif context.args:
        if len(context.args) >= 2:
            try:
                target_id = int(context.args[0])
                target_user = await context.bot.get_chat_member(chat_id, target_id)
                target_user = target_user.user
                time_str = " ".join(context.args[1:])
            except:
                await update.message.reply_text("❌ User ID galat ya user group mein nahi!")
                return
        else:
            await update.message.reply_text(
                "🔇 *MUTE USAGE* 🇮🇳\n\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "📌 *Reply karke:*\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "`/mute 10 second`\n"
                "`/mute 5 minute`\n"
                "`/mute 2 hour`\n"
                "`/mute 1 day`\n\n"
                "📌 *Short format:*\n"
                "`/mute 25s` `/mute 5m`\n"
                "`/mute 2h` `/mute 1d`\n"
                "`/mute 30d` (max)\n\n"
                "📌 *Manual:*\n"
                "`/mute user_id 10 minute`\n\n"
                "🇮🇳 IST Time | ⏰ Auto Unmute\n"
                f"👑 *Owner:* {OWNER_USERNAME}",
                parse_mode="Markdown"
            )
            return
    
    if not target_user:
        await update.message.reply_text("❌ User nahi mila! Message ko reply karo.")
        return
    
    if target_user.id == admin_id:
        await update.message.reply_text("😅 Khud ko mute nahi kar sakte!")
        return
    
    if target_user.is_bot:
        await update.message.reply_text("🤖 Bot ko mute nahi kar sakte!")
        return
    
    mute_minutes = parse_time(time_str)
    if mute_minutes is None:
        await update.message.reply_text(
            "❌ Time format galat!\n"
            "Use: `10 second`, `5 minute`, `2 hour`, `1 day`, `25s`, `5m`, `2h`, `1d`",
            parse_mode="Markdown"
        )
        return
    
    if mute_minutes > 43200:
        await update.message.reply_text("❌ Max *30 days* tak mute kar sakte ho!", parse_mode="Markdown")
        return
    
    if mute_minutes <= 0:
        await update.message.reply_text("❌ Time 0 se zyada do!")
        return
    
    now_ist = get_ist_now()
    until_ist = now_ist + timedelta(minutes=mute_minutes)
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            ),
            until_date=until_ist
        )
        
        target_name = target_user.first_name or "User"
        if target_user.last_name:
            target_name += f" {target_user.last_name}"
        admin_name = update.effective_user.first_name or "Admin"
        
        await update.message.reply_text(
            f"🔇 *MUTED! — INDIA TIME* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {target_name}\n"
            f"🆔 ID: `{target_user.id}`\n"
            f"👑 *By:* {admin_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ *Duration:* {format_time(mute_minutes)}\n\n"
            f"📅 *Muted at:*\n"
            f"   🕐 `{now_ist.strftime('%I:%M:%S %p')}`\n"
            f"   📆 {now_ist.strftime('%d %B %Y')}\n\n"
            f"🔓 *Unmute at:*\n"
            f"   🕐 `{until_ist.strftime('%I:%M:%S %p')}`\n"
            f"   📆 {until_ist.strftime('%d %B %Y')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ Time khatam hone par *AUTO UNMUTE* hoga!\n"
            f"🔊 Ya `/unmute` reply karke manual unmute\n\n"
            f"👑 *Owner:* {OWNER_USERNAME}",
            parse_mode="Markdown"
        )
        
        async def auto_unmute():
            await asyncio.sleep(mute_minutes * 60)
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=target_user.id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_audios=True,
                        can_send_documents=True,
                        can_send_photos=True,
                        can_send_videos=True,
                        can_send_video_notes=True,
                        can_send_voice_notes=True,
                        can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False
                    )
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ *AUTO UNMUTED!* 🇮🇳\n\n"
                         f"👤 *{target_name}*\n"
                         f"⏱️ {format_time(mute_minutes)} ka mute khatam!\n"
                         f"💬 _Ab message kar sakta hai!_ 🎉\n\n"
                         f"👑 *Owner:* {OWNER_USERNAME}",
                    parse_mode="Markdown"
                )
            except:
                pass
        
        asyncio.create_task(auto_unmute())
        
    except Exception as e:
        await update.message.reply_text(f"❌ Mute fail! Permissions check karo.\n`{str(e)[:80]}`")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP* mein chalta hai!", parse_mode="Markdown")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, admin_id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Sirf *GROUP ADMIN* unmute kar sakta hai! 👑", parse_mode="Markdown")
            return
    except:
        return
    
    target_user = None
    
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        try:
            target_id = int(context.args[0])
            target_user = await context.bot.get_chat_member(chat_id, target_id)
            target_user = target_user.user
        except:
            await update.message.reply_text("❌ User ID galat!")
            return
    else:
        await update.message.reply_text("🔊 *UNMUTE:* Kisi message ko reply karke `/unmute` bhejo", parse_mode="Markdown")
        return
    
    if not target_user:
        await update.message.reply_text("❌ User nahi mila!")
        return
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
        )
        
        now_ist = get_ist_now()
        target_name = target_user.first_name or "User"
        
        await update.message.reply_text(
            f"✅ *UNMUTED!* 🇮🇳\n\n"
            f"👤 *User:* {target_name}\n"
            f"🔓 *At:* `{now_ist.strftime('%I:%M:%S %p, %d %B %Y')}`\n\n"
            f"💬 _Ab message kar sakta hai!_ 🎉\n\n"
            f"👑 *Owner:* {OWNER_USERNAME}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Unmute fail: `{str(e)[:80]}`")

async def mutelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔇 *MUTE HELP* 🇮🇳\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *MUTE (reply karke):*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "`/mute 10 second` | `25s`\n"
        "`/mute 5 minute` | `5m`\n"
        "`/mute 2 hour` | `2h`\n"
        "`/mute 1 day` | `1d`\n"
        "`/mute 30d` (max)\n\n"
        "📌 *UNMUTE:* `/unmute` reply\n"
        "📌 *Manual:* `/mute ID time`\n\n"
        "⏰ *Auto Unmute* ON\n"
        "👑 Admin only | 🇮🇳 IST Time\n\n"
        f"👑 *Owner:* {OWNER_USERNAME}",
        parse_mode="Markdown"
    )

# ================== BASIC COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type != ChatType.PRIVATE:
        user_history[chat_id] = []
        await update.message.reply_text(
            "👋 *GARAM GAND AI READY!* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 *Admin Commands:*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔘 /activate — Bot ON\n"
            "🔇 /mute — Mute user\n"
            "🔊 /unmute — Unmute\n"
            "📋 /mutelist — Help\n\n"
            "✨ *Features:*\n"
            "• ⏰ Auto Unmute\n"
            "• 💬 Premium AI Reply\n"
            "• 👋 New User Welcome\n\n"
            f"👑 *Owner:* {OWNER_NAME}\n"
            f"📩 {OWNER_USERNAME}\n\n"
            "_Activate karo, phir enjoy karo!_ 🔥",
            parse_mode="Markdown"
        )
        return
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text(
            "🔒 *PRIVATE BOT* 🔒\n\n"
            "_Ye bot sirf *OWNER* ke liye hai!_ 👑\n\n"
            "💡 *Group mein add karo* —\n"
            "   wahan sabko premium reply milega!\n"
            "   New users ka welcome bhi hoga! ✨\n\n"
            f"👑 *Owner:* {OWNER_NAME}\n"
            f"📩 {OWNER_USERNAME}",
            parse_mode="Markdown"
        )
        return
    
    user_history[chat_id] = []
    await update.message.reply_text(
        "💎 *WELCOME BACK BOSS!* 💎\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 *PREMIUM SYSTEMS ACTIVE:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ *Premium AI Replies*\n"
        "✅ *Stylish Bold+Italic Text*\n"
        "✅ *Mute System (IST)* 🇮🇳\n"
        "✅ *Auto Unmute* ⏰\n"
        "✅ *New User Welcome* 👋\n"
        "✅ *All Media Support* 🖼️\n"
        "✅ *Private Lock* 🔒\n"
        "✅ *Owner Credit in Replies* 📩\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ *COMMANDS:*\n"
        "/start | /clear | /activate\n"
        "/mute | /unmute | /mutelist\n\n"
        f"👑 *Owner:* {OWNER_NAME}\n"
        f"📩 {OWNER_USERNAME}\n\n"
        "_Bolo boss, kya chahiye?_ 🔥",
        parse_mode="Markdown"
    )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP* mein!", parse_mode="Markdown")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.add(chat_id)
            user_history[chat_id] = []
            await update.message.reply_text(
                "✅ *GROUP ACTIVATED!* 🔥\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌟 *AB SAB KUCH ON:*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💬 *Premium AI Replies*\n"
                "🔇 *Mute System*\n"
                "⏰ *Auto Unmute*\n"
                "👋 *New User Welcome*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📢 _Sab kuch bhejo —_\n"
                "   _GARAM GAND jawab dega!_ 💎\n\n"
                f"👑 *Owner:* {OWNER_NAME}\n"
                f"📩 {OWNER_USERNAME}\n\n"
                "❌ /deactivate — Band karo",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Sirf *ADMIN*!", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Bot ko *admin* banao!", parse_mode="Markdown")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP*!", parse_mode="Markdown")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.discard(chat_id)
            await update.message.reply_text(
                "🔴 *GROUP DEACTIVATED!*\n"
                "_/activate se wapas on karo_",
                parse_mode="Markdown"
            )
    except:
        pass

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text("✅ *Memory Clear!* 💭", parse_mode="Markdown")

# ================== MESSAGE HANDLER ==================

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    user_id = update.effective_user.id
    
    # New user welcome
    if message.new_chat_members:
        await welcome_new_user(update, context)
        for new_user in message.new_chat_members:
            if new_user.id == context.bot.id:
                return
    
    if chat_type == ChatType.PRIVATE and user_id != OWNER_USER_ID:
        await update.message.reply_text(
            "🔒 *PRIVATE BOT* 🔒\n\n"
            "_Private mein sirf *OWNER* use kar sakta hai!_ 👑\n\n"
            "💡 Mujhe *GROUP* mein add karo —\n"
            "   wahan *SABKO* premium reply milega!\n"
            "   New users ka welcome bhi hoga! ✨\n\n"
            f"👑 *Owner:* {OWNER_NAME}\n"
            f"📩 {OWNER_USERNAME}",
            parse_mode="Markdown"
        )
        return
    
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    if message.text:
        user_input = message.text
    elif message.caption:
        if message.photo:
            user_input = f"🖼️ *[PHOTO]* — {message.caption}"
        elif message.video:
            user_input = f"🎬 *[VIDEO]* — {message.caption}"
        elif message.document:
            user_input = f"📄 *[DOCUMENT]* — {message.caption}"
        else:
            user_input = f"📨 *[Media]* — {message.caption}"
    elif message.photo:
        user_input = "🖼️ _Photo bheji hai — iska mazedaar aur stylish reaction de_"
    elif message.video:
        user_input = "🎬 _Video bheja hai — iska mazedaar aur stylish reaction de_"
    elif message.sticker:
        emoji = message.sticker.emoji or ""
        user_input = f"🎯 _Sticker bheja hai {emoji} — ispe funny aur stylish reaction de_"
    elif message.voice:
        user_input = "🎵 _Voice message bheja hai — funny aur stylish comment kar_"
    elif message.audio:
        user_input = "🎧 _Audio bheja hai — music pe stylish baat kar_"
    elif message.document:
        doc_name = message.document.file_name or "file"
        user_input = f"📄 _Document bheja hai: *{doc_name}* — iske baare mein stylish bol_"
    elif message.animation:
        user_input = "🎞️ _GIF bheja hai — mazedaar aur stylish reaction de_"
    elif message.video_note:
        user_input = "📹 _Video note bheja hai — funny stylish comment_"
    elif message.location:
        user_input = "📍 _Location bheji hai — stylish puchho kahan ho_"
    elif message.contact:
        user_input = "👤 _Contact share kiya hai — mazedaar stylish comment_"
    elif message.poll:
        user_input = "📊 _Poll banaya hai — stylish vote karne ko bol_"
    else:
        user_input = "📨 _Kuch bheja hai — curious stylish reaction de_"

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        bot_reply = get_premium_reply(user_input, chat_id)
        
        if chat_id not in user_history:
            user_history[chat_id] = []
        user_history[chat_id].append({"role": "user", "content": user_input})
        user_history[chat_id].append({"role": "assistant", "content": bot_reply})
        user_history[chat_id] = user_history[chat_id][-30:]
        
        await message.reply_text(bot_reply, parse_mode="Markdown")
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
    app.add_handler(CommandHandler("mutelist", mutelist))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("💎 GARAM GAND AI — PREMIUM STYLISH BOT")
    print(f"👑 Owner: {OWNER_NAME} ({OWNER_USERNAME})")
    print(f"🆔 Owner ID: {OWNER_USER_ID}")
    print("👋 New User Welcome | ⏰ Auto Unmute")
    print("🔇 Mute | 🔊 Unmute | 💬 Premium AI")
    app.run_polling()

if __name__ == "__main__":
    main()
