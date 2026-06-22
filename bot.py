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
OWNER_USER_ID = 1234567890  # 👈 APNI USER ID YAHAN DALO
# =================================================

co = cohere.Client(COHERE_API_KEY)

IST = pytz.timezone('Asia/Kolkata')

user_history = {}
active_groups = set()

# ================== PREMIUM AI ==================

PREMIUM_PREAMBLE = """Tu GARAM GAND AI Bot hai — ek PREMIUM, MAST aur FUNNY AI assistant.

TERI PERSONALITY:
- Mast, funny, thoda attitude wala lekin RESPECTFUL
- Har sawal ka DETAILED, ACCURATE aur HELPFUL jawab
- Emojis use kar: 🔥💯😂👊💎⚡🎯❤️🙏
- User ki LANGUAGE mein jawab de
- NATURAL baat kar, robot ki tarah nahi
- Joke sunane ko bole to REAL FUNNY jokes de
- Shayari bole to ORIGINAL SHAYARI likh
- Code maange to PROPER WORKING code de
- Advice maange to GENUINE HELPFUL advice de
- Koi bhi topic — FULL CONFIDENCE se jawab
- Har baat mein thoda SWAG
- Short messages ko INTERESTING bana
- Desi + Classy mix
- Kabhi boring nahi hona
- Har reply MEMORABLE hona chahiye
- User ki feeling samajh"""

def get_ist_now():
    return datetime.now(IST)

def parse_time(time_str):
    """Koi bhi time format samjho"""
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
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if mins > 0:
        parts.append(f"{mins} minute{'s' if mins != 1 else ''}")
    if secs > 0 and days == 0:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    
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
        return "😅 Thoda sa ruk ja bhai, fir se bol! 💎"

# ================== MUTE SYSTEM ==================

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf **GROUP** mein chalta hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, admin_id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Sirf **GROUP ADMIN** mute kar sakta hai! 👑")
            return
    except:
        await update.message.reply_text("❌ Bot ko admin rights do pehle!")
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
                "🔇 **MUTE USAGE** 🇮🇳\n\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "📌 **Reply karke:**\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                "`/mute 10 second`\n"
                "`/mute 5 minute`\n"
                "`/mute 2 hour`\n"
                "`/mute 1 day`\n\n"
                "📌 **Short format:**\n"
                "`/mute 25s` `/mute 5m`\n"
                "`/mute 2h` `/mute 1d`\n"
                "`/mute 30d` (max)\n\n"
                "📌 **Manual:**\n"
                "`/mute user_id 10 minute`\n\n"
                "🇮🇳 IST Time | ⏰ Auto Unmute"
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
        await update.message.reply_text("❌ Time format galat! Use: `10 second`, `5 minute`, `2 hour`, `1 day`, `25s`, `5m`, `2h`, `1d`")
        return
    
    if mute_minutes > 43200:
        await update.message.reply_text("❌ Max **30 days** tak mute kar sakte ho!")
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
        reply_msg = update.message.reply_to_message.message_id if update.message.reply_to_message else None
        
        mute_msg = await update.message.reply_text(
            f"🔇 **MUTED! — INDIA TIME** 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **User:** {target_name}\n"
            f"🆔 ID: `{target_user.id}`\n"
            f"👑 **By:** {admin_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ **Duration:** {format_time(mute_minutes)}\n\n"
            f"📅 **Muted at:**\n"
            f"   🕐 `{now_ist.strftime('%I:%M:%S %p')}`\n"
            f"   📆 {now_ist.strftime('%d %B %Y')}\n\n"
            f"🔓 **Unmute at:**\n"
            f"   🕐 `{until_ist.strftime('%I:%M:%S %p')}`\n"
            f"   📆 {until_ist.strftime('%d %B %Y')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ Time khatam hone par **AUTO UNMUTE** hoga!\n"
            f"🔊 Ya `/unmute` reply karke manual unmute"
        )
        
        # 🔥 AUTO UNMUTE SCHEDULE
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
                    text=f"✅ **AUTO UNMUTED!** 🇮🇳\n\n"
                         f"👤 {target_name}\n"
                         f"⏱️ {format_time(mute_minutes)} ka mute khatam!\n"
                         f"💬 Ab message kar sakta hai! 🎉"
                )
            except:
                pass
        
        asyncio.create_task(auto_unmute())
        
    except Exception as e:
        await update.message.reply_text(f"❌ Mute fail! Permissions check karo.\n`{str(e)[:80]}`")

# ================== UNMUTE ==================

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    admin_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf **GROUP** mein chalta hai!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, admin_id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Sirf **GROUP ADMIN** unmute kar sakta hai! 👑")
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
        await update.message.reply_text("🔊 **UNMUTE:** Kisi message ko reply karke `/unmute` bhejo")
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
            f"✅ **UNMUTED!** 🇮🇳\n\n"
            f"👤 **User:** {target_name}\n"
            f"🔓 **At:** `{now_ist.strftime('%I:%M:%S %p, %d %B %Y')}`\n\n"
            f"💬 Ab message kar sakta hai! 🎉"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Unmute fail: `{str(e)[:80]}`")

