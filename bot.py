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

PREMIUM_PREAMBLE = """Tu ek PREMIUM AI Assistant hai — GARAM GAND AI Bot.

TERI PERSONALITY:
• Mast, funny, thoda attitude wala lekin RESPECTFUL
• Har sawal ka DETAILED, ACCURATE aur HELPFUL jawab
• Emojis use kar: 🔥💯😂👊💎⚡🎯❤️🙏🌟✨👑
• User ki LANGUAGE mein jawab de
• NATURAL baat kar, robot ki tarah nahi
• Joke sunane ko bole to REAL FUNNY jokes de
• Shayari bole to ORIGINAL SHAYARI likh
• Code maange to PROPER WORKING code de
• Advice maange to GENUINE HELPFUL advice de
• Koi bhi topic — FULL CONFIDENCE se jawab
• Har baat mein thoda SWAG
• Desi + Classy mix
• Kabhi boring nahi hona
• Har reply MEMORABLE hona chahiye

TERA REPLY STYLE (BOHOT IMPORTANT):
• *Bold* text use kar IMPORTANT cheeze highlight karne ke liye — is tarah: *yeh important hai*
• _Italic_ text use kar FUNNY aur STYLISH feel ke liye — is tarah: _yeh funny hai_
• Emojis ke saath text aur MAST lagna chahiye
• Har reply PREMIUM aur STYLISH dikhna chahiye
• Spacing aur FORMATTING achi honi chahiye
• Reply padhne mein MAZA aana chahiye
• LINES aur DIVIDERS use kar sections separate karne ke liye
• Har reply COMPLETE aur DETAILED hona chahiye
• Adha-adhura jawab KABHI mat dena
• Agar koi PUCHHTA hai to POORA jawab de
• Agar koi PHOTO bhejta hai to USKA REACTION de
• Agar koi STICKER bhejta hai to FUNNY REACTION de
• Agar koi EMOTIONAL baat kare to UNDERSTANDING dikha
• Har reply ke end mein ek MAST sign-off de"""

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
        parts.append(f"*{days}* day{'s' if days!=1 else ''}")
    if hours > 0:
        parts.append(f"*{hours}* hour{'s' if hours!=1 else ''}")
    if mins > 0:
        parts.append(f"*{mins}* minute{'s' if mins!=1 else ''}")
    if secs > 0 and days == 0:
        parts.append(f"*{secs}* second{'s' if secs!=1 else ''}")
    return ", ".join(parts) if parts else "0 seconds"

def get_premium_reply(user_input, chat_id):
    if chat_id not in user_history:
        user_history[chat_id] = []
    history = user_history[chat_id]
    chat_history = []
    for msg in history[-10:]:
        role = "USER" if msg["role"]=="user" else "CHATBOT"
        chat_history.append({"role":role,"message":msg["content"]})
    try:
        response = co.chat(
            message=user_input,
            chat_history=chat_history,
            preamble=PREMIUM_PREAMBLE,
            temperature=0.95,
            max_tokens=600
        )
        return response.text
    except:
        return "_😅 Thoda sa ruk ja bhai, fir se bol!_ 💎\n\n━━━━━━━━━━━━━━━━━━━━━━\n✨ _GARAM GAND AI_ ✨"

# ================== WELCOME ==================

async def welcome_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members:
        return
    
    chat_id = update.effective_chat.id
    
    for new_user in update.message.new_chat_members:
        if new_user.id == context.bot.id:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🤖 *GARAM GAND AI JOINED!* 💎\n\n"
                     "━━━━━━━━━━━━━━━━━━━━━━\n"
                     "👑 Admin `/activate` karo\n"
                     "📢 Phir sabko *PREMIUM REPLY* milega!\n"
                     "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                     "🔥 _Bot ready hai — activate karo!_",
                parse_mode="Markdown"
            )
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
            f"💎 *Yahaan aapko milega:*\n"
            f"   • *Premium AI Replies* 🔥\n"
            f"   • *Mute System* 🔇\n"
            f"   • *Auto Unmute* ⏰\n"
            f"   • *Full Entertainment* ⚡\n\n"
            f"📢 Kuch bhi puchho, bhejo —\n"
            f"   *GARAM GAND AI* jawab dega! 💬\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔰 _Group mein enjoy karo!_ 🤗"
        )
        await context.bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode="Markdown")

