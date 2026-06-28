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
last_message_time = {}

# ================== AVANTIKA AI PREMIUM ==================
AVANTIKA_PREAMBLE = """You are *AVANTIKA AI* — *Premium*, *Smart*, *Multi-Language AI Assistant* 🔥💎⚡

*RULES:*
1. Detect user's language & reply in *SAME language*
2. Use *Bold* (**text**) & _Italic_ (_text_) formatting ALWAYS
3. Use emojis: 🔥💯😂👊💎⚡🎯❤️🤯😎✨🌟👑💬📊🏆🔇🔨⚠️📜📝📌🪙🎲🤔😄💕💭🔍▶️
4. Give detailed, helpful answers
5. Coding questions → *working code* with explanation
6. Knowledge → accurate info with sources
7. Fun → jokes, shayari, motivational quotes"""

def get_ist_now():
    return datetime.now(IST)

def parse_time(ts):
    ts = ts.lower().strip().replace(" ", "")
    if not ts:
        return None
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
    if days: parts.append(f"*{days}* day{'s' if days != 1 else ''}")
    if hours: parts.append(f"*{hours}* hour{'s' if hours != 1 else ''}")
    if mins: parts.append(f"*{mins}* minute{'s' if mins != 1 else ''}")
    if seconds and not days: parts.append(f"*{seconds}* second{'s' if seconds != 1 else ''}")
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
        return "_😅 Fir se bol! Kuch error aaya..._ 💎"

async def get_admin_ids(chat_id, context):
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        return {admin.user.id for admin in admins}
    except:
        return set()

def is_night_mode_active(chat_id):
    """Check if night mode is currently active"""
    if chat_id not in group_nightmode:
        return False
    now = get_ist_now()
    current_hour = now.hour
    start_hour = group_nightmode[chat_id]["start"]
    end_hour = group_nightmode[chat_id]["end"]
    if start_hour < end_hour:
        return start_hour <= current_hour < end_hour
    else:
        return current_hour >= start_hour or current_hour < end_hour

# ================== PREMIUM WELCOME ==================
async def handle_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return
    chat_id = update.effective_chat.id
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "✨ *AVANTIKA AI — JOINED!* ✨\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "💎 *_PREMIUM AI BOT_* 💎\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "👑 *_Admin:_* `/activate` _karo_ ⚡\n\n"
                    "🔥 *_FEATURES:_*\n"
                    "• 💬 _AI Chat_ — Premium Replies\n"
                    "• 🎮 _Games_ — 5 Interactive Games\n"
                    "• 📊 _Polls_ — Live Voting System\n"
                    "• 🏆 _Ranks_ — XP & Leaderboard\n"
                    "• 🌙 _Night Mode_ — Auto Message Delete\n"
                    "• ⏱️ _Slow Mode_ — Rate Limiting\n"
                    "• 🔞 _Word Filters_ — Auto Delete\n"
                    "• 🔇 _Mute_ | 🔨 _Ban_ | ⚠️ _Warn_\n"
                    "• 📜 _Rules_ | 📝 _Notes_ | 📌 _Pin_\n"
                    "• 😂 _Jokes_ | 💕 _Shayari_ | 🤯 _Facts_\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "📋 `/help` — _Full Command List!_ 💬\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "_🔥 Activate karo — DHAMAKA MACHADEGA! 🔥_"
                ),
                parse_mode="Markdown"
            )
        else:
            welcome_msg = group_welcome_msgs.get(
                chat_id,
                (
                    "✨ *_WELCOME TO THE GROUP!_* ✨\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 *_Name:_* *{user.first_name}*\n"
                    f"🆔 *_ID:_* `{user.id}`\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "🌟 *_Aapka swagat hai!_* 🎉\n\n"
                    "💎 *_Yahaan milega:_*\n"
                    "• _AI Replies_ — Premium 🔥\n"
                    "• _Coding Help_ — Working Code 💻\n"
                    "• _Knowledge_ — Accurate Info 📚\n"
                    "• _Fun & Masti_ — Jokes, Shayari 😂\n\n"
                    "📋 `/help` — _Commands dekho!_ 💬\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "🔰 *_Enjoy karo!_* 🤗"
                )
            )
            welcome_msg = welcome_msg.replace("{name}", f"*{user.first_name}*")
            welcome_msg = welcome_msg.replace("{id}", f"`{user.id}`")
            welcome_msg = welcome_msg.replace("{mention}", f"[{user.first_name}](tg://user?id={user.id})")
            await context.bot.send_message(chat_id=chat_id, text=welcome_msg, parse_mode="Markdown")

# ================== PREMIUM GOODBYE ==================
async def handle_left_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.left_chat_member:
        return
    chat_id = update.effective_chat.id
    user = update.message.left_chat_member
    if user.id == context.bot.id:
        return
    goodbye_msg = group_goodbye_msgs.get(
        chat_id,
        (
            "👋 *_GOODBYE!_* 👋\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *_User:_* *{user.first_name}*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "😢 *_Fir milenge dost!_* 💔\n"
            "_Jab tak, khush raho!_ ✨"
        )
    )
    goodbye_msg = goodbye_msg.replace("{name}", f"*{user.first_name}*")
    goodbye_msg = goodbye_msg.replace("{id}", f"`{user.id}`")
    await context.bot.send_message(chat_id=chat_id, text=goodbye_msg, parse_mode="Markdown")

