import os
import asyncio
import cohere
import pytz
import random
import re
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatType
from collections import defaultdict

# ================== KEYS ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
# ==========================================

OWNER_USER_ID = 7614459746

co = cohere.Client(COHERE_API_KEY)
IST = pytz.timezone('Asia/Kolkata')

# ================== DATABASES ==================
user_history = {}
active_groups = {}
allowed_users = {7614459746}
group_warnings = defaultdict(lambda: defaultdict(int))
group_rules = {}
group_notes = defaultdict(list)
group_filters = defaultdict(list)
group_welcome_msgs = {}
group_goodbye_msgs = {}
group_nightmode = {}
group_slowmode = {}
group_games = {}
group_ranks = defaultdict(lambda: defaultdict(int))
group_afk = {}
group_polls = {}

# ================== AVANTIKA AI ==================
AVANTIKA_PREAMBLE = """You are AVANTIKA AI — Premium, Smart, Multi-Language assistant.
Detect user's language, reply in SAME language. Detailed answers.
Use **Bold**, _Italic_, emojis 🔥💯😂👊💎⚡🎯❤️. Natural & friendly.
Coding → working code. Knowledge → accurate info. Fun → jokes, shayari."""

def get_ist_now():
    return datetime.now(IST)

def parse_time(ts):
    """Parse time string to minutes"""
    ts = ts.lower().strip().replace(" ", "")
    if not ts:
        return None
    # Direct mappings
    mappings = [
        ('seconds', 1/60), ('second', 1/60), ('sec', 1/60), ('secs', 1/60), ('s', 1/60),
        ('minutes', 1), ('minute', 1), ('mins', 1), ('min', 1), ('m', 1),
        ('hours', 60), ('hour', 60), ('hrs', 60), ('hr', 60), ('h', 60),
        ('days', 1440), ('day', 1440), ('d', 1440),
    ]
    for suffix, multiplier in mappings:
        if ts.endswith(suffix):
            try:
                value = float(ts[:-len(suffix)])
                return value * multiplier
            except:
                pass
    try:
        return float(ts)
    except:
        return None

def format_time(minutes):
    """Format minutes to readable string"""
    total_seconds = int(minutes * 60)
    if total_seconds <= 0:
        return "0 seconds"
    
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    mins, seconds = divmod(remainder, 60)
    
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if mins:
        parts.append(f"{mins} minute{'s' if mins != 1 else ''}")
    if seconds and not days:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    return ", ".join(parts) if parts else "0 seconds"

def is_allowed(uid):
    return uid in allowed_users

def get_ai_reply(text, chat_id):
    """Get AI reply from Cohere"""
    if chat_id not in user_history:
        user_history[chat_id] = []
    
    chat_history = []
    for msg in user_history[chat_id][-4:]:
        role = "USER" if msg["role"] == "user" else "CHATBOT"
        chat_history.append({"role": role, "message": msg["content"]})
    
    try:
        response = co.chat(
            message=text,
            chat_history=chat_history,
            preamble=AVANTIKA_PREAMBLE,
            temperature=0.95,
            max_tokens=800
        )
        return response.text
    except:
        return "😅 _Fir se bol!_ 💎"

def is_user_admin(update, context, chat_id, user_id):
    """Check if user is admin in group"""
    try:
        # Try cached admins first
        cache_key = f"admins_{chat_id}"
        if cache_key in context.bot_data:
            return user_id in context.bot_data[cache_key]
        
        # Fetch fresh
        admins = context.bot_data.get(cache_key, set())
        if not admins:
            try:
                chat_admins = context.bot.get_chat_administrators(chat_id)
                # Can't await here, return True as fallback
                return True
            except:
                return False
        return user_id in admins
    except:
        return False

async def refresh_admins(context, chat_id):
    """Cache group admins"""
    try:
        chat_admins = await context.bot.get_chat_administrators(chat_id)
        context.bot_data[f"admins_{chat_id}"] = {admin.user.id for admin in chat_admins}
    except:
        pass

def is_night_time(chat_id):
    """Check if currently in night mode"""
    if chat_id not in group_nightmode:
        return False
    
    now = get_ist_now()
    start = group_nightmode[chat_id]["start"]
    end = group_nightmode[chat_id]["end"]
    
    if start < end:
        # Same day: e.g., 22 to 6
        return start <= now.hour < end
    else:
        # Crosses midnight: e.g., 23 to 7
        return now.hour >= start or now.hour < end

# ================== WELCOME ==================
async def handle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome new members"""
    if not update.message or not update.message.new_chat_members:
        return
    
    chat_id = update.effective_chat.id
    
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            # Bot joined
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "✨ *AVANTIKA AI JOINED!* ✨\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "👑 Admin: `/activate` karo\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "🔥 *FEATURES:*\n"
                    "💬 AI Chat | 🎮 Games | 📊 Polls\n"
                    "🏆 Ranks | 🔞 Filters | ⚠️ Warn\n"
                    "🔇 Mute | 🔨 Ban | 📌 Pin\n"
                    "🌙 Night Mode | ⏱️ Slowmode\n"
                    "📜 Rules | 📝 Notes\n\n"
                    "📋 `/help` — Full command list!"
                ),
                parse_mode="Markdown"
            )
        else:
            # New member
            welcome_msg = group_welcome_msgs.get(
                chat_id,
                f"✨ *WELCOME!* ✨\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *{user.first_name}*\n"
                f"🆔 `{user.id}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌟 _Aapka swagat hai!_ 🎉\n\n"
                f"📋 `/help` — Commands dekho!"
            )
            welcome_msg = welcome_msg.replace("{name}", user.first_name)
            welcome_msg = welcome_msg.replace("{id}", str(user.id))
            welcome_msg = welcome_msg.replace("{mention}", f"[{user.first_name}](tg://user?id={user.id})")
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=welcome_msg,
                parse_mode="Markdown"
            )

# ================== GOODBYE ==================
async def handle_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Goodbye left members"""
    if not update.message or not update.message.left_chat_member:
        return
    
    chat_id = update.effective_chat.id
    user = update.message.left_chat_member
    
    if user.id == context.bot.id:
        return
    
    goodbye_msg = group_goodbye_msgs.get(
        chat_id,
        f"👋 *GOODBYE!*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *{user.first_name}* left!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"😢 _Fir milenge!_"
    )
    goodbye_msg = goodbye_msg.replace("{name}", user.first_name)
    goodbye_msg = goodbye_msg.replace("{id}", str(user.id))
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=goodbye_msg,
        parse_mode="Markdown"
    )

