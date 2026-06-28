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
group_warnings = {}
group_rules = {}
group_notes = {}
group_filters = {}
group_welcome_msgs = {}
group_goodbye_msgs = {}
group_nightmode = {}
group_slowmode = {}
group_games = {}
group_ranks = {}
group_afk = {}
group_polls = {}

# Track last message time for slowmode
last_msg_time = {}

# ================== AVANTIKA AI ==================
AVANTIKA_PREAMBLE = """You are AVANTIKA AI — Premium, Smart, Multi-Language assistant.
Detect user's language, reply in SAME language. Detailed answers.
Use **Bold**, _Italic_, emojis 🔥💯😂👊💎⚡🎯❤️. Natural & friendly.
Coding → working code. Knowledge → accurate info. Fun → jokes, shayari."""

def get_ist_now():
    return datetime.now(IST)

def parse_time(ts):
    ts = ts.lower().strip().replace(" ", "")
    if not ts:
        return None
    
    # Check for patterns like "10s", "5m", "2h", "1d"
    patterns = {
        's': 1/60, 'sec': 1/60, 'secs': 1/60, 'second': 1/60, 'seconds': 1/60,
        'm': 1, 'min': 1, 'mins': 1, 'minute': 1, 'minutes': 1,
        'h': 60, 'hr': 60, 'hrs': 60, 'hour': 60, 'hours': 60,
        'd': 1440, 'day': 1440, 'days': 1440,
    }
    
    for suffix, multiplier in patterns.items():
        if ts.endswith(suffix):
            try:
                num = float(ts[:-len(suffix)])
                return num * multiplier
            except:
                pass
    
    # Try plain number (minutes)
    try:
        return float(ts)
    except:
        return None

def format_time(minutes):
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

async def get_admin_ids(chat_id, context):
    """Get list of admin IDs for a chat"""
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        return {admin.user.id for admin in admins}
    except:
        return set()

def check_night_mode(chat_id):
    """Check if night mode is active RIGHT NOW"""
    if chat_id not in group_nightmode:
        return False
    
    now = get_ist_now()
    current_hour = now.hour
    start_hour = group_nightmode[chat_id]["start"]
    end_hour = group_nightmode[chat_id]["end"]
    
    if start_hour < end_hour:
        # Same day range: e.g., 1 to 5 (1AM to 5AM)
        return start_hour <= current_hour < end_hour
    else:
        # Crosses midnight: e.g., 22 to 6 (10PM to 6AM)
        return current_hour >= start_hour or current_hour < end_hour

# ================== COMMANDS ==================

async def cmd_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    admin_ids = await get_admin_ids(chat_id, context)
    
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text(
            "❌ *ADMIN ONLY!* 👑\n\n"
            "1️⃣ Bot ko *ADMIN* banao\n"
            "2️⃣ Sab *permissions ON* karo\n"
            "3️⃣ `/activate` karo",
            parse_mode="Markdown"
        )
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
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    active_groups[chat_id] = False
    await update.message.reply_text("🔴 *DEACTIVATED!* `/activate` se ON karo!", parse_mode="Markdown")

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        if user_id == OWNER_USER_ID:
            user_history[chat_id] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK BOSS!* 👑\n\n💎 *AVANTIKA AI*\n\n✅ Sab features working!\n📋 `/help` — Commands\n\n_Bolo boss!_ 🔥",
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

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *AVANTIKA AI — HELP* 💎\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👑 *ADMIN COMMANDS:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 `/activate` — Bot ON\n"
        "🔹 `/deactivate` — Bot OFF\n"
        "🔹 `/mute 10m` — Mute (reply)\n"
        "🔹 `/unmute` — Unmute (reply)\n"
        "🔹 `/ban` — Ban (reply/ID)\n"
        "🔹 `/unban ID` — Unban\n"
        "🔹 `/warn` — Warning (reply)\n"
        "🔹 `/clearwarns` — Reset warnings\n"
        "🔹 `/setrules text` — Set rules\n"
        "🔹 `/setwelcome msg` — Welcome\n"
        "🔹 `/setgoodbye msg` — Goodbye\n"
        "🔹 `/addnote text` — Add note\n"
        "🔹 `/clearnotes` — Clear notes\n"
        "🔹 `/pin` — Pin (reply)\n"
        "🔹 `/unpin` — Unpin all\n"
        "🔹 `/addfilter word` — Filter\n"
        "🔹 `/rmfilter word` — Remove\n"
        "🔹 `/slowmode 5` — Slowmode\n"
        "🔹 `/slowmodeoff` — Slowmode OFF\n"
        "🔹 `/nightmode 22 6` — Night\n"
        "🔹 `/nightmodeoff` — Night OFF\n"
        "🔹 `/poll \"Q\" \"A\" \"B\"` — Poll\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 *USER COMMANDS:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔸 `/help` — Help\n"
        "🔸 `/info` — Info\n"
        "🔸 `/id` — User ID\n"
        "🔸 `/rules` — Rules\n"
        "🔸 `/notes` — Notes\n"
        "🔸 `/filters` — Filters\n"
        "🔸 `/rank` — XP\n"
        "🔸 `/leaderboard` — Top 10\n"
        "🔸 `/game` — Games 🎮\n"
        "🔸 `/afk reason` — AFK\n"
        "🔸 `/stats` — Stats\n"
        "🔸 `/flip` — Coin flip\n"
        "🔸 `/dice` — Dice\n"
        "🔸 `/choose A or B` — Choose\n"
        "🔸 `/fact` — Fact\n"
        "🔸 `/joke` — Joke\n"
        "🔸 `/shayari` — Shayari\n"
        "🔸 `/quote` — Quote\n"
        "🔸 `/google q` — Search\n"
        "🔸 `/youtube q` — YT\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