# ================== MUTE ==================

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP* mein chalta hai!", parse_mode="Markdown")
        return
    
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if admin_id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ Sirf *GROUP ADMIN* mute kar sakta hai! 👑", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ Bot ko *ADMIN* banao pehle!", parse_mode="Markdown")
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
            await update.message.reply_text("❌ User ID galat!")
            return
    else:
        await update.message.reply_text(
            "🔇 *MUTE USAGE* 🇮🇳\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Reply karke:*\n"
            "`/mute 10 second` | `/mute 5 minute`\n"
            "`/mute 2 hour` | `/mute 1 day`\n\n"
            "📌 *Short format:*\n"
            "`/mute 25s` | `5m` | `2h` | `1d`\n"
            "`/mute 30d` (max)\n\n"
            "🇮🇳 IST Time | ⏰ Auto Unmute",
            parse_mode="Markdown"
        )
        return
    
    if not target_user:
        await update.message.reply_text("❌ User nahi mila! Message ko reply karo.")
        return
    if target_user.id == admin_id:
        await update.message.reply_text("😅 _Khud ko mute nahi kar sakte bhai!_")
        return
    if target_user.is_bot:
        await update.message.reply_text("🤖 _Bot ko mute nahi kar sakte!_")
        return
    
    mute_minutes = parse_time(time_str)
    if mute_minutes is None:
        await update.message.reply_text("❌ Time: `10 second`, `5 minute`, `25s`, `5m`, `2h`, `1d`", parse_mode="Markdown")
        return
    if mute_minutes > 43200:
        await update.message.reply_text("❌ Max *30 days*!", parse_mode="Markdown")
        return
    if mute_minutes <= 0:
        await update.message.reply_text("❌ Time 0 se zyada do!")
        return
    
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
            f"🔇 *MUTED! — INDIA TIME* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {target_name}\n"
            f"🆔 ID: `{target_user.id}`\n"
            f"👑 *By:* {admin_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ *Duration:* {format_time(mute_minutes)}\n\n"
            f"📅 *Muted at:*\n"
            f"   🕐 `{now_ist.strftime('%I:%M:%S %p')}` — {now_ist.strftime('%d %b %Y')}\n\n"
            f"🔓 *Unmute at:*\n"
            f"   🕐 `{until_ist.strftime('%I:%M:%S %p')}` — {until_ist.strftime('%d %b %Y')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ *Auto Unmute* ON hai!\n"
            f"🔊 Ya `/unmute` reply karke",
            parse_mode="Markdown"
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
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ *AUTO UNMUTED!* 🇮🇳\n\n"
                         f"👤 *{target_name}*\n"
                         f"⏱️ {format_time(mute_minutes)} ka mute khatam!\n"
                         f"💬 _Ab message kar sakta hai!_ 🎉",
                    parse_mode="Markdown"
                )
            except: pass
        
        asyncio.create_task(auto_unmute())
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Mute fail!*\n\n"
            f"⚠️ Bot ko yeh permissions do:\n"
            f"✅ Ban Users ✅ Delete Messages\n\n"
            f"`{str(e)[:80]}`",
            parse_mode="Markdown"
        )

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP* mein!", parse_mode="Markdown")
        return
    
    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        try:
            target_user = (await context.bot.get_chat_member(chat_id, int(context.args[0]))).user
        except:
            await update.message.reply_text("❌ ID galat!")
            return
    else:
        await update.message.reply_text("🔊 Reply karke `/unmute` bhejo", parse_mode="Markdown")
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
        now_ist = get_ist_now()
        await update.message.reply_text(
            f"✅ *UNMUTED!* 🇮🇳\n\n"
            f"👤 *{target_user.first_name}*\n"
            f"🔓 `{now_ist.strftime('%I:%M:%S %p, %d %b %Y')}`\n\n"
            f"💬 _Ab message kar sakta hai!_ 🎉",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ `{str(e)[:80]}`")

async def mutelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔇 *MUTE HELP* 🇮🇳\n\n"
        "`/mute 10 second` | `25s`\n"
        "`/mute 5 minute` | `5m`\n"
        "`/mute 2 hour` | `2h`\n"
        "`/mute 1 day` | `1d`\n"
        "`/mute 30d` (max)\n\n"
        "🔊 `/unmute` reply | ⏰ Auto Unmute",
        parse_mode="Markdown"
    )

# ================== COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE and user_id == OWNER_USER_ID:
        user_history[chat_id] = []
        await update.message.reply_text(
            "💎 *WELCOME BACK BOSS!* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 *PREMIUM SYSTEMS ACTIVE:*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ *Premium AI Replies* (Bold+Italic)\n"
            "✅ *Mute System* 🇮🇳\n"
            "✅ *Auto Unmute* ⏰\n"
            "✅ *New User Welcome* 👋\n"
            "✅ *All Media Support* 🖼️🎬🎯🎵\n"
            "✅ *Private Lock* 🔒\n\n"
            "⚡ *COMMANDS:*\n"
            "/start | /clear | /activate\n"
            "/mute | /unmute | /mutelist\n\n"
            "_Bolo boss, kya chahiye?_ 🔥\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✨ _GARAM GAND AI_ ✨",
            parse_mode="Markdown"
        )
    elif chat_type == ChatType.PRIVATE:
        await update.message.reply_text(
            "🔒 *PRIVATE BOT* 🔒\n\n"
            "_Ye bot sirf OWNER ke liye hai!_ 👑\n\n"
            "💡 *Group mein add karo* —\n"
            "   wahan *SABKO* premium reply milega!\n"
            "   New users ka welcome bhi hoga! ✨",
            parse_mode="Markdown"
        )
    else:
        user_history[chat_id] = []
        await update.message.reply_text(
            "👋 *GARAM GAND AI READY!* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 Admin `/activate` karo\n"
            "🔇 `/mute` | 🔊 `/unmute`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "_Activate karo, phir enjoy karo!_ 🔥",
            parse_mode="Markdown"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP* mein!", parse_mode="Markdown")
        return
    
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text(
                "❌ *Sirf GROUP ADMIN!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 *STEPS:*\n"
                "1️⃣ Bot ko *ADMIN* banao\n"
                "2️⃣ Sab *permissions ON* karo\n"
                "3️⃣ Phir `/activate` bhejo\n"
                "━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode="Markdown"
            )
            return
    except:
        await update.message.reply_text("❌ Bot ko *ADMIN* banao pehle!", parse_mode="Markdown")
        return
    
    active_groups[chat_id] = True
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
        "📢 _Sab kuch bhejo —_\n"
        "   _GARAM GAND jawab dega!_ 💎\n\n"
        "❌ /deactivate",
        parse_mode="Markdown"
    )

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *DEACTIVATED!* /activate", parse_mode="Markdown")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_history[update.effective_chat.id] = []
    await update.message.reply_text("✅ *Memory Clear!* 💭", parse_mode="Markdown")