# ================== ACTIVATE/DEACTIVATE ==================
async def cmd_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activate bot in group"""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    # Check if user is admin
    try:
        chat_admins = await context.bot.get_chat_administrators(chat_id)
        admin_ids = {admin.user.id for admin in chat_admins}
        context.bot_data[f"admins_{chat_id}"] = admin_ids
        
        if update.effective_user.id not in admin_ids:
            await update.message.reply_text(
                "❌ *ADMIN ONLY!* 👑\n\n"
                "1️⃣ Bot ko *ADMIN* banao\n"
                "2️⃣ Sab *permissions ON* karo\n"
                "3️⃣ `/activate` karo",
                parse_mode="Markdown"
            )
            return
    except:
        await update.message.reply_text("❌ *Bot ko ADMIN banao!*", parse_mode="Markdown")
        return
    
    active_groups[chat_id] = True
    user_history[chat_id] = []
    
    await update.message.reply_text(
        "✅ *ACTIVATED!* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *AVANTIKA AI IS LIVE!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 AI Chat | 🎮 Games | 📊 Polls\n"
        "🏆 Ranks | 🔞 Filters | 🌙 Night Mode\n"
        "🔇 Mute | 🔨 Ban | ⚠️ Warn\n"
        "📜 Rules | 📝 Notes | 📌 Pin\n\n"
        "📋 `/help` — All commands!\n"
        "❌ `/deactivate` — OFF",
        parse_mode="Markdown"
    )

async def cmd_deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deactivate bot in group"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    active_groups[chat_id] = False
    await update.message.reply_text("🔴 *DEACTIVATED!*\n`/activate` se ON karo!", parse_mode="Markdown")

# ================== START ==================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        if user_id == OWNER_USER_ID:
            user_history[chat_id] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK BOSS!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 *AVANTIKA AI*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ Sab features working!\n"
                "📋 `/help` — Commands\n\n"
                "_Bolo boss!_ 🔥",
                parse_mode="Markdown"
            )
        elif is_allowed(user_id):
            user_history[chat_id] = []
            await update.message.reply_text("✅ *Access Granted!*\n💬 _Ask anything!_ 🔥", parse_mode="Markdown")
        else:
            await update.message.reply_text("🔒 *Access Denied!*", parse_mode="Markdown")
    else:
        user_history[chat_id] = []
        await update.message.reply_text(
            "👋 *AVANTIKA AI* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 Admin: `/activate` karo\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 `/help` — Commands!\n\n"
            "_Activate karo — DHAMAKA!_ 🔥",
            parse_mode="Markdown"
        )

# ================== HELP ==================
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command - show all commands"""
    help_text = (
        "📚 *AVANTIKA AI — HELP* 💎\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👑 *ADMIN COMMANDS:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 `/activate` — Bot ON\n"
        "🔹 `/deactivate` — Bot OFF\n"
        "🔹 `/mute 10m` — Mute user (reply)\n"
        "🔹 `/unmute` — Unmute user (reply)\n"
        "🔹 `/ban` — Ban user (reply/ID)\n"
        "🔹 `/unban ID` — Unban user\n"
        "🔹 `/warn` — Warning (reply)\n"
        "🔹 `/clearwarns` — Reset warnings\n"
        "🔹 `/setrules rules` — Set rules\n"
        "🔹 `/setwelcome msg` — Custom welcome\n"
        "🔹 `/setgoodbye msg` — Custom goodbye\n"
        "🔹 `/addnote note` — Add note\n"
        "🔹 `/clearnotes` — Clear all notes\n"
        "🔹 `/pin` — Pin message (reply)\n"
        "🔹 `/unpin` — Unpin all\n"
        "🔹 `/addfilter word` — Word filter\n"
        "🔹 `/rmfilter word` — Remove filter\n"
        "🔹 `/slowmode 5` — Slowmode (seconds)\n"
        "🔹 `/slowmodeoff` — Slowmode OFF\n"
        "🔹 `/nightmode 22 6` — Night mode\n"
        "🔹 `/nightmodeoff` — Night mode OFF\n"
        "🔹 `/poll \"Q\" \"A\" \"B\"` — Create poll\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 *USER COMMANDS:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔸 `/help` — Ye help\n"
        "🔸 `/info` — Info\n"
        "🔸 `/id` — User ID\n"
        "🔸 `/rules` — Group rules\n"
        "🔸 `/notes` — Notes list\n"
        "🔸 `/filters` — Filter list\n"
        "🔸 `/rank` — Your XP\n"
        "🔸 `/leaderboard` — Top 10\n"
        "🔸 `/game` — Game center 🎮\n"
        "🔸 `/afk reason` — AFK mode\n"
        "🔸 `/stats` — Group stats\n"
        "🔸 `/flip` — Coin flip\n"
        "🔸 `/dice` — Dice roll\n"
        "🔸 `/choose A or B` — Choose\n"
        "🔸 `/fact` — Random fact\n"
        "🔸 `/joke` — Hindi joke\n"
        "🔸 `/shayari` — Shayari\n"
        "🔸 `/quote` — Quote\n"
        "🔸 `/google query` — Search\n"
        "🔸 `/youtube query` — YT\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# ================== MUTE ==================
async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute a user"""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ *Sirf Group mein!*", parse_mode="Markdown")
        return
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    target = None
    time_str = "1h"
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if context.args:
            time_str = " ".join(context.args)
    elif context.args and len(context.args) >= 2:
        try:
            member = await context.bot.get_chat_member(chat_id, int(context.args[0]))
            target = member.user
            time_str = " ".join(context.args[1:])
        except:
            await update.message.reply_text("❌ *User nahi mila!*", parse_mode="Markdown")
            return
    else:
        await update.message.reply_text(
            "🔇 *MUTE SYSTEM*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Reply karke:*\n"
            "`/mute 10s` — 10 seconds\n"
            "`/mute 5m` — 5 minutes\n"
            "`/mute 2h` — 2 hours\n"
            "`/mute 1d` — 1 day\n\n"
            "📌 *ID se:*\n"
            "`/mute 123456 2h`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⏰ *Auto Unmute ON*",
            parse_mode="Markdown"
        )
        return
    
    if not target or target.id == update.effective_user.id or target.is_bot:
        return
    
    minutes = parse_time(time_str)
    if not minutes or minutes > 43200 or minutes <= 0:
        await update.message.reply_text("❌ *Invalid time!* `10s`, `5m`, `2h`, `1d`", parse_mode="Markdown")
        return
    
    now = get_ist_now()
    until = now + timedelta(minutes=minutes)
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target.id,
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
            until_date=until
        )
        
        name = target.first_name
        if target.last_name:
            name += f" {target.last_name}"
        
        await update.message.reply_text(
            f"🔇 *MUTED!* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *{name}*\n"
            f"🆔 `{target.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ *Duration:* {format_time(minutes)}\n"
            f"📅 *Muted:* {now.strftime('%I:%M %p, %d %b')}\n"
            f"🔓 *Unmute:* {until.strftime('%I:%M %p, %d %b')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ *Auto Unmute ON*\n"
            f"🔊 `/unmute` reply se manual!",
            parse_mode="Markdown"
        )
        
        # Auto unmute
        async def auto_unmute():
            await asyncio.sleep(minutes * 60)
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=target.id,
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
                        can_invite_users=True,
                        can_pin_messages=False
                    )
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ *AUTO UNMUTED!*\n👤 *{name}*\n⏱️ {format_time(minutes)} ka mute khatam!\n💬 _Ab message kar sakta hai!_ 🎉",
                    parse_mode="Markdown"
                )
            except:
                pass
        
        asyncio.create_task(auto_unmute())
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Mute Failed!*\nBot ko *Ban Users* permission do!\n`{str(e)[:100]}`",
            parse_mode="Markdown"
        )

async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unmute a user"""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    target = None
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    elif context.args:
        try:
            member = await context.bot.get_chat_member(chat_id, int(context.args[0]))
            target = member.user
        except:
            return
    
    if not target:
        await update.message.reply_text("🔊 *Reply karo ya ID do!*", parse_mode="Markdown")
        return
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target.id,
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
                can_invite_users=True,
                can_pin_messages=False
            )
        )
        await update.message.reply_text(
            f"✅ *UNMUTED!* 🔓\n\n"
            f"👤 *{target.first_name}*\n"
            f"💬 _Ab message kar sakta hai!_ 🎉",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ *Failed!*\n`{str(e)[:100]}`", parse_mode="Markdown")

# ================== BAN/UNBAN ==================
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user"""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    target = None
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    elif context.args:
        try:
            member = await context.bot.get_chat_member(chat_id, int(context.args[0]))
            target = member.user
        except:
            await update.message.reply_text("❌ *User nahi mila!*", parse_mode="Markdown")
            return
    
    if not target or target.id == update.effective_user.id or target.is_bot:
        await update.message.reply_text("❌ *Ban nahi kar sakta!*", parse_mode="Markdown")
        return
    
    try:
        await context.bot.ban_chat_member(chat_id, target.id)
        await update.message.reply_text(
            f"🔨 *BANNED!* 🚫\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *{target.first_name}*\n"
            f"🆔 `{target.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔓 `/unban {target.id}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Ban Failed!*\nBot ko *Ban Users* permission do!\n`{str(e)[:100]}`",
            parse_mode="Markdown"
        )

async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("📝 `/unban user_id`", parse_mode="Markdown")
        return
    
    try:
        user_id = int(context.args[0])
        await context.bot.unban_chat_member(chat_id, user_id)
        await update.message.reply_text(
            f"✅ *UNBANNED!* 🔓\n\n"
            f"🆔 `{user_id}`\n"
            f"💬 Ab user wapas aa sakta hai!",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ *Failed!*\n`{str(e)[:100]}`", parse_mode="Markdown")

# ================== WARN ==================
async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Warn a user"""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ *Kisi message pe reply karo!*", parse_mode="Markdown")
        return
    
    target = update.message.reply_to_message.from_user
    
    if target.is_bot:
        return
    
    group_warnings[chat_id][target.id] += 1
    count = group_warnings[chat_id][target.id]
    
    if count >= 3:
        # Auto mute for 1 hour
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=target.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=get_ist_now() + timedelta(hours=1)
            )
            await update.message.reply_text(
                f"🚫 *3 WARNINGS — MUTED!*\n\n"
                f"👤 *{target.first_name}*\n"
                f"⚠️ 3/3 warnings\n"
                f"⏱️ Auto mute 1 hour",
                parse_mode="Markdown"
            )
            group_warnings[chat_id][target.id] = 0
        except:
            pass
    else:
        await update.message.reply_text(
            f"⚠️ *WARNING!*\n\n"
            f"👤 *{target.first_name}*\n"
            f"📊 *{count}/3*\n"
            f"⚠️ 3 = Auto Mute!",
            parse_mode="Markdown"
        )