# ================== NIGHT MODE ==================
async def cmd_nightmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args or len(context.args) < 2:
        # Show current status
        if chat_id in group_nightmode:
            nm = group_nightmode[chat_id]
            status = "ON 😴" if check_night_mode(chat_id) else "OFF (time not reached)"
            await update.message.reply_text(
                f"🌙 *NIGHT MODE*\n\n"
                f"Status: {status}\n"
                f"Start: {nm['start']}:00 IST\n"
                f"End: {nm['end']}:00 IST\n\n"
                f"`/nightmode 22 6` — Set\n"
                f"`/nightmodeoff` — Disable",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🌙 *NIGHT MODE*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "`/nightmode 22 6` — 10PM to 6AM\n"
                "`/nightmode 23 7` — 11PM to 7AM\n"
                "`/nightmode 1 5` — 1AM to 5AM\n"
                "`/nightmodeoff` — Disable\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ *Night mode ON hone par:*\n"
                "• Users messages DELETE honge\n"
                "• Sirf ADMINS message kar sakte hain\n"
                "• Time ke hisab se AUTO ON/OFF",
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
            await update.message.reply_text("❌ *0-23 ke beech mein do!*", parse_mode="Markdown")
            return
        
        group_nightmode[chat_id] = {"start": start, "end": end}
        
        is_active = check_night_mode(chat_id)
        
        await update.message.reply_text(
            f"🌙 *NIGHT MODE SET!* 😴\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕙 Start: {start}:00 IST\n"
            f"🕕 End: {end}:00 IST\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Status: {'🟢 ACTIVE NOW' if is_active else '🔴 Will auto-start'}\n\n"
            f"⚠️ *Jab night mode ON ho:*\n"
            f"• Users messages = AUTO DELETE\n"
            f"• Sirf ADMINS bol sakte hain\n\n"
            f"`/nightmodeoff` — Disable",
            parse_mode="Markdown"
        )
    except:
        await update.message.reply_text("❌ *Format:* `/nightmode 22 6`", parse_mode="Markdown")

async def cmd_nightmodeoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    group_nightmode.pop(chat_id, None)
    await update.message.reply_text("🌙 *Night Mode OFF!* ✅\nAb sab message kar sakte hain!", parse_mode="Markdown")

# ================== SLOWMODE ==================
async def cmd_slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        current = group_slowmode.get(chat_id, None)
        if current:
            await update.message.reply_text(
                f"⏱️ *SLOWMODE*\n\n"
                f"Status: 🟢 ON\n"
                f"Delay: {current} seconds\n\n"
                f"`/slowmodeoff` — Disable",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "⏱️ *SLOWMODE*\n\n"
                "`/slowmode 5` — 5 sec\n"
                "`/slowmode 30` — 30 sec\n"
                "`/slowmode 60` — 1 min\n"
                "`/slowmodeoff` — OFF",
                parse_mode="Markdown"
            )
        return
    
    try:
        seconds = int(context.args[0])
        if seconds <= 0:
            group_slowmode.pop(chat_id, None)
            if chat_id in last_msg_time:
                last_msg_time[chat_id] = {}
            await update.message.reply_text("⏱️ *Slowmode OFF!* 🚀", parse_mode="Markdown")
        else:
            group_slowmode[chat_id] = seconds
            await update.message.reply_text(
                f"⏱️ *SLOWMODE ON!* 🐌\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ Delay: {seconds} seconds\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⚠️ Users ko har message ke beech\n"
                f"{seconds}s wait karna hoga!\n"
                f"Fast messages = DELETE\n\n"
                f"👑 Admins exempt",
                parse_mode="Markdown"
            )
    except:
        await update.message.reply_text("❌ *Number do!* `/slowmode 5`", parse_mode="Markdown")

async def cmd_slowmodeoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    group_slowmode.pop(chat_id, None)
    if chat_id in last_msg_time:
        last_msg_time[chat_id] = {}
    await update.message.reply_text("⏱️ *Slowmode OFF!* 🚀", parse_mode="Markdown")

# ================== GAME ==================
async def cmd_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    keyboard = [
        [InlineKeyboardButton("🎯 Number Guess (1-100)", callback_data="game_guess")],
        [InlineKeyboardButton("✊ Rock Paper Scissors", callback_data="game_rps")],
        [InlineKeyboardButton("🎲 Roll Dice", callback_data="game_dice")],
        [InlineKeyboardButton("❓ Quiz Time", callback_data="game_quiz")],
        [InlineKeyboardButton("🔤 Word Scramble", callback_data="game_scramble")],
    ]
    
    await update.message.reply_text(
        "🎮 *GAME CENTER* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Button dabao aur khelo! 🏆\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def game_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game button clicks"""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    game_choice = query.data
    
    if game_choice == "game_guess":
        number = random.randint(1, 100)
        group_games[chat_id] = {"type": "guess", "number": number, "attempts": 0}
        await query.edit_message_text(
            "🎯 *NUMBER GUESS GAME!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔢 Maine 1-100 ke beech ek number socha hai!\n"
            "💬 Chat mein guess karo!\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "_Example: 50_",
            parse_mode="Markdown"
        )
    
    elif game_choice == "game_rps":
        group_games[chat_id] = {"type": "rps"}
        await query.edit_message_text(
            "✊ *ROCK PAPER SCISSORS!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💬 Chat mein type karo:\n"
            "`rock` 🪨 | `paper` 📄 | `scissors` ✂️\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    
    elif game_choice == "game_dice":
        dice_num = random.randint(1, 6)
        dice_faces = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        await query.edit_message_text(
            f"🎲 *DICE ROLL!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{dice_faces[dice_num]}  *{dice_num}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    
    elif game_choice == "game_quiz":
        questions = [
            {"q": "🌍 India ki capital kya hai?", "a": "delhi"},
            {"q": "🧮 15 + 27 kitna hota hai?", "a": "42"},
            {"q": "🎬 'DDLJ' ke hero kaun hain?", "a": "shah rukh khan"},
            {"q": "🏏 Sabse zyada ODI centuries kisne banayi?", "a": "sachin tendulkar"},
            {"q": "💻 Python language kab launch hui?", "a": "1991"},
        ]
        q = random.choice(questions)
        group_games[chat_id] = {"type": "quiz", "answer": q["a"]}
        await query.edit_message_text(
            f"❓ *QUIZ TIME!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 {q['q']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 Chat mein answer likho!",
            parse_mode="Markdown"
        )
    
    elif game_choice == "game_scramble":
        words = ["python", "telegram", "coding", "india", "game", "computer", "keyboard", "internet"]
        word = random.choice(words)
        scrambled = ''.join(random.sample(word, len(word)))
        group_games[chat_id] = {"type": "scramble", "answer": word}
        await query.edit_message_text(
            f"🔤 *WORD SCRAMBLE!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔀 Scrambled: `{scrambled}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 Sahi word likho chat mein!\n"
            f"_Hint: {len(word)} letters_",
            parse_mode="Markdown"
        )

# ================== POLL ==================
async def cmd_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text(
            "📊 *POLL CREATE*\n\n"
            "`/poll \"Question\" \"Option1\" \"Option2\" \"Option3\"`\n\n"
            "Example:\n"
            "`/poll \"Best language?\" \"Python\" \"JS\" \"Go\"`",
            parse_mode="Markdown"
        )
        return
    
    text = " ".join(context.args)
    parts = re.findall(r'"([^"]*)"', text)
    
    if len(parts) < 3:
        await update.message.reply_text("❌ Quotes use karo: `/poll \"Q\" \"A\" \"B\"`", parse_mode="Markdown")
        return
    
    question = parts[0]
    options = parts[1:]
    
    if chat_id not in group_polls:
        group_polls[chat_id] = {}
    
    pid = str(len(group_polls[chat_id]) + 1)
    
    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{opt} (0)", callback_data=f"vote_{pid}_{i}")])
    keyboard.append([InlineKeyboardButton("📊 Results", callback_data=f"result_{pid}")])
    
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
        f"👇 Vote karo!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def poll_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle poll button clicks"""
    query = update.callback_query
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    data = query.data
    
    if data.startswith("vote_"):
        _, pid, oid = data.split("_")
        oid = int(oid)
        
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
                keyboard.append([InlineKeyboardButton(f"{opt} ({count})", callback_data=f"vote_{pid}_{i}")])
            keyboard.append([InlineKeyboardButton("📊 Results", callback_data=f"result_{pid}")])
            
            try:
                await query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
            except:
                pass
            await query.answer("✅ Vote recorded!")
    
    elif data.startswith("result_"):
        pid = data.split("_")[1]
        
        if chat_id in group_polls and pid in group_polls[chat_id]:
            poll = group_polls[chat_id][pid]
            total = sum(len(v) for v in poll["votes"].values())
            
            result_text = f"📊 *POLL #{pid} RESULTS*\n\n"
            result_text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
            result_text += f"*Q:* {poll['question']}\n"
            result_text += f"📥 Total: {total} votes\n"
            result_text += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for i, opt in enumerate(poll["options"]):
                vc = len(poll["votes"][i])
                pct = (vc/total*100) if total > 0 else 0
                bar = "█" * int(pct/5)
                result_text += f"*{opt}:* {vc} ({pct:.1f}%)\n{bar}\n\n"
            
            await query.edit_message_text(result_text, parse_mode="Markdown")
            await query.answer("📊 Results!")

# ================== MUTE ==================
async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ *Sirf Group mein!*", parse_mode="Markdown")
        return
    
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
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
            "📌 Reply karke: `/mute 10s` `/mute 5m` `/mute 2h` `/mute 1d`\n"
            "📌 ID se: `/mute 123456 2h`\n\n"
            "⏰ Auto Unmute ON",
            parse_mode="Markdown"
        )
        return
    
    if not target or target.id == update.effective_user.id or target.is_bot:
        return
    
    minutes = parse_time(time_str)
    if not minutes or minutes > 43200 or minutes <= 0:
        await update.message.reply_text("❌ *Invalid time!* `10s` `5m` `2h` `1d`", parse_mode="Markdown")
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
            f"⏱️ Duration: {format_time(minutes)}\n"
            f"📅 Muted: {now.strftime('%I:%M %p, %d %b')}\n"
            f"🔓 Unmute: {until.strftime('%I:%M %p, %d %b')}\n\n"
            f"⏰ *Auto Unmute ON*\n"
            f"🔊 `/unmute` reply se manual!",
            parse_mode="Markdown"
        )
        
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
        await update.message.reply_text(f"❌ *Mute Failed!*\nBot ko *Ban Users* permission do!", parse_mode="Markdown")

async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
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
            pass
    
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
        await update.message.reply_text(f"✅ *UNMUTED!* 🔓\n👤 *{target.first_name}*\n💬 _Ab message kar sakta hai!_ 🎉", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ *Failed!*\n`{str(e)[:100]}`", parse_mode="Markdown")

# ================== BAN/UNBAN ==================
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
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
        await update.message.reply_text(f"🔨 *BANNED!* 🚫\n\n👤 *{target.first_name}*\n🆔 `{target.id}`\n\n🔓 `/unban {target.id}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("❌ *Ban Failed!* Bot ko *Ban Users* permission do!", parse_mode="Markdown")

async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("📝 `/unban user_id`", parse_mode="Markdown")
        return
    
    try:
        uid = int(context.args[0])
        await context.bot.unban_chat_member(chat_id, uid)
        await update.message.reply_text(f"✅ *UNBANNED!* 🔓\n🆔 `{uid}`", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ *Failed!*", parse_mode="Markdown")

# ================== WARN ==================
async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ *Kisi message pe reply karo!*", parse_mode="Markdown")
        return
    
    target = update.message.reply_to_message.from_user
    
    if target.is_bot:
        return
    
    if chat_id not in group_warnings:
        group_warnings[chat_id] = {}
    if target.id not in group_warnings[chat_id]:
        group_warnings[chat_id][target.id] = 0
    
    group_warnings[chat_id][target.id] += 1
    count = group_warnings[chat_id][target.id]
    
    if count >= 3:
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=target.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=get_ist_now() + timedelta(hours=1)
            )
            await update.message.reply_text(f"🚫 *3 WARNINGS — MUTED!*\n👤 *{target.first_name}*\n⏱️ 1 hour", parse_mode="Markdown")
            group_warnings[chat_id][target.id] = 0
        except:
            pass
    else:
        await update.message.reply_text(f"⚠️ *WARNING {count}/3*\n👤 *{target.first_name}*\n⚠️ 3 = Auto Mute!", parse_mode="Markdown")

async def cmd_clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if chat_id in group_warnings and target.id in group_warnings[chat_id]:
            group_warnings[chat_id][target.id] = 0
        await update.message.reply_text(f"✅ Warnings cleared for *{target.first_name}*", parse_mode="Markdown")
    else:
        group_warnings[chat_id] = {}
        await update.message.reply_text("✅ *Sab warnings cleared!*", parse_mode="Markdown")

# ================== SIMPLE COMMANDS ==================
async def cmd_setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    if not context.args:
        return
    group_rules[chat_id] = " ".join(context.args)
    await update.message.reply_text("📜 *Rules Set!* ✅", parse_mode="Markdown")

async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in group_rules:
        await update.message.reply_text(f"📜 *RULES*\n\n{group_rules[chat_id]}", parse_mode="Markdown")
    else:
        await update.message.reply_text("📜 _No rules!_", parse_mode="Markdown")

async def cmd_addnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        return
    if chat_id not in group_notes:
        group_notes[chat_id] = []
    group_notes[chat_id].append(" ".join(context.args))
    await update.message.reply_text(f"✅ *Note Added!* 📝 (#{len(group_notes[chat_id])})", parse_mode="Markdown")

async def cmd_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in group_notes and group_notes[chat_id]:
        nl = "\n".join([f"{i+1}. {n}" for i, n in enumerate(group_notes[chat_id])])
        await update.message.reply_text(f"📝 *NOTES*\n\n{nl}", parse_mode="Markdown")
    else:
        await update.message.reply_text("📝 _No notes!_", parse_mode="Markdown")

async def cmd_clearnotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    group_notes[chat_id] = []
    await update.message.reply_text("✅ *Cleared!*", parse_mode="Markdown")

async def cmd_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return
    try:
        await update.message.reply_to_message.pin()
        await update.message.reply_text("📌 *Pinned!* ✅", parse_mode="Markdown")
    except:
        pass

async def cmd_unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    except:
        pass

async def cmd_setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        return
    group_welcome_msgs[chat_id] = " ".join(context.args)
    await update.message.reply_text("✅ *Welcome Set!* ✨", parse_mode="Markdown")

async def cmd_setgoodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        return
    group_goodbye_msgs[chat_id] = " ".join(context.args)
    await update.message.reply_text("✅ *Goodbye Set!* 👋", parse_mode="Markdown")

async def cmd_addfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        return
    word = " ".join(context.args).lower()
    if chat_id not in group_filters:
        group_filters[chat_id] = []
    if word not in group_filters[chat_id]:
        group_filters[chat_id].append(word)
        await update.message.reply_text(f"🔞 *Filtered:* `{word}`", parse_mode="Markdown")

async def cmd_rmfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        return
    word = " ".join(context.args).lower()
    if chat_id in group_filters and word in group_filters[chat_id]:
        group_filters[chat_id].remove(word)
        await update.message.reply_text(f"✅ *Removed:* `{word}`", parse_mode="Markdown")

async def cmd_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in group_filters and group_filters[chat_id]:
        fl = "\n".join([f"• `{w}`" for w in group_filters[chat_id]])
        await update.message.reply_text(f"🔞 *FILTERS*\n{fl}", parse_mode="Markdown")
    else:
        await update.message.reply_text("🔞 _No filters!_", parse_mode="Markdown")

async def cmd_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    uid = update.effective_user.id
    if update.message.reply_to_message:
        uid = update.message.reply_to_message.from_user.id
    
    if chat_id not in group_ranks:
        group_ranks[chat_id] = {}
    
    score = group_ranks[chat_id].get(uid, 0)
    
    if score < 50:
        level = "🌱 Beginner"
    elif score < 200:
        level = "🌟 Active"
    elif score < 500:
        level = "💎 Pro"
    else:
        level = "🔥 LEGEND"
    
    await update.message.reply_text(f"🏆 *RANK*\n⭐ XP: {score}\n🏅 Level: {level}", parse_mode="Markdown")

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in group_ranks or not group_ranks[chat_id]:
        await update.message.reply_text("🏆 _No XP yet!_", parse_mode="Markdown")
        return
    
    top = sorted(group_ranks[chat_id].items(), key=lambda x: x[1], reverse=True)[:10]
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lb = "🏆 *LEADERBOARD*\n\n"
    
    for i, (uid, score) in enumerate(top, 1):
        try:
            u = await context.bot.get_chat(uid)
            name = u.first_name
        except:
            name = f"User{uid}"
        lb += f"{medals.get(i, f'#{i}')} *{name}* — {score} XP\n"
    
    await update.message.reply_text(lb, parse_mode="Markdown")

async def cmd_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    reason = " ".join(context.args) if context.args else "AFK"
    group_afk[uid] = {"reason": reason, "time": get_ist_now(), "name": update.effective_user.first_name}
    await update.message.reply_text(f"😴 *AFK ON!*\n📝 {reason}", parse_mode="Markdown")

async def cmd_flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🪙 *{random.choice(['Heads', 'Tails'])}!*", parse_mode="Markdown")

async def cmd_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sides = int(context.args[0]) if context.args and context.args[0].isdigit() else 6
    result = random.randint(1, max(2, sides))
    await update.message.reply_text(f"🎲 *{result}*", parse_mode="Markdown")

async def cmd_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    text = " ".join(context.args)
    options = [o.strip() for o in text.replace(" or ", ",").split(",") if o.strip()]
    if len(options) >= 2:
        await update.message.reply_text(f"✨ *{random.choice(options)}*", parse_mode="Markdown")

async def cmd_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = ["🐙 Octopus ke 3 dil!", "🍯 Honey kabhi kharab nahi hoti!", "⚡ Lightning 8.6M bar/day!", "🧠 Brain 20W power!"]
    await update.message.reply_text(f"🤯 *{random.choice(facts)}*", parse_mode="Markdown")

async def cmd_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = ["😂 Teacher: 'Late kyun?' Student: 'Corner tha!'", "🤣 Santa: 'Pizza download nahi hua!'"]
    await update.message.reply_text(f"😄 *{random.choice(jokes)}*", parse_mode="Markdown")

async def cmd_shayari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = ["💕 *Mohabbat mein khoya sab kuch...*", "🌟 *Zindagi ek safar hai...*"]
    await update.message.reply_text(random.choice(s), parse_mode="Markdown")

async def cmd_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = ["💭 *'Stay hungry, stay foolish.'* — Jobs", "💭 *'Think different.'* — Apple"]
    await update.message.reply_text(random.choice(q), parse_mode="Markdown")

async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(f"👤 *{u.first_name}*\n🆔 `{u.id}`", parse_mode="Markdown")
    else:
        c = await context.bot.get_chat(update.effective_chat.id)
        await update.message.reply_text(f"👥 *{c.title}*\n🆔 `{update.effective_chat.id}`", parse_mode="Markdown")

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        await update.message.reply_text(f"🆔 `{update.message.reply_to_message.from_user.id}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    is_night = check_night_mode(chat_id)
    s = f"📊 *STATS*\n\n📝 Notes: {len(group_notes.get(chat_id, []))}\n🔞 Filters: {len(group_filters.get(chat_id, []))}\n🏆 Ranked: {len(group_ranks.get(chat_id, {}))}\n⏱️ Slowmode: {group_slowmode.get(chat_id, 'OFF')}s\n🌙 Night Mode: {'🟢 ON' if is_night else '🔴 OFF'}"
    await update.message.reply_text(s, parse_mode="Markdown")

async def cmd_google(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await update.message.reply_text(f"🔍 https://www.google.com/search?q={'+'.join(context.args)}", disable_web_page_preview=False)

async def cmd_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await update.message.reply_text(f"▶️ https://www.youtube.com/results?search_query={'+'.join(context.args)}", disable_web_page_preview=False)

# ================== OWNER ==================
async def cmd_adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    if context.args:
        try:
            allowed_users.add(int(context.args[0]))
            await update.message.reply_text(f"✅ `{context.args[0]}`", parse_mode="Markdown")
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
                await update.message.reply_text(f"✅ `{uid}`", parse_mode="Markdown")
        except:
            pass

async def cmd_userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    ul = "\n".join([f"• `{u}`" for u in allowed_users])
    await update.message.reply_text(f"👥 *Users ({len(allowed_users)})*\n{ul}", parse_mode="Markdown")

async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID or not context.args:
        return
    msg = "📢 *BROADCAST*\n" + " ".join(context.args)
    c = 0
    for u in allowed_users:
        try:
            await context.bot.send_message(u, msg, parse_mode="Markdown")
            c += 1
        except:
            pass
    await update.message.reply_text(f"✅ {c} users", parse_mode="Markdown")

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    group_warnings[chat_id] = {}
    group_rules.pop(chat_id, None)
    group_notes[chat_id] = []
    group_filters[chat_id] = []
    group_ranks[chat_id] = {}
    group_games.pop(chat_id, None)
    await update.message.reply_text("✅ *Reset!*", parse_mode="Markdown")

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    msg = update.message
    
    # ===== WELCOME =====
    if msg.new_chat_members:
        for user in msg.new_chat_members:
            if user.id == context.bot.id:
                await context.bot.send_message(chat_id,
                    "✨ *AVANTIKA AI JOINED!* ✨\n\n"
                    "👑 Admin: `/activate` karo\n"
                    "📋 `/help` — Commands\n\n"
                    "_Activate karo — DHAMAKA!_ 🔥",
                    parse_mode="Markdown"
                )
            else:
                wm = group_welcome_msgs.get(chat_id, f"✨ *WELCOME!* ✨\n\n👤 *{user.first_name}*\n🌟 _Aapka swagat hai!_ 🎉")
                wm = wm.replace("{name}", user.first_name).replace("{id}", str(user.id))
                wm = wm.replace("{mention}", f"[{user.first_name}](tg://user?id={user.id})")
                await context.bot.send_message(chat_id, wm, parse_mode="Markdown")
        return
    
    # ===== GOODBYE =====
    if msg.left_chat_member:
        user = msg.left_chat_member
        if user.id != context.bot.id:
            gm = group_goodbye_msgs.get(chat_id, f"👋 *{user.first_name}* left! 😢")
            gm = gm.replace("{name}", user.first_name).replace("{id}", str(user.id))
            await context.bot.send_message(chat_id, gm, parse_mode="Markdown")
        return
    
    # ===== PRIVATE CHAT CHECK =====
    if chat_type == ChatType.PRIVATE:
        if not is_allowed(user_id):
            await msg.reply_text("🔒 *Access Denied!*", parse_mode="Markdown")
            return
    else:
        # ===== GROUP: MUST BE ACTIVATED =====
        if chat_id not in active_groups or not active_groups[chat_id]:
            return
        
        # ===== NIGHT MODE CHECK =====
        if check_night_mode(chat_id):
            admin_ids = await get_admin_ids(chat_id, context)
            if user_id not in admin_ids:
                try:
                    await msg.delete()
                except:
                    pass
                return
        
        # ===== SLOWMODE CHECK =====
        if chat_id in group_slowmode:
            admin_ids = await get_admin_ids(chat_id, context)
            if user_id not in admin_ids:
                now = datetime.now().timestamp()
                if chat_id not in last_msg_time:
                    last_msg_time[chat_id] = {}
                
                last_time = last_msg_time[chat_id].get(user_id, 0)
                delay = group_slowmode[chat_id]
                
                if now - last_time < delay:
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                
                last_msg_time[chat_id][user_id] = now
    
    if not msg.text:
        return
    
    # ===== GAME HANDLING =====
    if chat_id in group_games:
        game = group_games[chat_id]
        txt = msg.text.lower().strip()
        
        if game["type"] == "guess":
            try:
                guess_num = int(txt)
                game["attempts"] += 1
                
                if guess_num == game["number"]:
                    await msg.reply_text(
                        f"🎯 *CORRECT!* 🎉\n\n"
                        f"Number: {game['number']}\n"
                        f"Attempts: {game['attempts']}",
                        parse_mode="Markdown"
                    )
                    del group_games[chat_id]
                    return
                elif guess_num < game["number"]:
                    await msg.reply_text(f"📈 *Higher!* ⬆️ (#{game['attempts']})", parse_mode="Markdown")
                else:
                    await msg.reply_text(f"📉 *Lower!* ⬇️ (#{game['attempts']})", parse_mode="Markdown")
            except:
                pass
            return
        
        elif game["type"] == "rps":
            if txt in ["rock", "paper", "scissors"]:
                bot_choice = random.choice(["rock", "paper", "scissors"])
                emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
                
                if txt == bot_choice:
                    result = "🤝 *TIE!*"
                elif (txt == "rock" and bot_choice == "scissors") or \
                     (txt == "paper" and bot_choice == "rock") or \
                     (txt == "scissors" and bot_choice == "paper"):
                    result = "🎉 *YOU WIN!*"
                else:
                    result = "😢 *BOT WINS!*"
                
                await msg.reply_text(
                    f"✊ *RPS!*\n\n"
                    f"You: {emojis[txt]} {txt}\n"
                    f"Bot: {emojis[bot_choice]} {bot_choice}\n\n"
                    f"{result}",
                    parse_mode="Markdown"
                )
                del group_games[chat_id]
                return
        
        elif game["type"] == "quiz":
            if txt == game["answer"]:
                await msg.reply_text("✅ *CORRECT!* 🎉", parse_mode="Markdown")
                del group_games[chat_id]
                return
            return
        
        elif game["type"] == "scramble":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *CORRECT!* 🎉\nWord: *{game['answer']}*", parse_mode="Markdown")
                del group_games[chat_id]
                return
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
                await msg.reply_text(f"🔞 *Filtered!* ⚠️", parse_mode="Markdown")
                return
    
    # ===== AFK CHECK =====
    if msg.reply_to_message and msg.reply_to_message.from_user:
        replied_uid = msg.reply_to_message.from_user.id
        if replied_uid in group_afk and replied_uid != user_id:
            afk = group_afk[replied_uid]
            diff = get_ist_now() - afk["time"]
            hours, rem = divmod(int(diff.total_seconds()), 3600)
            mins, _ = divmod(rem, 60)
            ts = f"{hours}h {mins}m" if hours else f"{mins}m"
            await msg.reply_text(f"😴 *AFK!*\n👤 {afk.get('name', 'User')}\n📝 {afk['reason']}\n⏱️ {ts} ago", parse_mode="Markdown")
    
    # ===== RANK UPDATE =====
    if chat_type != ChatType.PRIVATE:
        if chat_id not in group_ranks:
            group_ranks[chat_id] = {}
        if user_id not in group_ranks[chat_id]:
            group_ranks[chat_id][user_id] = 0
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
    
    # All commands
    all_commands = {
        "start": cmd_start, "help": cmd_help, "activate": cmd_activate,
        "deactivate": cmd_deactivate, "mute": cmd_mute, "unmute": cmd_unmute,
        "ban": cmd_ban, "unban": cmd_unban, "warn": cmd_warn,
        "clearwarns": cmd_clearwarns, "nightmode": cmd_nightmode,
        "nightmodeoff": cmd_nightmodeoff, "slowmode": cmd_slowmode,
        "slowmodeoff": cmd_slowmodeoff, "addfilter": cmd_addfilter,
        "rmfilter": cmd_rmfilter, "filters": cmd_filters,
        "setwelcome": cmd_setwelcome, "setgoodbye": cmd_setgoodbye,
        "setrules": cmd_setrules, "rules": cmd_rules,
        "addnote": cmd_addnote, "notes": cmd_notes,
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
    
    for cmd_name, handler in all_commands.items():
        app.add_handler(CommandHandler(cmd_name, handler))
    
    # Button handlers
    app.add_handler(CallbackQueryHandler(game_button_handler, pattern="^game_"))
    app.add_handler(CallbackQueryHandler(poll_button_handler, pattern="^(vote_|result_)"))
    
    # Message handler
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("👑 AVANTIKA AI — NIGHT MODE ✅ | SLOW MODE ✅ | GAMES ✅ | ALL WORKING! 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()
