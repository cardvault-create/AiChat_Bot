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

PREMIUM_PREAMBLE = """Tu GARAM GAND AI Bot hai — MAST, FUNNY, SMART AI.

TERA STYLE:
• Jo puche uska SAHI jawab de — lekin FUNNY andaaz mein
• *Bold* kar important words, _Italic_ kar funny parts
• Emojis use kar: 🔥💯😂👊💎⚡🎯❤️✨🤣😎
• JAWAB SAHI HO — information accurate rakhiyo
• Lekin bolne ka STYLE funny aur entertaining rakh
• Jaise dost se baat kar raha hai waise bol
• Thoda attitude, thoda humor, poora knowledge
• Lamba mat bol — 2-4 line mein kaam khatam kar

EXAMPLES:
Q: India ki capital kya hai?
A: _Arey bhai!_ *Delhi* hai! 🇮🇳 Dilli ka dilwala! 😎🔥

Q: 2+2 kitna hota hai?
A: *4* mere genius dost! 🧮😂 Itna easy tha ki calculator bhi sharma gaya! 💯

Q: Who is PM of India?
A: *Narendra Modi ji*! 🇮🇳 Desh ke pradhan mantri, sabke bhai! 👑✨

Q: Mujhe sad feel ho raha hai
A: _Arey bhai!_ 😢 *Tension mat le!* Zindagi mein ups and downs aate hain. Tere saath hoon! 🤗💪"""

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
    for msg in history[-4:]:
        role = "USER" if msg["role"]=="user" else "CHATBOT"
        chat_history.append({"role":role,"message":msg["content"]})
    try:
        response = co.chat(
            message=user_input,
            chat_history=chat_history,
            preamble=PREMIUM_PREAMBLE,
            temperature=0.85,
            max_tokens=200
        )
        return response.text
    except:
        return "_😅 Fir se bol bhai!_ 💎"

# ================== WELCOME ==================

async def welcome_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members:
        return
    
    chat_id = update.effective_chat.id
    
    for new_user in update.message.new_chat_members:
        if new_user.id == context.bot.id:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🤖 *GARAM GAND AI AA GAYA!* 🔥\n\n"
                     "━━━━━━━━━━━━━━━━━━━━━━\n"
                     "👑 Admin `/activate` karo\n"
                     "📢 Phir sabko *FUNNY REPLY* milega!\n"
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
            f"🌟 _Aapka swagat hai!_ 🎉\n\n"
            f"💎 *Yahaan aapko milega:*\n"
            f"   • *Funny AI Replies* 😂\n"
            f"   • *Mute System* 🔇\n"
            f"   • *Auto Unmute* ⏰\n"
            f"   • *Full Entertainment* ⚡\n\n"
            f"📢 Kuch bhi puchho —\n"
            f"   *GARAM GAND AI* jawab dega! 💬\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔰 _Group mein enjoy karo!_ 🤗"
        )
        await context.bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode="Markdown")