# ================== NIGHT MODE ==================
async def cmd_nightmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
        return
    if not context.args or len(context.args) < 2:
        if chat_id in group_nightmode:
            nm = group_nightmode[chat_id]
            is_active = is_night_mode_active(chat_id)
            await update.message.reply_text(
                f"🌙 *_NIGHT MODE STATUS_* 😴\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🟢 *_Status:_* {'*ACTIVE* 🔴' if is_active else '*Inactive* 🟢'}\n"
                f"🕙 *_Start:_* `{nm['start']}:00 IST`\n"
                f"🕕 *_End:_* `{nm['end']}:00 IST`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"`/nightmode 22 6` — _Set new time_\n"
                f"`/nightmodeoff` — _Disable_",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🌙 *_NIGHT MODE_* 😴\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 *_Usage:_*\n"
                "`/nightmode 22 6` — _10PM to 6AM_\n"
                "`/nightmode 23 7` — _11PM to 7AM_\n"
                "`/nightmode 1 5` — _1AM to 5AM_\n"
                "`/nightmodeoff` — _Disable_\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ *_Jab Night Mode ON hoga:_*\n"
                "• _Users ke messages_ *AUTO DELETE* _honge_\n"
                "• _Sirf_ *ADMINS* _message kar sakte hain_\n"
                "• _Time ke hisab se_ *AUTO ON/OFF*",
                parse_mode="Markdown"
            )
        return
    if context.args[0].lower() == "off":
        group_nightmode.pop(chat_id, None)
        await update.message.reply_text("✅ *_Night Mode OFF!_* 🟢\n_Ab sab message kar sakte hain!_ 🎉", parse_mode="Markdown")
        return
    try:
        start = int(context.args[0])
        end = int(context.args[1])
        if start < 0 or start > 23 or end < 0 or end > 23:
            await update.message.reply_text("❌ *_0-23 ke beech mein number do!_*", parse_mode="Markdown")
            return
        group_nightmode[chat_id] = {"start": start, "end": end}
        is_active = is_night_mode_active(chat_id)
        await update.message.reply_text(
            f"✅ *_NIGHT MODE SET!_* 😴\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕙 *_Start:_* `{start}:00 IST`\n"
            f"🕕 *_End:_* `{end}:00 IST`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟢 *_Current Status:_* {'*ACTIVE 🔴*' if is_active else '*Will Auto-Start*'}\n\n"
            f"⚠️ *_Night mode mein:_*\n"
            f"• _User messages =_ *DELETE* 🗑️\n"
            f"• _Only_ *ADMINS* _can chat_ 👑\n\n"
            f"`/nightmodeoff` — _Disable_\n"
            f"`/nightmode` — _Check status_",
            parse_mode="Markdown"
        )
    except:
        await update.message.reply_text("❌ *_Format:_* `/nightmode 22 6`", parse_mode="Markdown")

async def cmd_nightmodeoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
        return
    group_nightmode.pop(chat_id, None)
    await update.message.reply_text("✅ *_Night Mode OFF!_* 🟢\n_Ab sab log message kar sakte hain!_ 🎉💬", parse_mode="Markdown")

# ================== SLOW MODE ==================
async def cmd_slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
        return
    if not context.args:
        current = group_slowmode.get(chat_id, None)
        if current:
            await update.message.reply_text(
                f"⏱️ *_SLOW MODE STATUS_* 🐌\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🟢 *_Status:_* ON\n"
                f"⏱️ *_Delay:_* `{current} seconds`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"`/slowmodeoff` — _Disable_\n"
                f"`/slowmode 10` — _Change time_",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "⏱️ *_SLOW MODE_* 🐌\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "`/slowmode 5` — _5 sec delay_\n"
                "`/slowmode 15` — _15 sec delay_\n"
                "`/slowmode 30` — _30 sec delay_\n"
                "`/slowmodeoff` — _Disable_\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ *_Users ko har message ke beech wait karna hoga!_*",
                parse_mode="Markdown"
            )
        return
    try:
        seconds = int(context.args[0])
        if seconds <= 0:
            group_slowmode.pop(chat_id, None)
            if chat_id in last_message_time:
                del last_message_time[chat_id]
            await update.message.reply_text("✅ *_Slow Mode OFF!_* 🚀\n_Ab fast message kar sakte hain!_", parse_mode="Markdown")
        else:
            group_slowmode[chat_id] = seconds
            if chat_id not in last_message_time:
                last_message_time[chat_id] = {}
            await update.message.reply_text(
                f"✅ *_SLOW MODE ON!_* 🐌\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ *_Delay:_* `{seconds} seconds`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⚠️ *_Users ko {seconds}s wait karna hoga!_*\n"
                f"🗑️ _Fast messages =_ *DELETE*\n"
                f"👑 *_Admins exempt_*\n\n"
                f"`/slowmodeoff` — _Disable_",
                parse_mode="Markdown"
            )
    except:
        await update.message.reply_text("❌ *_Number do!_* `/slowmode 5`", parse_mode="Markdown")

async def cmd_slowmodeoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
        return
    group_slowmode.pop(chat_id, None)
    if chat_id in last_message_time:
        del last_message_time[chat_id]
    await update.message.reply_text("✅ *_Slow Mode OFF!_* 🚀\n_Ab fast message kar sakte hain!_ ⚡", parse_mode="Markdown")