async def mutelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔇 **MUTE HELP** 🇮🇳\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 **MUTE (reply karke):**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "`/mute 10 second` | `25s`\n"
        "`/mute 5 minute` | `5m`\n"
        "`/mute 2 hour` | `2h`\n"
        "`/mute 1 day` | `1d`\n"
        "`/mute 30d` (max)\n\n"
        "📌 **UNMUTE:** `/unmute` reply\n"
        "📌 **Manual:** `/mute ID time`\n\n"
        "⏰ Auto Unmute ON\n"
        "👑 Admin only | 🇮🇳 IST Time"
    )

# ================== BASIC COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type != ChatType.PRIVATE:
        user_history[chat_id] = []
        await update.message.reply_text(
            "👋 **GARAM GAND AI READY!** 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 **Admin Commands:**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "/activate — Bot ON\n"
            "/mute — Mute user\n"
            "/unmute — Unmute user\n"
            "/mutelist — Mute help\n\n"
            "⏰ Auto Unmute Enabled!\n"
            "💬 Activate ke baad sabko premium reply!"
        )
        return
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("🔒 Private bot! Group mein add karo.")
        return
    
    user_history[chat_id] = []
    await update.message.reply_text(
        "💎 **WELCOME BOSS!** 💎\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 **SYSTEMS ACTIVE:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Premium AI Replies\n"
        "✅ Mute System (IST) 🇮🇳\n"
        "✅ Auto Unmute ⏰\n"
        "✅ Seconds/Minutes/Hours/Days\n"
        "✅ Private Lock 🔒\n"
        "✅ Group Support 👥\n"
        "✅ Sab Media Reply\n\n"
        "/start | /clear | /activate | /deactivate\n"
        "/mute | /unmute | /mutelist"
    )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.add(chat_id)
            user_history[chat_id] = []
            await update.message.reply_text(
                "✅ **GROUP ACTIVATED!** 🔥\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📢 Sabko PREMIUM REPLY!\n"
                "🔇 Mute + ⏰ Auto Unmute ON!\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "/mute 10 second | /mute 5 minute\n"
                "/mute 2 hour | /mute 1 day\n"
                "/unmute — Manual unmute\n\n"
                "❌ /deactivate — Band karo"
            )
        else:
            await update.message.reply_text("❌ Sirf ADMIN!")
    except:
        await update.message.reply_text("❌ Bot ko admin banao!")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ Sirf GROUP!")
        return
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            active_groups.discard(chat_id)
            await update.message.reply_text("🔴 Deactivated! /activate se on karo.")
    except:
        pass

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text("✅ Memory Clear! 💭")

# ================== MESSAGE HANDLER ==================

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE and user_id != OWNER_USER_ID:
        await update.message.reply_text("🔒 Private bot! Group mein add karo — sabko reply milega!")
        return
    
    if chat_type != ChatType.PRIVATE and chat_id not in active_groups:
        return
    
    if message.text:
        user_input = message.text
    elif message.caption:
        user_input = f"[Media]: {message.caption}"
    elif message.photo:
        user_input = "🖼️ Photo bheji — mazedaar reaction de"
    elif message.video:
        user_input = "🎬 Video bheja — mazedaar reaction de"
    elif message.sticker:
        emoji = message.sticker.emoji or ""
        user_input = f"🎯 Sticker {emoji} — funny reaction de"
    elif message.voice:
        user_input = "🎵 Voice message — funny comment kar"
    elif message.audio:
        user_input = "🎧 Audio — music pe baat kar"
    elif message.document:
        user_input = "📄 Document — iske baare mein bol"
    elif message.animation:
        user_input = "🎞️ GIF — mazedaar reaction de"
    elif message.video_note:
        user_input = "📹 Video note — funny comment"
    elif message.location:
        user_input = "📍 Location — puchho kahan ho"
    elif message.contact:
        user_input = "👤 Contact — mazedaar comment"
    elif message.poll:
        user_input = "📊 Poll — vote karne ko bol"
    else:
        user_input = "📨 Kuch bheja — curious reaction de"

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        bot_reply = get_premium_reply(user_input, chat_id)
        
        if chat_id not in user_history:
            user_history[chat_id] = []
        user_history[chat_id].append({"role": "user", "content": user_input})
        user_history[chat_id].append({"role": "assistant", "content": bot_reply})
        user_history[chat_id] = user_history[chat_id][-30:]
        
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
    
    print("💎 GARAM GAND AI — ULTIMATE BOT")
    print("🇮🇳 IST | ⏰ Auto Unmute | 🔇 Mute | 🔊 Unmute | 💬 AI")
    app.run_polling()

if __name__ == "__main__":
    main()