# ================== MUTE SYSTEM ==================

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP* mein chalta hai!")
        return
    
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if admin_id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ Sirf *GROUP ADMIN* mute kar sakta hai! 👑")
            return
    except:
        await update.message.reply_text("❌ Bot ko *ADMIN* banao pehle!")
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
            "━━━━━━━━━━━━━━━━━━━\n"
            "`/mute 10 second`\n"
            "`/mute 5 minute`\n"
            "`/mute 2 hour`\n"
            "`/mute 1 day`\n\n"
            "📌 *Short format:*\n"
            "`/mute 25s` `/mute 5m`\n"
            "`/mute 2h` `/mute 1d`\n"
            "`/mute 30d` (max)\n\n"
            "🇮🇳 IST Time | ⏰ Auto Unmute",
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
        await update.message.reply_text("❌ Time format galat! Use: `10 second`, `5 minute`, `25s`, `5m`, `2h`, `1d`")
        return
    if mute_minutes > 43200:
        await update.message.reply_text("❌ Max *30 days* tak mute kar sakte ho!")
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
        if target_user.last_name:
            target_name += f" {target_user.last_name}"
        admin_name = update.effective_user.first_name or "Admin"
        
        await update.message.reply_text(
            f"🔇 *MUTED! — INDIA TIME* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {target_name}\n"
            f"🆔 ID: `{target_user.id}`\n"
            f"👑 *Muted by:* {admin_name}\n"
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
            f"🔊 Ya `/unmute` reply karke manual unmute",
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
                         f"━━━━━━━━━━━━━━━━━━━━━━\n"
                         f"👤 *User:* {target_name}\n"
                         f"⏱️ *Duration:* {format_time(mute_minutes)}\n"
                         f"🔓 *Unmuted at:*\n"
                         f"   🕐 `{get_ist_now().strftime('%I:%M:%S %p')}`\n"
                         f"   📆 {get_ist_now().strftime('%d %B %Y')}\n"
                         f"━━━━━━━━━━━━━━━━━━━━━━\n"
                         f"💬 _Ab message kar sakta hai!_ 🎉",
                    parse_mode="Markdown"
                )
            except:
                pass
        
        asyncio.create_task(auto_unmute())
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Mute fail!*\n\n"
            f"⚠️ Bot ko yeh permissions do:\n"
            f"✅ Ban Users ✅ Delete Messages\n\n"
            f"Error: `{str(e)[:80]}`"
        )

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP* mein!")
        return
    
    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        try:
            target_user = (await context.bot.get_chat_member(chat_id, int(context.args[0]))).user
        except:
            await update.message.reply_text("❌ User ID galat!")
            return
    else:
        await update.message.reply_text("🔊 Kisi message ko reply karke `/unmute` bhejo")
        return
    
    if not target_user:
        await update.message.reply_text("❌ User nahi mila!")
        return
    
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
        target_name = target_user.first_name or "User"
        now_ist = get_ist_now()
        await update.message.reply_text(
            f"✅ *UNMUTED!* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {target_name}\n"
            f"🔓 *Unmuted at:*\n"
            f"   🕐 `{now_ist.strftime('%I:%M:%S %p')}`\n"
            f"   📆 {now_ist.strftime('%d %B %Y')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💬 _Ab message kar sakta hai!_ 🎉",
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
        "👑 Admin only | 🇮🇳 IST Time",
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
            "✅ *Funny AI Replies* 😂\n"
            "✅ *Mute System* 🇮🇳\n"
            "✅ *Auto Unmute* ⏰\n"
            "✅ *New User Welcome* 👋\n"
            "✅ *All Media Support* 🖼️\n"
            "✅ *Private Lock* 🔒\n\n"
            "⚡ *COMMANDS:*\n"
            "/start | /clear | /activate\n"
            "/mute | /unmute | /mutelist\n\n"
            "_Bolo boss, kya chahiye?_ 🔥",
            parse_mode="Markdown"
        )
    elif chat_type == ChatType.PRIVATE:
        await update.message.reply_text(
            "🔒 *PRIVATE BOT* 🔒\n\n"
            "_Ye bot sirf OWNER ke liye hai!_ 👑\n\n"
            "💡 *Group mein add karo* —\n"
            "   wahan sabko funny reply milega! 😂",
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
            "_Activate karo, phir enjoy karo!_ 😂🔥",
            parse_mode="Markdown"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf *GROUP* mein!")
        return
    
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text(
                "❌ *Sirf GROUP ADMIN activate kar sakta hai!* 👑\n\n"
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
        await update.message.reply_text("❌ Bot ko *ADMIN* banao pehle!")
        return
    
    active_groups[chat_id] = True
    user_history[chat_id] = []
    await update.message.reply_text(
        "✅ *GROUP ACTIVATED!* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *AB SAB KUCH ON:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 *Funny AI Replies* 😂\n"
        "🔇 *Mute System*\n"
        "⏰ *Auto Unmute*\n"
        "👋 *New User Welcome*\n\n"
        "📢 _Sab kuch bhejo —_\n"
        "   _GARAM GAND jawab dega!_ 💎\n\n"
        "❌ /deactivate — Band karo",
        parse_mode="Markdown"
    )

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *DEACTIVATED!* /activate se on karo")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_history[update.effective_chat.id] = []
    await update.message.reply_text("✅ *Memory Clear!* 💭")

# ================== MESSAGE HANDLER ==================

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    user_id = update.effective_user.id
    
    if message.new_chat_members:
        await welcome_new_user(update, context)
        return
    
    if not message.text:
        return
    
    if chat_type == ChatType.PRIVATE and user_id != OWNER_USER_ID:
        await update.message.reply_text("🔒 *PRIVATE BOT!* Group mein add karo.")
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
    app.add_handler(CommandHandler("mutelist", mutelist))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("😂 GARAM GAND AI — FUNNY + PREMIUM MUTE")
    print(f"👑 Owner ID: {OWNER_USER_ID}")
    print("✅ Funny Reply | Premium Mute | Auto Unmute")
    app.run_polling()

if __name__ == "__main__":
    main()