# ================== GAME CENTER ==================
async def cmd_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("🎯 Number Guess (1-100)", callback_data="gm_guess")],
        [InlineKeyboardButton("✊ Rock Paper Scissors", callback_data="gm_rps")],
        [InlineKeyboardButton("🎲 Roll Dice", callback_data="gm_dice")],
        [InlineKeyboardButton("❓ Quiz Time", callback_data="gm_quiz")],
        [InlineKeyboardButton("🔤 Word Scramble", callback_data="gm_scramble")],
    ]
    await update.message.reply_text(
        "🎮 *_GAME CENTER_* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💎 *_Button dabao aur khelo!_* 💎\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "_🏆 Jeetne wale ko XP milega!_ ⭐",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def game_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    choice = query.data
    
    if choice == "gm_guess":
        number = random.randint(1, 100)
        group_games[chat_id] = {"type": "guess", "number": number, "attempts": 0}
        await query.edit_message_text(
            "🎯 *_NUMBER GUESS GAME!_* 🔢\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🤔 _Maine 1-100 ke beech ek number socha!_\n"
            "💬 *_Chat mein guess karo!_*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "_Example: 50_\n\n"
            "🔢 _Guess karo abhi!_ ⚡",
            parse_mode="Markdown"
        )
    elif choice == "gm_rps":
        group_games[chat_id] = {"type": "rps"}
        await query.edit_message_text(
            "✊ *_ROCK PAPER SCISSORS!_* ✂️\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💬 *_Chat mein type karo:_*\n"
            "🪨 `rock` | 📄 `paper` | ✂️ `scissors`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "_Bot bhi apni choice dega!_ 🤖",
            parse_mode="Markdown"
        )
    elif choice == "gm_dice":
        dice_num = random.randint(1, 6)
        dice_faces = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        await query.edit_message_text(
            f"🎲 *_DICE ROLL!_* 🎲\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{dice_faces[dice_num]}  *_Rolled:_* `{dice_num}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"_🎲 Phir se khelo:_ `/dice`",
            parse_mode="Markdown"
        )
    elif choice == "gm_quiz":
        questions = [
            {"q": "🌍 *_India ki capital kya hai?_*", "a": "delhi"},
            {"q": "🧮 *_15 + 27 kitna hota hai?_*", "a": "42"},
            {"q": "🎬 *_'DDLJ' ke hero kaun hain?_*", "a": "shah rukh khan"},
            {"q": "🏏 *_Sabse zyada ODI centuries?_*", "a": "sachin tendulkar"},
            {"q": "💻 *_Python kab launch hui?_*", "a": "1991"},
        ]
        q = random.choice(questions)
        group_games[chat_id] = {"type": "quiz", "answer": q["a"]}
        await query.edit_message_text(
            f"❓ *_QUIZ TIME!_* 🧠\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 {q['q']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 *_Chat mein answer likho!_*",
            parse_mode="Markdown"
        )
    elif choice == "gm_scramble":
        words = ["python", "telegram", "coding", "india", "game", "computer", "keyboard", "internet", "bot", "premium"]
        word = random.choice(words)
        scrambled = ''.join(random.sample(word, len(word)))
        group_games[chat_id] = {"type": "scramble", "answer": word}
        await query.edit_message_text(
            f"🔤 *_WORD SCRAMBLE!_* 🧩\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔀 *_Scrambled:_* `{scrambled}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 *_Chat mein sahi word likho!_*\n"
            f"📏 _Hint: {len(word)} letters_",
            parse_mode="Markdown"
        )

# ================== PREMIUM COMMANDS ==================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    if chat_type == ChatType.PRIVATE:
        if user_id == OWNER_USER_ID:
            user_history[chat_id] = []
            await update.message.reply_text(
                "👑 *_WELCOME BACK BOSS!_* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 *_AVANTIKA AI — PREMIUM_* 💎\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ *_Sab features 100% working!_*\n"
                "🔥 *_Premium Text Formatting_*\n"
                "📋 `/help` — _Full Command List_\n\n"
                "_Bolo boss! Kya karna hai?_ 🔥",
                parse_mode="Markdown"
            )
        elif is_allowed(user_id):
            user_history[chat_id] = []
            await update.message.reply_text(
                "✅ *_Access Granted!_* 🔓\n\n"
                "💎 *_AVANTIKA AI — PREMIUM_* 💎\n\n"
                "💬 *_Ask me anything!_* 🔥\n"
                "_Main multi-language hu, jo bolo same language mein jawab dunga!_ 🌍",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("🔒 *_Access Denied!_* ❌", parse_mode="Markdown")
    else:
        user_history[chat_id] = []
        await update.message.reply_text(
            "👋 *_AVANTIKA AI — PREMIUM_* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 *_Admin:_* `/activate` _karo_ ⚡\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💎 *_PREMIUM FEATURES:_*\n"
            "• _AI Chat_ | 🎮 _Games_ | 📊 _Polls_\n"
            "• 🌙 _Night Mode_ | ⏱️ _Slow Mode_\n"
            "• 🏆 _Ranks_ | 🔞 _Filters_ | 📱 _AFK_\n\n"
            "📋 `/help` — _Sab commands dekho!_ 💬\n\n"
            "_🔥 Activate karo — DHAMAKA! 🔥_",
            parse_mode="Markdown"
        )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *_AVANTIKA AI — PREMIUM HELP_* 💎\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👑 *_ADMIN COMMANDS:_*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 `/activate` — _Bot ON_\n"
        "🔹 `/deactivate` — _Bot OFF_\n"
        "🔹 `/mute 10m` — _Mute user (reply)_\n"
        "🔹 `/unmute` — _Unmute user (reply)_\n"
        "🔹 `/ban` — _Ban user (reply/ID)_\n"
        "🔹 `/unban ID` — _Unban user_\n"
        "🔹 `/warn` — _Warning (reply)_\n"
        "🔹 `/clearwarns` — _Reset warnings_\n"
        "🔹 `/setrules` — _Set group rules_\n"
        "🔹 `/setwelcome` — _Custom welcome_\n"
        "🔹 `/setgoodbye` — _Custom goodbye_\n"
        "🔹 `/addnote` — _Add note_\n"
        "🔹 `/clearnotes` — _Clear notes_\n"
        "🔹 `/pin` — _Pin message (reply)_\n"
        "🔹 `/unpin` — _Unpin all_\n"
        "🔹 `/addfilter` — _Word filter_\n"
        "🔹 `/rmfilter` — _Remove filter_\n"
        "🔹 `/slowmode 5` — _Slow mode_\n"
        "🔹 `/slowmodeoff` — _Slow mode OFF_\n"
        "🔹 `/nightmode 22 6` — _Night mode_\n"
        "🔹 `/nightmodeoff` — _Night mode OFF_\n"
        "🔹 `/poll \"Q\" \"A\" \"B\"` — _Create poll_\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 *_USER COMMANDS:_*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔸 `/help` — _This help_\n"
        "🔸 `/info` — _Group/User info_\n"
        "🔸 `/id` — _User ID_\n"
        "🔸 `/rules` — _Group rules_\n"
        "🔸 `/notes` — _Notes list_\n"
        "🔸 `/filters` — _Filter list_\n"
        "🔸 `/rank` — _Your XP_\n"
        "🔸 `/leaderboard` — _Top 10_\n"
        "🔸 `/game` — _Game center_ 🎮\n"
        "🔸 `/afk reason` — _AFK mode_\n"
        "🔸 `/stats` — _Group stats_\n"
        "🔸 `/flip` — _Coin flip_\n"
        "🔸 `/dice` — _Dice roll_\n"
        "🔸 `/choose A or B` — _Random choose_\n"
        "🔸 `/fact` — _Random fact_\n"
        "🔸 `/joke` — _Hindi joke_\n"
        "🔸 `/shayari` — _Shayari_\n"
        "🔸 `/quote` — _Motivational quote_\n"
        "🔸 `/google query` — _Google search_\n"
        "🔸 `/youtube query` — _YouTube search_\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

async def cmd_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text(
            "❌ *_ADMIN ONLY!_* 👑\n\n"
            "1️⃣ _Bot ko_ *ADMIN* _banao_\n"
            "2️⃣ _Sab_ *permissions ON* _karo_\n"
            "3️⃣ `/activate` _karo_",
            parse_mode="Markdown"
        )
        return
    active_groups[chat_id] = True
    user_history[chat_id] = []
    await update.message.reply_text(
        "✅ *_ACTIVATED!_* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *_AVANTIKA AI — LIVE!_* 🌟\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💎 *_ALL SYSTEMS GO:_*\n"
        "• 💬 _AI Chat — Premium Replies_\n"
        "• 🎮 _Games — 5 Types_\n"
        "• 📊 _Polls — Live Voting_\n"
        "• 🏆 _Ranks — XP System_\n"
        "• 🌙 _Night Mode — Auto Delete_\n"
        "• ⏱️ _Slow Mode — Rate Limit_\n"
        "• 🔞 _Filters — Auto Delete_\n"
        "• 🔇 _Mute_ | 🔨 _Ban_ | ⚠️ _Warn_\n\n"
        "📋 `/help` — _All Commands_\n"
        "❌ `/deactivate` — _OFF_\n\n"
        "_🔥 DHAMAKA MACH GAYA! 🔥_",
        parse_mode="Markdown"
    )

async def cmd_deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
        return
    active_groups[chat_id] = False
    await update.message.reply_text("🔴 *_DEACTIVATED!_*\n`/activate` _se wapas ON karo!_ ⚡", parse_mode="Markdown")

# ================== MUTE/UNMUTE ==================
async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ *_Sirf Group mein kaam karega!_*", parse_mode="Markdown")
        return
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
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
            await update.message.reply_text("❌ *_User nahi mila!_*", parse_mode="Markdown")
            return
    else:
        await update.message.reply_text(
            "🔇 *_MUTE SYSTEM_* 🇮🇳\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *_Reply karke:_*\n"
            "`/mute 10s` — _10 seconds_\n"
            "`/mute 5m` — _5 minutes_\n"
            "`/mute 2h` — _2 hours_\n"
            "`/mute 1d` — _1 day_\n\n"
            "📌 *_ID se:_*\n"
            "`/mute 123456 2h`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⏰ *_Auto Unmute ON_*\n"
            "🔊 `/unmute` _reply — Manual_",
            parse_mode="Markdown"
        )
        return
    if not target or target.id == update.effective_user.id or target.is_bot:
        return
    minutes = parse_time(time_str)
    if not minutes or minutes > 43200 or minutes <= 0:
        await update.message.reply_text("❌ *_Invalid time!_* `10s` `5m` `2h` `1d`", parse_mode="Markdown")
        return
    now = get_ist_now()
    until = now + timedelta(minutes=minutes)
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id, user_id=target.id,
            permissions=ChatPermissions(
                can_send_messages=False, can_send_audios=False, can_send_documents=False,
                can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
                can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
                can_add_web_page_previews=False, can_change_info=False,
                can_invite_users=False, can_pin_messages=False
            ),
            until_date=until
        )
        name = target.first_name + (f" {target.last_name}" if target.last_name else "")
        await update.message.reply_text(
            f"🔇 *_MUTED!_* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *_User:_* *{name}*\n"
            f"🆔 *_ID:_* `{target.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ *_Duration:_* {format_time(minutes)}\n"
            f"📅 *_Muted:_* `{now.strftime('%I:%M %p, %d %b')}`\n"
            f"🔓 *_Unmute:_* `{until.strftime('%I:%M %p, %d %b')}`\n\n"
            f"⏰ *_Auto Unmute ON_*\n"
            f"🔊 `/unmute` _reply — Manual_",
            parse_mode="Markdown"
        )
        async def auto_unmute():
            await asyncio.sleep(minutes * 60)
            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat_id, user_id=target.id,
                    permissions=ChatPermissions(
                        can_send_messages=True, can_send_audios=True, can_send_documents=True,
                        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                        can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                        can_add_web_page_previews=True, can_change_info=False,
                        can_invite_users=True, can_pin_messages=False
                    )
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ *_AUTO UNMUTED!_*\n👤 *{name}*\n⏱️ {format_time(minutes)} _ka mute khatam!_\n💬 _Ab message kar sakta hai!_ 🎉",
                    parse_mode="Markdown"
                )
            except:
                pass
        asyncio.create_task(auto_unmute())
    except Exception as e:
        await update.message.reply_text("❌ *_Mute Failed! Bot ko Ban Users permission do!_* 👑", parse_mode="Markdown")