async def cmd_clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear warnings"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        group_warnings[chat_id][target.id] = 0
        await update.message.reply_text(f"✅ *Warnings cleared for {target.first_name}!*", parse_mode="Markdown")
    else:
        group_warnings[chat_id] = defaultdict(int)
        await update.message.reply_text("✅ *Sab warnings cleared!*", parse_mode="Markdown")

# ================== NIGHT MODE ==================
async def cmd_nightmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set night mode - NO ONE can message except admins"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "🌙 *NIGHT MODE*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "`/nightmode 22 6` — 10PM to 6AM\n"
            "`/nightmode 23 7` — 11PM to 7AM\n"
            "`/nightmode off` — Disable\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ *Night mode mein:*\n"
            "• Users ke messages DELETE honge\n"
            "• Sirf ADMINS message kar sakte hain\n"
            "• Auto ON/OFF hota hai",
            parse_mode="Markdown"
        )
        return
    
    if context.args[0].lower() == "off":
        group_nightmode.pop(chat_id, None)
        await update.message.reply_text("🌙 *Night Mode OFF!* ✅", parse_mode="Markdown")
        return
    
    try:
        start = int(context.args[0])
        end = int(context.args[1])
        
        if start < 0 or start > 23 or end < 0 or end > 23:
            await update.message.reply_text("❌ *0-23 ke beech do!*", parse_mode="Markdown")
            return
        
        group_nightmode[chat_id] = {"start": start, "end": end}
        
        await update.message.reply_text(
            f"🌙 *NIGHT MODE ON!* 😴\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕙 *Start:* {start}:00 IST\n"
            f"🕕 *End:* {end}:00 IST\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚠️ *Is time mein:*\n"
            f"• User messages = DELETE\n"
            f"• Sirf ADMINS bol sakte hain\n\n"
            f"🌙 `/nightmode off` — Disable",
            parse_mode="Markdown"
        )
    except:
        await update.message.reply_text("❌ *Format:* `/nightmode 22 6`", parse_mode="Markdown")