# ================== MESSAGE HANDLER ==================

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    user_id = update.effective_user.id
    
    if message.new_chat_members:
        await welcome_new_user(update, context)
        return
    
    if chat_type == ChatType.PRIVATE:
        if user_id != OWNER_USER_ID:
            await update.message.reply_text(
                "🔒 *PRIVATE BOT* 🔒\n\n"
                "_Private mein sirf OWNER use kar sakta hai!_ 👑\n\n"
                "💡 Mujhe *GROUP* mein add karo —\n"
                "   wahan *SABKO* premium reply milega! ✨",
                parse_mode="Markdown"
            )
            return
    else:
        if chat_id not in active_groups or not active_groups[chat_id]:
            return
    
    # ========== MESSAGE DETECTION ==========
    if message.text:
        user_input = message.text
    elif message.caption:
        if message.photo:
            user_input = f"🖼️ *[PHOTO]* with caption: _{message.caption}_ — is photo ka mazedaar aur detailed reaction de, compliment kar, guess kar kya hai, aur emojis use kar"
        elif message.video:
            user_input = f"🎬 *[VIDEO]* with caption: _{message.caption}_ — is video ka mazedaar reaction de, curious ho"
        elif message.document:
            user_input = f"📄 *[DOCUMENT]* with caption: _{message.caption}_ — is document ke baare mein baat kar"
        else:
            user_input = f"📨 *[Media]* with caption: _{message.caption}_"
    elif message.photo:
        user_input = "🖼️ *Photo bheji hai* — iska *detailed* aur *stylish* reaction de. Compliment kar, guess kar, emojis use kar, mast reply de."
    elif message.video:
        user_input = "🎬 *Video bheja hai* — iska *detailed* aur *stylish* reaction de. Curious ho, guess kar content, emojis use kar."
    elif message.sticker:
        emoji = message.sticker.emoji or "❓"
        user_input = f"🎯 *Sticker bheja hai* Emoji: {emoji} — ispe *FUNNY* aur *OVER-THE-TOP* reaction de. Sticker ke emotion ke hisaab se mazedaar jawab de."
    elif message.voice:
        user_input = "🎵 *Voice message bheja hai* — iska *funny* aur *stylish* comment kar. 'Voice note sun liya' type ka mazedaar reply de."
    elif message.audio:
        user_input = "🎧 *Audio bheja hai* — music pe *stylish* baat kar, gaane ke baare mein guess kar."
    elif message.document:
        doc_name = message.document.file_name or "file"
        user_input = f"📄 *Document bheja hai:* _{doc_name}_ — iske baare mein *detailed* aur *stylish* bol, guess kar kya ho sakta hai."
    elif message.animation:
        user_input = "🎞️ *GIF bheja hai* — iska *mazedaar* aur *stylish* reaction de, funny comment kar."
    elif message.video_note:
        user_input = "📹 *Video note bheja hai* — iska *funny stylish* comment kar."
    elif message.location:
        user_input = "📍 *Location bheji hai* — *stylish* puchho kahan ho, mazedaar guess kar."
    elif message.contact:
        user_input = "👤 *Contact share kiya hai* — *mazedaar stylish* comment kar."
    elif message.poll:
        user_input = "📊 *Poll banaya hai* — *stylish* vote karne ko bol, funny comment kar."
    else:
        user_input = "📨 *Kuch bheja hai* — *curious stylish* reaction de."

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        bot_reply = get_premium_reply(user_input, chat_id)
        
        if chat_id not in user_history:
            user_history[chat_id] = []
        user_history[chat_id].append({"role":"user","content":user_input})
        user_history[chat_id].append({"role":"assistant","content":bot_reply})
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
    
    print("💎 GARAM GAND AI — ULTIMATE PREMIUM")
    print(f"👑 Owner ID: {OWNER_USER_ID}")
    print("✅ Bold+Italic | Mute | Auto Unmute | Welcome")
    app.run_polling()

if __name__ == "__main__":
    main()