async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
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
        await update.message.reply_text("🔊 *_Reply karo ya ID do!_*", parse_mode="Markdown")
        return
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id, user_id=target.id,
            permissions=ChatPermissions(
                can_send_messages=True, can_send_audios=True, can_send_documents=True,
                can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                can_add_web_page_previews=True, can_change_info=False,
                can_invite_users=True, can_pin_messages=False
            )
        )
        await update.message.reply_text(f"✅ *_UNMUTED!_* 🔓\n👤 *{target.first_name}*\n💬 _Ab message kar sakta hai!_ 🎉", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ *_Failed!_*", parse_mode="Markdown")

# ================== BAN/UNBAN ==================
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
        return
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    elif context.args:
        try:
            member = await context.bot.get_chat_member(chat_id, int(context.args[0]))
            target = member.user
        except:
            await update.message.reply_text("❌ *_User nahi mila!_*", parse_mode="Markdown")
            return
    if not target or target.id == update.effective_user.id or target.is_bot:
        await update.message.reply_text("❌ *_Ban nahi kar sakta!_*", parse_mode="Markdown")
        return
    try:
        await context.bot.ban_chat_member(chat_id, target.id)
        await update.message.reply_text(
            f"🔨 *_BANNED!_* 🚫\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *_User:_* *{target.first_name}*\n"
            f"🆔 *_ID:_* `{target.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔓 `/unban {target.id}`",
            parse_mode="Markdown"
        )
    except:
        await update.message.reply_text("❌ *_Ban Failed! Bot ko Ban Users permission do!_*", parse_mode="Markdown")

async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("📝 `/unban user_id`", parse_mode="Markdown")
        return
    try:
        uid = int(context.args[0])
        await context.bot.unban_chat_member(chat_id, uid)
        await update.message.reply_text(f"✅ *_UNBANNED!_* 🔓\n🆔 `{uid}`\n💬 _Ab user wapas aa sakta hai!_", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ *_Failed!_*", parse_mode="Markdown")

# ================== SIMPLE COMMANDS ==================
async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin!_* 👑", parse_mode="Markdown"); return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ *_Kisi message pe reply karo!_*", parse_mode="Markdown"); return
    target = update.message.reply_to_message.from_user
    if target.is_bot: return
    if chat_id not in group_warnings: group_warnings[chat_id] = {}
    if target.id not in group_warnings[chat_id]: group_warnings[chat_id][target.id] = 0
    group_warnings[chat_id][target.id] += 1
    count = group_warnings[chat_id][target.id]
    if count >= 3:
        try:
            await context.bot.restrict_chat_member(chat_id=chat_id, user_id=target.id, permissions=ChatPermissions(can_send_messages=False), until_date=get_ist_now() + timedelta(hours=1))
            await update.message.reply_text(f"🚫 *3 WARNINGS — MUTED!*\n👤 *{target.first_name}*\n⏱️ 1 hour", parse_mode="Markdown")
            group_warnings[chat_id][target.id] = 0
        except: pass
    else:
        await update.message.reply_text(f"⚠️ *_WARNING {count}/3_*\n👤 *{target.first_name}*\n⚠️ 3 = Auto Mute!", parse_mode="Markdown")

async def cmd_clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin!_* 👑", parse_mode="Markdown"); return
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if chat_id in group_warnings and target.id in group_warnings[chat_id]: group_warnings[chat_id][target.id] = 0
        await update.message.reply_text(f"✅ *_Cleared for {target.first_name}!_*", parse_mode="Markdown")
    else:
        group_warnings[chat_id] = {}
        await update.message.reply_text("✅ *_Sab warnings cleared!_*", parse_mode="Markdown")

# ================== QUICK COMMANDS ==================
async def cmd_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin!_* 👑", parse_mode="Markdown"); return
    if len(context.args) < 3:
        await update.message.reply_text("📊 `/poll \"Question\" \"A\" \"B\" \"C\"`", parse_mode="Markdown"); return
    text = " ".join(context.args)
    parts = re.findall(r'"([^"]*)"', text)
    if len(parts) < 3:
        await update.message.reply_text("❌ *_Quotes use karo!_*", parse_mode="Markdown"); return
    question, options = parts[0], parts[1:]
    if chat_id not in group_polls: group_polls[chat_id] = {}
    pid = str(len(group_polls[chat_id]) + 1)
    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{opt} (0)", callback_data=f"vt_{pid}_{i}")])
    keyboard.append([InlineKeyboardButton("📊 Results", callback_data=f"rs_{pid}")])
    group_polls[chat_id][pid] = {"question": question, "options": options, "votes": {i: set() for i in range(len(options))}}
    await update.message.reply_text(
        f"📊 *_POLL #{pid}_*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*Q:* {question}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👇 *_Vote karo!_*",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

async def poll_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    data = query.data
    if data.startswith("vt_"):
        _, pid, oid = data.split("_"); oid = int(oid)
        if chat_id in group_polls and pid in group_polls[chat_id]:
            poll = group_polls[chat_id][pid]
            for v in poll["votes"].values(): v.discard(uid)
            poll["votes"][oid].add(uid)
            keyboard = []
            for i, opt in enumerate(poll["options"]):
                count = len(poll["votes"][i])
                keyboard.append([InlineKeyboardButton(f"{opt} ({count})", callback_data=f"vt_{pid}_{i}")])
            keyboard.append([InlineKeyboardButton("📊 Results", callback_data=f"rs_{pid}")])
            try: await query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
            except: pass
            await query.answer("✅ *_Vote recorded!_*")
    elif data.startswith("rs_"):
        pid = data.split("_")[1]
        if chat_id in group_polls and pid in group_polls[chat_id]:
            poll = group_polls[chat_id][pid]
            total = sum(len(v) for v in poll["votes"].values())
            result_text = f"📊 *_POLL #{pid} RESULTS_*\n\n"
            result_text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
            result_text += f"*Q:* {poll['question']}\n"
            result_text += f"📥 *Total:* {total} votes\n"
            result_text += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, opt in enumerate(poll["options"]):
                vc = len(poll["votes"][i])
                pct = (vc/total*100) if total > 0 else 0
                bar = "█" * int(pct/5)
                result_text += f"*{opt}:* {vc} ({pct:.1f}%)\n{bar}\n\n"
            await query.edit_message_text(result_text, parse_mode="Markdown")
            await query.answer("📊 *_Results!_*")

# ================== SIMPLE COMMANDS (CONTINUED) ==================
async def cmd_setrules(update, context):
    chat_id = update.effective_chat.id
    if not context.args: return
    group_rules[chat_id] = " ".join(context.args)
    await update.message.reply_text("✅ *_Rules Set!_* 📜", parse_mode="Markdown")

async def cmd_rules(update, context):
    chat_id = update.effective_chat.id
    if chat_id in group_rules:
        await update.message.reply_text(f"📜 *_GROUP RULES_*\n\n{group_rules[chat_id]}", parse_mode="Markdown")
    else:
        await update.message.reply_text("📜 *_No rules set!_*", parse_mode="Markdown")

async def cmd_addnote(update, context):
    chat_id = update.effective_chat.id
    if not context.args: return
    if chat_id not in group_notes: group_notes[chat_id] = []
    group_notes[chat_id].append(" ".join(context.args))
    await update.message.reply_text(f"✅ *_Note Added!_* 📝 (#{len(group_notes[chat_id])})", parse_mode="Markdown")

async def cmd_notes(update, context):
    chat_id = update.effective_chat.id
    if chat_id in group_notes and group_notes[chat_id]:
        nl = "\n".join([f"{i+1}. _{n}_" for i, n in enumerate(group_notes[chat_id])])
        await update.message.reply_text(f"📝 *_NOTES_*\n\n{nl}", parse_mode="Markdown")
    else:
        await update.message.reply_text("📝 *_No notes!_*", parse_mode="Markdown")

async def cmd_clearnotes(update, context):
    chat_id = update.effective_chat.id
    group_notes[chat_id] = []
    await update.message.reply_text("✅ *_Cleared!_*", parse_mode="Markdown")

async def cmd_pin(update, context):
    if not update.message.reply_to_message: return
    try:
        await update.message.reply_to_message.pin()
        await update.message.reply_text("📌 *_Pinned!_* ✅", parse_mode="Markdown")
    except: pass

async def cmd_unpin(update, context):
    try: await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    except: pass

async def cmd_setwelcome(update, context):
    chat_id = update.effective_chat.id
    if not context.args: return
    group_welcome_msgs[chat_id] = " ".join(context.args)
    await update.message.reply_text("✅ *_Welcome Set!_* ✨", parse_mode="Markdown")

async def cmd_setgoodbye(update, context):
    chat_id = update.effective_chat.id
    if not context.args: return
    group_goodbye_msgs[chat_id] = " ".join(context.args)
    await update.message.reply_text("✅ *_Goodbye Set!_* 👋", parse_mode="Markdown")

async def cmd_addfilter(update, context):
    chat_id = update.effective_chat.id
    if not context.args: return
    word = " ".join(context.args).lower()
    if chat_id not in group_filters: group_filters[chat_id] = []
    if word not in group_filters[chat_id]:
        group_filters[chat_id].append(word)
        await update.message.reply_text(f"🔞 *_Filtered:_* `{word}`", parse_mode="Markdown")

async def cmd_rmfilter(update, context):
    chat_id = update.effective_chat.id
    if not context.args: return
    word = " ".join(context.args).lower()
    if chat_id in group_filters and word in group_filters[chat_id]:
        group_filters[chat_id].remove(word)
        await update.message.reply_text(f"✅ *_Removed:_* `{word}`", parse_mode="Markdown")

async def cmd_filters(update, context):
    chat_id = update.effective_chat.id
    if chat_id in group_filters and group_filters[chat_id]:
        fl = "\n".join([f"• `{w}`" for w in group_filters[chat_id]])
        await update.message.reply_text(f"🔞 *_FILTERS_*\n{fl}", parse_mode="Markdown")
    else:
        await update.message.reply_text("🔞 *_No filters!_*", parse_mode="Markdown")

async def cmd_rank(update, context):
    chat_id = update.effective_chat.id
    uid = update.effective_user.id
    if update.message.reply_to_message: uid = update.message.reply_to_message.from_user.id
    if chat_id not in group_ranks: group_ranks[chat_id] = {}
    score = group_ranks[chat_id].get(uid, 0)
    if score < 50: level = "🌱 *_Beginner_*"
    elif score < 200: level = "🌟 *_Active_*"
    elif score < 500: level = "💎 *_Pro_*"
    else: level = "🔥 *_LEGEND_*"
    await update.message.reply_text(f"🏆 *_RANK_*\n⭐ XP: {score}\n🏅 Level: {level}", parse_mode="Markdown")

async def cmd_leaderboard(update, context):
    chat_id = update.effective_chat.id
    if chat_id not in group_ranks or not group_ranks[chat_id]:
        await update.message.reply_text("🏆 *_No XP yet! Chat karo!_*", parse_mode="Markdown"); return
    top = sorted(group_ranks[chat_id].items(), key=lambda x: x[1], reverse=True)[:10]
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lb = "🏆 *_LEADERBOARD_*\n\n"
    for i, (uid, score) in enumerate(top, 1):
        try:
            u = await context.bot.get_chat(uid); name = u.first_name
        except: name = f"User{uid}"
        lb += f"{medals.get(i, f'#{i}')} *{name}* — {score} XP\n"
    await update.message.reply_text(lb, parse_mode="Markdown")

async def cmd_afk(update, context):
    uid = update.effective_user.id
    reason = " ".join(context.args) if context.args else "AFK"
    group_afk[uid] = {"reason": reason, "time": get_ist_now(), "name": update.effective_user.first_name}
    await update.message.reply_text(f"😴 *_AFK ON!_*\n📝 _{reason}_", parse_mode="Markdown")

async def cmd_flip(update, context):
    await update.message.reply_text(f"🪙 *_FLIP!_*\n\n✨ *{random.choice(['Heads', 'Tails'])}*", parse_mode="Markdown")

async def cmd_dice(update, context):
    sides = int(context.args[0]) if context.args and context.args[0].isdigit() else 6
    result = random.randint(1, max(2, sides))
    await update.message.reply_text(f"🎲 *_DICE!_*\n\n✨ `{result}` (1-{sides})", parse_mode="Markdown")

async def cmd_choose(update, context):
    if not context.args: return
    text = " ".join(context.args)
    options = [o.strip() for o in text.replace(" or ", ",").split(",") if o.strip()]
    if len(options) >= 2:
        await update.message.reply_text(f"🤔 *_CHOOSING..._*\n\n✨ *_I choose:_* *{random.choice(options)}*", parse_mode="Markdown")

async def cmd_fact(update, context):
    facts = [
        "🐙 *_Octopus ke 3 dil hote hain!_*",
        "🍯 *_Honey kabhi kharab nahi hoti!_*",
        "⚡ *_Lightning din mein 8.6 million bar girti hai!_*",
        "🧠 *_Human brain 20W electricity generate karta hai!_*",
        "🦋 *_Butterflies apne pairo se taste karti hain!_*",
        "🌍 *_Earth ka 71% surface paani se dhaka hai!_*",
    ]
    await update.message.reply_text(f"🤯 *_RANDOM FACT!_*\n\n{random.choice(facts)}", parse_mode="Markdown")

async def cmd_joke(update, context):
    jokes = [
        "😂 *_Teacher:_* '_Late kyun?'_\n*_Student:_* '_Corner tha ghar se nikalte time!_'",
        "🤣 *_Santa:_* '_Online pizza order kiya... ab tak download nahi hua!_'",
        "😆 *_Pappu:_* '_Papa, aaj sirf maine answer diya!'_\n*_Papa:_* '_Kya pucha?'_\n*_Pappu:_* '_Homework kaun nahi laya?_'",
    ]
    await update.message.reply_text(f"😄 *_JOKE!_*\n\n{random.choice(jokes)}", parse_mode="Markdown")

async def cmd_shayari(update, context):
    s = [
        "💕 *_Mohabbat mein humne khoya hai sab kuch,_*\n*_Phir bhi teri yaadon mein khoye rehte hain..._*",
        "🌟 *_Zindagi ek safar hai suhana,_*\n*_Yahan kal kya ho kisne jaana..._*",
        "🔥 *_Duniya ki bheed mein tanha the hum,_*\n*_Jab tak tumse na mile the..._*",
    ]
    await update.message.reply_text(random.choice(s), parse_mode="Markdown")

async def cmd_quote(update, context):
    q = [
        "💭 *_'The only way to do great work is to love what you do.'_* — Steve Jobs",
        "💭 *_'Believe you can and you're halfway there.'_* — Roosevelt",
        "💭 *_'Success is not final, failure is not fatal.'_* — Churchill",
    ]
    await update.message.reply_text(random.choice(q), parse_mode="Markdown")

async def cmd_info(update, context):
    if update.effective_chat.type == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(f"👤 *_USER INFO_*\n\n👤 *{u.first_name}*\n🆔 `{u.id}`\n📛 @{u.username or 'None'}", parse_mode="Markdown")
    else:
        c = await context.bot.get_chat(update.effective_chat.id)
        await update.message.reply_text(f"👥 *_GROUP INFO_*\n\n👥 *{c.title}*\n🆔 `{update.effective_chat.id}`", parse_mode="Markdown")

async def cmd_id(update, context):
    if update.message.reply_to_message:
        await update.message.reply_text(f"🆔 `{update.message.reply_to_message.from_user.id}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

async def cmd_stats(update, context):
    chat_id = update.effective_chat.id
    is_night = is_night_mode_active(chat_id)
    s = (
        f"📊 *_GROUP STATS_* 🔥\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 *_Notes:_* {len(group_notes.get(chat_id, []))}\n"
        f"🔞 *_Filters:_* {len(group_filters.get(chat_id, []))}\n"
        f"🏆 *_Ranked:_* {len(group_ranks.get(chat_id, {}))}\n"
        f"⏱️ *_Slowmode:_* {group_slowmode.get(chat_id, 'OFF')}s\n"
        f"🌙 *_Night Mode:_* {'*ON 🔴*' if is_night else 'OFF 🟢'}\n"
        f"✨ *_Custom Welcome:_* {'*YES*' if chat_id in group_welcome_msgs else 'Default'}\n"
        f"📜 *_Rules:_* {'*SET*' if chat_id in group_rules else 'Not set'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(s, parse_mode="Markdown")

async def cmd_google(update, context):
    if context.args:
        await update.message.reply_text(f"🔍 *_Search:_* [Click here](https://www.google.com/search?q={'+'.join(context.args)})", parse_mode="Markdown", disable_web_page_preview=False)

async def cmd_youtube(update, context):
    if context.args:
        await update.message.reply_text(f"▶️ *_YouTube:_* [Click here](https://www.youtube.com/results?search_query={'+'.join(context.args)})", parse_mode="Markdown", disable_web_page_preview=False)

# ================== OWNER COMMANDS ==================
async def cmd_adduser(update, context):
    if update.effective_user.id != OWNER_USER_ID: return
    if context.args:
        try: allowed_users.add(int(context.args[0])); await update.message.reply_text(f"✅ `{context.args[0]}`", parse_mode="Markdown")
        except: pass

async def cmd_removeuser(update, context):
    if update.effective_user.id != OWNER_USER_ID: return
    if context.args:
        try:
            uid = int(context.args[0])
            if uid != OWNER_USER_ID: allowed_users.discard(uid); await update.message.reply_text(f"✅ `{uid}`", parse_mode="Markdown")
        except: pass

async def cmd_userlist(update, context):
    if update.effective_user.id != OWNER_USER_ID: return
    ul = "\n".join([f"• `{u}`" for u in allowed_users])
    await update.message.reply_text(f"👥 *_Users ({len(allowed_users)})_*\n{ul}", parse_mode="Markdown")

async def cmd_broadcast(update, context):
    if update.effective_user.id != OWNER_USER_ID or not context.args: return
    msg = "📢 *_BROADCAST_*\n\n" + " ".join(context.args)
    c = 0
    for u in allowed_users:
        try: await context.bot.send_message(u, msg, parse_mode="Markdown"); c += 1
        except: pass
    await update.message.reply_text(f"✅ *{c} users*", parse_mode="Markdown")

async def cmd_clear(update, context):
    if update.effective_user.id != OWNER_USER_ID: return
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    group_warnings[chat_id] = {}
    group_rules.pop(chat_id, None)
    group_notes[chat_id] = []
    group_filters[chat_id] = []
    if chat_id in group_ranks: group_ranks[chat_id] = {}
    group_games.pop(chat_id, None)
    await update.message.reply_text("✅ *_COMPLETE RESET!_* 🔄", parse_mode="Markdown")

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    msg = update.message
    
    # New members
    if msg.new_chat_members:
        await handle_new_members(update, context)
        return
    
    # Left members
    if msg.left_chat_member:
        await handle_left_members(update, context)
        return
    
    # Private chat
    if chat_type == ChatType.PRIVATE:
        if not is_allowed(user_id):
            await msg.reply_text("🔒 *_Access Denied!_* ❌", parse_mode="Markdown")
            return
    else:
        # Group must be activated
        if chat_id not in active_groups or not active_groups[chat_id]:
            return
        
        # ========== NIGHT MODE: DELETE MESSAGES ==========
        if is_night_mode_active(chat_id):
            admin_ids = await get_admin_ids(chat_id, context)
            if user_id not in admin_ids:
                try:
                    await msg.delete()
                except:
                    pass
                return
        
        # ========== SLOW MODE: DELETE FAST MESSAGES ==========
        if chat_id in group_slowmode:
            admin_ids = await get_admin_ids(chat_id, context)
            if user_id not in admin_ids:
                now = datetime.now().timestamp()
                if chat_id not in last_message_time:
                    last_message_time[chat_id] = {}
                last_time = last_message_time[chat_id].get(user_id, 0)
                delay = group_slowmode[chat_id]
                if now - last_time < delay:
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                last_message_time[chat_id][user_id] = now
    
    if not msg.text:
        return
    
    # ========== GAME HANDLING ==========
    if chat_id in group_games:
        game = group_games[chat_id]
        txt = msg.text.lower().strip()
        
        if game["type"] == "guess":
            try:
                guess_num = int(txt)
                game["attempts"] += 1
                if guess_num == game["number"]:
                    await msg.reply_text(
                        f"🎯 *_CORRECT!_* 🎉\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🔢 *_Number:_* {game['number']}\n"
                        f"📊 *_Attempts:_* {game['attempts']}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"🏆 *_Badhai ho! Jeet gaye!_* 🏆",
                        parse_mode="Markdown"
                    )
                    del group_games[chat_id]
                    return
                elif guess_num < game["number"]:
                    await msg.reply_text(f"📈 *_HIGHER!_* ⬆️\n_Attempt #{game['attempts']}: {guess_num} is too low_", parse_mode="Markdown")
                else:
                    await msg.reply_text(f"📉 *_LOWER!_* ⬇️\n_Attempt #{game['attempts']}: {guess_num} is too high_", parse_mode="Markdown")
                return
            except:
                pass
        
        elif game["type"] == "rps":
            if txt in ["rock", "paper", "scissors"]:
                bot_choice = random.choice(["rock", "paper", "scissors"])
                emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
                if txt == bot_choice: result = "🤝 *_TIE!_*"
                elif (txt == "rock" and bot_choice == "scissors") or (txt == "paper" and bot_choice == "rock") or (txt == "scissors" and bot_choice == "paper"): result = "🎉 *_YOU WIN!_*"
                else: result = "😢 *_BOT WINS!_*"
                await msg.reply_text(
                    f"✊ *_RPS RESULT!_*\n\n"
                    f"🙋 *_You:_* {emojis[txt]} _{txt}_\n"
                    f"🤖 *_Bot:_* {emojis[bot_choice]} _{bot_choice}_\n\n"
                    f"{result}",
                    parse_mode="Markdown"
                )
                del group_games[chat_id]
                return
        
        elif game["type"] == "quiz":
            if txt == game["answer"]:
                await msg.reply_text("✅ *_CORRECT!_* 🎉\n\n_Bahut accha! Aap jeet gaye!_ 🏆", parse_mode="Markdown")
                del group_games[chat_id]
                return
        
        elif game["type"] == "scramble":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *_CORRECT!_* 🎉\n\n_Word:_ *{game['answer']}*\n_Bahut accha!_ 🏆", parse_mode="Markdown")
                del group_games[chat_id]
                return
    
    # ========== FILTER CHECK ==========
    if chat_id in group_filters:
        text_lower = msg.text.lower()
        for word in group_filters[chat_id]:
            if word in text_lower:
                try: await msg.delete()
                except: pass
                await msg.reply_text(f"🔞 *_Filtered word detected!_* ⚠️\n👤 {update.effective_user.first_name}\n_Messages delete ho gaya!_", parse_mode="Markdown")
                return
    
    # ========== AFK CHECK ==========
    if msg.reply_to_message and msg.reply_to_message.from_user:
        replied_uid = msg.reply_to_message.from_user.id
        if replied_uid in group_afk and replied_uid != user_id:
            afk = group_afk[replied_uid]
            diff = get_ist_now() - afk["time"]
            hours, rem = divmod(int(diff.total_seconds()), 3600)
            mins, _ = divmod(rem, 60)
            ts = f"{hours}h {mins}m" if hours else f"{mins}m"
            await msg.reply_text(
                f"😴 *_USER AFK HAI!_*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *{afk.get('name', 'User')}*\n"
                f"📝 _{afk['reason']}_\n"
                f"⏱️ _{ts} ago_\n"
                f"━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode="Markdown"
            )
    
    # ========== RANK UPDATE ==========
    if chat_type != ChatType.PRIVATE:
        if chat_id not in group_ranks: group_ranks[chat_id] = {}
        if user_id not in group_ranks[chat_id]: group_ranks[chat_id][user_id] = 0
        group_ranks[chat_id][user_id] += random.randint(1, 3)
    
    # ========== AI REPLY ==========
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    try:
        reply = get_ai_reply(msg.text, chat_id)
        if chat_id not in user_history: user_history[chat_id] = []
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
    
    for cmd, handler in commands.items():
        app.add_handler(CommandHandler(cmd, handler))
    
    app.add_handler(CallbackQueryHandler(game_button_click, pattern="^gm_"))
    app.add_handler(CallbackQueryHandler(poll_button_click, pattern="^(vt_|rs_)"))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("👑 AVANTIKA AI PREMIUM — ALL FEATURES 100% WORKING! 🔥")
    print("✅ Night Mode: Messages AUTO DELETE")
    print("✅ Slow Mode: Fast messages DELETE")
    print("✅ Games: 5 Interactive Games")
    print("✅ Premium Text: Bold + Italic + Emojis")
    app.run_polling()

if __name__ == "__main__":
    main()