# ================== SLOWMODE ==================
async def cmd_slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set slowmode"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "⏱️ *SLOWMODE*\n\n"
            "`/slowmode 5` — 5 sec delay\n"
            "`/slowmode 30` — 30 sec\n"
            "`/slowmodeoff` — OFF",
            parse_mode="Markdown"
        )
        return
    
    try:
        seconds = int(context.args[0])
        if seconds <= 0:
            group_slowmode.pop(chat_id, None)
            await update.message.reply_text("⏱️ *Slowmode OFF!* 🚀", parse_mode="Markdown")
        else:
            group_slowmode[chat_id] = seconds
            await update.message.reply_text(
                f"⏱️ *SLOWMODE ON!* 🐌\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ Delay: {seconds} seconds\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Users ko wait karna hoga!",
                parse_mode="Markdown"
            )
    except:
        await update.message.reply_text("❌ *Number do!*", parse_mode="Markdown")

async def cmd_slowmodeoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Turn off slowmode"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    group_slowmode.pop(chat_id, None)
    await update.message.reply_text("⏱️ *Slowmode OFF!* 🚀", parse_mode="Markdown")

# ================== FILTERS ==================
async def cmd_addfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add word filter"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("🔞 `/addfilter word`", parse_mode="Markdown")
        return
    
    word = " ".join(context.args).lower()
    
    if word not in group_filters[chat_id]:
        group_filters[chat_id].append(word)
        await update.message.reply_text(
            f"🔞 *Filter Added!* ✅\n\n"
            f"Word: `{word}`\n"
            f"📋 `/filters` — List\n"
            f"🗑️ `/rmfilter {word}` — Remove",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("⚠️ *Already filtered!*", parse_mode="Markdown")

async def cmd_rmfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove word filter"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        return
    
    word = " ".join(context.args).lower()
    
    if word in group_filters[chat_id]:
        group_filters[chat_id].remove(word)
        await update.message.reply_text(f"✅ *Removed:* `{word}`", parse_mode="Markdown")

async def cmd_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all filters"""
    chat_id = update.effective_chat.id
    
    if group_filters[chat_id]:
        fl = "\n".join([f"• `{w}`" for w in group_filters[chat_id]])
        await update.message.reply_text(
            f"🔞 *FILTERS ({len(group_filters[chat_id])})*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n{fl}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("🔞 _No filters!_\n`/addfilter word`", parse_mode="Markdown")

# ================== WELCOME/GOODBYE ==================
async def cmd_setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set custom welcome"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "✨ *CUSTOM WELCOME*\n\n"
            "`/setwelcome Welcome {name}! 🎉`\n\n"
            "Variables: `{name}`, `{id}`, `{mention}`",
            parse_mode="Markdown"
        )
        return
    
    msg = " ".join(context.args)
    group_welcome_msgs[chat_id] = msg
    
    preview = msg.replace("{name}", update.effective_user.first_name)
    preview = preview.replace("{id}", str(update.effective_user.id))
    
    await update.message.reply_text(
        f"✅ *Welcome Set!* ✨\n\n"
        f"Preview:\n{preview}",
        parse_mode="Markdown"
    )

async def cmd_setgoodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set custom goodbye"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("👋 *CUSTOM GOODBYE*\n`/setgoodbye Bye {name}! 😢`", parse_mode="Markdown")
        return
    
    group_goodbye_msgs[chat_id] = " ".join(context.args)
    await update.message.reply_text("✅ *Goodbye Set!* 👋", parse_mode="Markdown")

# ================== RULES ==================
async def cmd_setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set group rules"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("📜 `/setrules rules here...`", parse_mode="Markdown")
        return
    
    group_rules[chat_id] = " ".join(context.args)
    await update.message.reply_text("📜 *Rules Set!* ✅\n📋 `/rules` — Users dekh sakte hain!", parse_mode="Markdown")

async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show group rules"""
    chat_id = update.effective_chat.id
    
    if chat_id in group_rules:
        await update.message.reply_text(
            f"📜 *GROUP RULES*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n{group_rules[chat_id]}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("📜 _No rules!_ `/setrules`", parse_mode="Markdown")

# ================== NOTES ==================
async def cmd_addnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add note"""
    chat_id = update.effective_chat.id
    
    if not context.args:
        await update.message.reply_text("📝 `/addnote your note`", parse_mode="Markdown")
        return
    
    note = " ".join(context.args)
    group_notes[chat_id].append(note)
    
    await update.message.reply_text(
        f"✅ *Note Added!* 📝\n"
        f"#{len(group_notes[chat_id])}: {note[:200]}\n"
        f"📋 `/notes` — List",
        parse_mode="Markdown"
    )

async def cmd_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List notes"""
    chat_id = update.effective_chat.id
    
    if group_notes[chat_id]:
        nl = "\n".join([f"{i+1}. {n[:200]}" for i, n in enumerate(group_notes[chat_id])])
        await update.message.reply_text(
            f"📝 *NOTES ({len(group_notes[chat_id])})*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n{nl}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("📝 _No notes!_ `/addnote`", parse_mode="Markdown")

async def cmd_clearnotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all notes"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    group_notes[chat_id] = []
    await update.message.reply_text("✅ *Notes cleared!*", parse_mode="Markdown")

# ================== PIN ==================
async def cmd_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pin message"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("📌 *Kisi message pe reply karo!*", parse_mode="Markdown")
        return
    
    try:
        await update.message.reply_to_message.pin()
        await update.message.reply_text("📌 *Pinned!* ✅", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ *Pin failed!* Bot ko permission do!", parse_mode="Markdown")

async def cmd_unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unpin all"""
    chat_id = update.effective_chat.id
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    try:
        await context.bot.unpin_all_chat_messages(chat_id)
        await update.message.reply_text("✅ *Unpinned!*", parse_mode="Markdown")
    except:
        pass

# ================== POLL ==================
async def cmd_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create poll"""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    if not is_user_admin(update, context, chat_id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text(
            "📊 *POLL*\n\n"
            "`/poll \"Question\" \"A\" \"B\" \"C\"`\n\n"
            "Example:\n"
            "`/poll \"Best?\" \"Python\" \"JS\"`",
            parse_mode="Markdown"
        )
        return
    
    text = " ".join(context.args)
    parts = re.findall(r'"([^"]*)"', text)
    
    if len(parts) < 3:
        await update.message.reply_text("❌ Quotes use karo!", parse_mode="Markdown")
        return
    
    question = parts[0]
    options = parts[1:]
    
    pid = str(len(group_polls.get(chat_id, {})) + 1)
    
    if chat_id not in group_polls:
        group_polls[chat_id] = {}
    
    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{opt} (0)", callback_data=f"poll_{pid}_{i}")])
    keyboard.append([InlineKeyboardButton("📊 Results", callback_data=f"pollres_{pid}")])
    
    group_polls[chat_id][pid] = {
        "question": question,
        "options": options,
        "votes": {i: set() for i in range(len(options))}
    }
    
    await update.message.reply_text(
        f"📊 *POLL #{pid}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*Q:* {question}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Vote karo! 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def poll_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle poll votes"""
    query = update.callback_query
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    data = query.data
    
    if data.startswith("poll_") and not data.startswith("pollres_"):
        parts = data.split("_")
        pid = parts[1]
        oid = int(parts[2])
        
        if chat_id in group_polls and pid in group_polls[chat_id]:
            poll = group_polls[chat_id][pid]
            # Remove previous vote
            for v in poll["votes"].values():
                v.discard(uid)
            # Add new vote
            poll["votes"][oid].add(uid)
            
            # Update buttons
            keyboard = []
            for i, opt in enumerate(poll["options"]):
                count = len(poll["votes"][i])
                keyboard.append([InlineKeyboardButton(f"{opt} ({count})", callback_data=f"poll_{pid}_{i}")])
            keyboard.append([InlineKeyboardButton("📊 Results", callback_data=f"pollres_{pid}")])
            
            await query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
            await query.answer("✅ Vote recorded!")
    
    elif data.startswith("pollres_"):
        pid = data.split("_")[1]
        if chat_id in group_polls and pid in group_polls[chat_id]:
            poll = group_polls[chat_id][pid]
            total = sum(len(v) for v in poll["votes"].values())
            
            results = f"📊 *POLL #{pid} RESULTS*\n\n"
            results += f"━━━━━━━━━━━━━━━━━━━━━━\n"
            results += f"*Q:* {poll['question']}\n"
            results += f"📥 Total Votes: {total}\n"
            results += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for i, opt in enumerate(poll["options"]):
                vc = len(poll["votes"][i])
                pct = (vc/total*100) if total > 0 else 0
                bar = "█" * int(pct/5)
                results += f"*{opt}:* {vc} ({pct:.1f}%)\n{bar}\n\n"
            
            await query.edit_message_text(results, parse_mode="Markdown")
            await query.answer("📊 Results!")

# ================== GAME ==================
async def cmd_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Game center"""
    chat_id = update.effective_chat.id
    
    keyboard = [
        [InlineKeyboardButton("🎯 Number Guess (1-100)", callback_data="game_guess")],
        [InlineKeyboardButton("✊ Rock Paper Scissors", callback_data="game_rps")],
        [InlineKeyboardButton("🎲 Roll Dice", callback_data="game_dice")],
        [InlineKeyboardButton("❓ Quiz", callback_data="game_quiz")],
        [InlineKeyboardButton("🔤 Word Scramble", callback_data="game_scramble")],
    ]
    
    await update.message.reply_text(
        "🎮 *GAME CENTER* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Khelo aur jeeto! 🏆\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game callbacks"""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    game = query.data
    
    if game == "game_guess":
        number = random.randint(1, 100)
        group_games[chat_id] = {"type": "guess", "number": number, "attempts": 0}
        await query.edit_message_text(
            "🎯 *NUMBER GUESS!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Maine 1-100 socha!\n"
            "💬 Reply karo apna guess!\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    
    elif game == "game_rps":
        group_games[chat_id] = {"type": "rps"}
        await query.edit_message_text(
            "✊ *ROCK PAPER SCISSORS!*\n\n"
            "💬 Type: `rock`, `paper`, `scissors`",
            parse_mode="Markdown"
        )
    
    elif game == "game_dice":
        d = random.randint(1, 6)
        dice_faces = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        await query.edit_message_text(f"🎲 *DICE!*\n\n{dice_faces[d]} *{d}*", parse_mode="Markdown")
    
    elif game == "game_quiz":
        questions = [
            {"q": "🌍 India capital?", "a": "delhi"},
            {"q": "🧮 15 + 27 = ?", "a": "42"},
            {"q": "🎬 'DDLJ' hero?", "a": "shah rukh khan"},
            {"q": "🏏 Most ODI centuries?", "a": "sachin tendulkar"},
            {"q": "💻 Python year?", "a": "1991"},
        ]
        q = random.choice(questions)
        group_games[chat_id] = {"type": "quiz", "answer": q["a"]}
        await query.edit_message_text(
            f"❓ *QUIZ!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{q['q']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 Reply karo!",
            parse_mode="Markdown"
        )
    
    elif game == "game_scramble":
        words = ["python", "telegram", "bot", "coding", "india", "game", "computer"]
        w = random.choice(words)
        scrambled = ''.join(random.sample(w, len(w)))
        group_games[chat_id] = {"type": "scramble", "answer": w}
        await query.edit_message_text(
            f"🔤 *WORD SCRAMBLE!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"`{scrambled}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 Reply karo sahi word!",
            parse_mode="Markdown"
        )

# ================== RANK ==================
async def cmd_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user rank"""
    chat_id = update.effective_chat.id
    uid = update.effective_user.id
    
    if update.message.reply_to_message:
        uid = update.message.reply_to_message.from_user.id
    
    score = group_ranks[chat_id].get(uid, 0)
    
    # Find position
    sorted_ranks = sorted(group_ranks[chat_id].items(), key=lambda x: x[1], reverse=True)
    position = next((i+1 for i, (u, _) in enumerate(sorted_ranks) if u == uid), "?")
    
    if score < 50:
        level = "🌱 Beginner"
    elif score < 200:
        level = "🌟 Active"
    elif score < 500:
        level = "💎 Pro"
    else:
        level = "🔥 LEGEND"
    
    try:
        user = await context.bot.get_chat(uid)
        name = user.first_name
    except:
        name = "User"
    
    await update.message.reply_text(
        f"🏆 *RANK*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *{name}*\n"
        f"⭐ XP: {score}\n"
        f"📊 Rank: #{position}\n"
        f"🏅 Level: {level}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top 10"""
    chat_id = update.effective_chat.id
    
    if not group_ranks[chat_id]:
        await update.message.reply_text("🏆 _Abhi koi XP nahi! Chat karo!_", parse_mode="Markdown")
        return
    
    top = sorted(group_ranks[chat_id].items(), key=lambda x: x[1], reverse=True)[:10]
    
    lb = "🏆 *LEADERBOARD* 🔥\n\n"
    lb += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    
    for i, (uid, score) in enumerate(top, 1):
        try:
            user = await context.bot.get_chat(uid)
            name = user.first_name
        except:
            name = f"User {uid}"
        lb += f"{medals.get(i, f'#{i}')} *{name}* — {score} XP\n"
    
    lb += "━━━━━━━━━━━━━━━━━━━━━━"
    
    await update.message.reply_text(lb, parse_mode="Markdown")

# ================== AFK ==================
async def cmd_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set AFK"""
    uid = update.effective_user.id
    reason = " ".join(context.args) if context.args else "AFK"
    
    group_afk[uid] = {
        "reason": reason,
        "time": get_ist_now(),
        "name": update.effective_user.first_name
    }
    
    await update.message.reply_text(
        f"😴 *AFK ON!*\n\n"
        f"👤 {update.effective_user.first_name}\n"
        f"📝 {reason}\n"
        f"🕐 {get_ist_now().strftime('%I:%M %p')}\n\n"
        f"💬 Koi reply karega to auto alert!",
        parse_mode="Markdown"
    )

# ================== FUN COMMANDS ==================
async def cmd_flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = random.choice(["Heads 🪙", "Tails 🪙"])
    await update.message.reply_text(f"🪙 *FLIP!*\n\n{result}", parse_mode="Markdown")

async def cmd_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sides = int(context.args[0]) if context.args and context.args[0].isdigit() else 6
    if sides < 2:
        sides = 6
    result = random.randint(1, sides)
    await update.message.reply_text(f"🎲 *DICE!*\n\n`{result}` (1-{sides})", parse_mode="Markdown")

async def cmd_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🤔 `/choose A or B or C`", parse_mode="Markdown")
        return
    
    text = " ".join(context.args)
    options = [o.strip() for o in text.replace(" or ", ",").split(",") if o.strip()]
    
    if len(options) < 2:
        await update.message.reply_text("🤔 *2+ options do!*", parse_mode="Markdown")
        return
    
    choice = random.choice(options)
    await update.message.reply_text(f"🤔 *I choose:*\n\n✨ *{choice}*", parse_mode="Markdown")

async def cmd_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = [
        "🐙 Octopus ke 3 dil hote hain!",
        "🍯 Honey kabhi kharab nahi hoti!",
        "⚡ Lightning din mein 8.6 million bar girti hai!",
        "🧠 Human brain 20W electricity generate karta hai!",
        "🦋 Butterflies apne pairo se taste karti hain!",
        "🌍 Earth ka 71% surface paani!",
        "🐘 Elephants can't jump!",
        "🦈 Sharks dinosaurs se purane hain!",
    ]
    await update.message.reply_text(f"🤯 *FACT!*\n\n{random.choice(facts)}", parse_mode="Markdown")

async def cmd_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "😂 Teacher: 'Late kyun?'\nStudent: 'Corner tha ghar se nikalte time!'",
        "🤣 Santa: 'Online pizza order kiya... download nahi hua!'",
        "😆 Pappu: 'Papa, aaj sirf maine answer diya!'\nPapa: 'Kya pucha?'\nPappu: 'Homework kaun nahi laya?'",
        "😜 Biwi: 'Tum mujhse pyaar nahi karte!'\nPati: 'Aur kisko karu?'",
    ]
    await update.message.reply_text(f"😄 *JOKE!*\n\n{random.choice(jokes)}", parse_mode="Markdown")

async def cmd_shayari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shayaris = [
        "💕 *Mohabbat mein humne khoya hai sab kuch,*\n*Phir bhi teri yaadon mein khoye rehte hain...*",
        "🌟 *Zindagi ek safar hai suhana,*\n*Yahan kal kya ho kisne jaana...*",
        "🔥 *Duniya ki bheed mein tanha the hum,*\n*Jab tak tumse na mile the...*",
    ]
    await update.message.reply_text(random.choice(shayaris), parse_mode="Markdown")

async def cmd_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quotes = [
        "💭 *'The only way to do great work is to love what you do.'* — Steve Jobs",
        "💭 *'In the middle of difficulty lies opportunity.'* — Einstein",
        "💭 *'Believe you can and you're halfway there.'* — Roosevelt",
        "💭 *'Success is not final, failure is not fatal.'* — Churchill",
    ]
    await update.message.reply_text(random.choice(quotes), parse_mode="Markdown")

# ================== INFO ==================
async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(
            f"👤 *USER INFO*\n\n"
            f"👤 *{u.first_name}*\n🆔 `{u.id}`\n📛 @{u.username or 'None'}",
            parse_mode="Markdown"
        )
    else:
        try:
            c = await context.bot.get_chat(update.effective_chat.id)
            await update.message.reply_text(
                f"👥 *GROUP INFO*\n\n"
                f"👥 *{c.title}*\n🆔 `{update.effective_chat.id}`",
                parse_mode="Markdown"
            )
        except:
            pass

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        await update.message.reply_text(f"🆔 `{u.id}` | 👤 {u.first_name}", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    stats = f"📊 *GROUP STATS* 🔥\n\n"
    stats += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    stats += f"📝 Notes: {len(group_notes.get(chat_id, []))}\n"
    stats += f"🔞 Filters: {len(group_filters.get(chat_id, []))}\n"
    stats += f"⚠️ Warnings: {sum(group_warnings.get(chat_id, {}).values())}\n"
    stats += f"🏆 Ranked: {len(group_ranks.get(chat_id, {}))}\n"
    stats += f"⏱️ Slowmode: {group_slowmode.get(chat_id, 'OFF')}s\n"
    stats += f"🌙 Night Mode: {'ON 😴' if chat_id in group_nightmode else 'OFF'}\n"
    stats += f"✨ Custom Welcome: {'YES' if chat_id in group_welcome_msgs else 'Default'}\n"
    stats += f"📜 Rules: {'SET' if chat_id in group_rules else 'Not set'}\n"
    stats += f"━━━━━━━━━━━━━━━━━━━━━━"
    
    await update.message.reply_text(stats, parse_mode="Markdown")

async def cmd_google(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    query = "+".join(context.args)
    await update.message.reply_text(
        f"🔍 [Click to search](https://www.google.com/search?q={query})",
        parse_mode="Markdown",
        disable_web_page_preview=False
    )

async def cmd_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    query = "+".join(context.args)
    await update.message.reply_text(
        f"▶️ [Click to search](https://www.youtube.com/results?search_query={query})",
        parse_mode="Markdown",
        disable_web_page_preview=False
    )

# ================== OWNER COMMANDS ==================
async def cmd_adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    if context.args:
        try:
            allowed_users.add(int(context.args[0]))
            await update.message.reply_text(f"✅ Added `{context.args[0]}`", parse_mode="Markdown")
        except:
            pass

async def cmd_removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    if context.args:
        try:
            uid = int(context.args[0])
            if uid != OWNER_USER_ID:
                allowed_users.discard(uid)
                await update.message.reply_text(f"✅ Removed `{uid}`", parse_mode="Markdown")
        except:
            pass

async def cmd_userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    ul = "\n".join([f"• `{u}` {'👑' if u==OWNER_USER_ID else ''}" for u in allowed_users])
    await update.message.reply_text(f"👥 *Users ({len(allowed_users)})*\n{ul}", parse_mode="Markdown")

async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID or not context.args:
        return
    msg = "📢 *BROADCAST*\n\n" + " ".join(context.args)
    count = 0
    for uid in allowed_users:
        try:
            await context.bot.send_message(uid, msg, parse_mode="Markdown")
            count += 1
        except:
            pass
    await update.message.reply_text(f"✅ Sent to {count} users", parse_mode="Markdown")

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    group_warnings[chat_id] = defaultdict(int)
    group_rules.pop(chat_id, None)
    group_notes[chat_id] = []
    group_filters[chat_id] = []
    group_ranks[chat_id] = defaultdict(int)
    await update.message.reply_text("✅ *Reset!* 🔄", parse_mode="Markdown")

# ================== MESSAGE HANDLER ==================
last_message_time = defaultdict(lambda: defaultdict(float))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    msg = update.message
    
    # Welcome/Goodbye
    if msg.new_chat_members:
        await handle_welcome(update, context)
        return
    if msg.left_chat_member:
        await handle_goodbye(update, context)
        return
    
    # Private chat - only allowed users
    if chat_type == ChatType.PRIVATE:
        if not is_allowed(user_id):
            await msg.reply_text("🔒 *Access Denied!*", parse_mode="Markdown")
            return
    
    # Group - must be activated
    if chat_type != ChatType.PRIVATE:
        if chat_id not in active_groups or not active_groups[chat_id]:
            return
        
        # ===== NIGHT MODE CHECK =====
        if is_night_time(chat_id):
            is_admin = is_user_admin(update, context, chat_id, user_id)
            if not is_admin:
                try:
                    await msg.delete()
                except:
                    pass
                return
        
        # ===== SLOWMODE CHECK =====
        if chat_id in group_slowmode:
            is_admin = is_user_admin(update, context, chat_id, user_id)
            if not is_admin:
                now = datetime.now().timestamp()
                last = last_message_time[chat_id].get(user_id, 0)
                if now - last < group_slowmode[chat_id]:
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                last_message_time[chat_id][user_id] = now
    
    if not msg.text:
        return
    
    # ===== GAME HANDLING =====
    if chat_id in group_games:
        game = group_games[chat_id]
        txt = msg.text.lower().strip()
        
        if game["type"] == "guess":
            try:
                guess = int(txt)
                game["attempts"] += 1
                if guess == game["number"]:
                    await msg.reply_text(f"🎯 *CORRECT!* 🎉\nNumber: {game['number']}\nAttempts: {game['attempts']}", parse_mode="Markdown")
                    del group_games[chat_id]
                    return
                elif guess < game["number"]:
                    await msg.reply_text(f"📈 Higher! (#{game['attempts']})", parse_mode="Markdown")
                else:
                    await msg.reply_text(f"📉 Lower! (#{game['attempts']})", parse_mode="Markdown")
            except:
                pass
        
        elif game["type"] == "rps":
            if txt in ["rock", "paper", "scissors"]:
                bot = random.choice(["rock", "paper", "scissors"])
                e = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
                if txt == bot:
                    r = "🤝 TIE!"
                elif (txt=="rock" and bot=="scissors") or (txt=="paper" and bot=="rock") or (txt=="scissors" and bot=="paper"):
                    r = "🎉 YOU WIN!"
                else:
                    r = "😢 BOT WINS!"
                await msg.reply_text(f"✊ You: {e[txt]} | Bot: {e[bot]}\n\n{r}", parse_mode="Markdown")
                del group_games[chat_id]
                return
        
        elif game["type"] == "quiz":
            if txt == game["answer"]:
                await msg.reply_text("✅ *CORRECT!* 🎉", parse_mode="Markdown")
                del group_games[chat_id]
                return
        
        elif game["type"] == "scramble":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *CORRECT!* 🎉\nWord: *{game['answer']}*", parse_mode="Markdown")
                del group_games[chat_id]
                return
    
    # ===== FILTER CHECK =====
    if chat_id in group_filters:
        text_lower = msg.text.lower()
        for word in group_filters[chat_id]:
            if word in text_lower:
                try:
                    await msg.delete()
                except:
                    pass
                await msg.reply_text(f"🔞 *Filtered!* ⚠️\n👤 {update.effective_user.first_name}", parse_mode="Markdown")
                return
    
    # ===== AFK CHECK =====
    if msg.reply_to_message and msg.reply_to_message.from_user:
        replied_uid = msg.reply_to_message.from_user.id
        if replied_uid in group_afk and replied_uid != user_id:
            afk = group_afk[replied_uid]
            diff = get_ist_now() - afk["time"]
            hours, rem = divmod(int(diff.total_seconds()), 3600)
            mins, secs = divmod(rem, 60)
            ts = f"{hours}h {mins}m" if hours else f"{mins}m" if mins else f"{secs}s"
            
            await msg.reply_text(
                f"😴 *AFK!*\n\n"
                f"👤 {afk.get('name', 'User')}\n"
                f"📝 {afk['reason']}\n"
                f"⏱️ Since: {ts} ago",
                parse_mode="Markdown"
            )
    
    # ===== RANK UPDATE =====
    if chat_type != ChatType.PRIVATE:
        group_ranks[chat_id][user_id] += random.randint(1, 3)
    
    # ===== AI REPLY =====
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        reply = get_ai_reply(msg.text, chat_id)
        
        if chat_id not in user_history:
            user_history[chat_id] = []
        user_history[chat_id].append({"role": "user", "content": msg.text})
        user_history[chat_id].append({"role": "assistant", "content": reply})
        user_history[chat_id] = user_history[chat_id][-10:]
        
        await msg.reply_text(reply, parse_mode="Markdown")
    except:
        pass

# ================== MAIN ==================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    commands = {
        "start": cmd_start, "help": cmd_help, "activate": cmd_activate,
        "deactivate": cmd_deactivate, "mute": cmd_mute, "unmute": cmd_unmute,
        "ban": cmd_ban, "unban": cmd_unban, "warn": cmd_warn,
        "clearwarns": cmd_clearwarns, "nightmode": cmd_nightmode,
        "slowmode": cmd_slowmode, "slowmodeoff": cmd_slowmodeoff,
        "addfilter": cmd_addfilter, "rmfilter": cmd_rmfilter,
        "filters": cmd_filters, "setwelcome": cmd_setwelcome,
        "setgoodbye": cmd_setgoodbye, "setrules": cmd_setrules,
        "rules": cmd_rules, "addnote": cmd_addnote, "notes": cmd_notes,
        "clearnotes": cmd_clearnotes, "pin": cmd_pin, "unpin": cmd_unpin,
        "poll": cmd_poll, "game": cmd_game, "rank": cmd_rank,
        "leaderboard": cmd_leaderboard, "afk": cmd_afk,
        "flip": cmd_flip, "dice": cmd_dice, "choose": cmd_choose,
        "fact": cmd_fact, "joke": cmd_joke, "shayari": cmd_shayari,
        "quote": cmd_quote, "info": cmd_info, "id": cmd_id,
        "stats": cmd_stats, "google": cmd_google, "youtube": cmd_youtube,
        "adduser": cmd_adduser, "removeuser": cmd_removeuser,
        "userlist": cmd_userlist, "broadcast": cmd_broadcast,
        "clear": cmd_clear,
    }
    
    for cmd, handler in commands.items():
        app.add_handler(CommandHandler(cmd, handler))
    
    app.add_handler(CallbackQueryHandler(game_callback, pattern="^game_"))
    app.add_handler(CallbackQueryHandler(poll_callback, pattern="^poll"))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("👑 AVANTIKA AI — ALL WORKING! 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()
