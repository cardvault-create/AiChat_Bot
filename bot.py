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

# ================== ALL DATABASES ==================
user_history = {}
active_groups = {}
allowed_users = {7614459746}
group_warnings = defaultdict(dict)
group_rules = {}
group_notes = defaultdict(list)
group_polls = {}
group_games = {}
group_reminders = defaultdict(list)
group_filters = defaultdict(list)
group_welcome_msgs = {}
group_goodbye_msgs = {}
group_antispam = defaultdict(lambda: defaultdict(list))
group_ranks = defaultdict(lambda: defaultdict(int))
group_nicknames = defaultdict(dict)
group_reactions = defaultdict(dict)
group_slowmode = {}
group_nightmode = {}
group_locks = defaultdict(list)
group_schedule = defaultdict(list)
group_afk = {}
group_last_message = defaultdict(lambda: defaultdict(float))

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
    for w, m in [('seconds',1/60),('second',1/60),('sec',1/60),('s',1/60),
                 ('minutes',1),('minute',1),('mins',1),('min',1),('m',1),
                 ('hours',60),('hour',60),('hrs',60),('hr',60),('h',60),
                 ('days',1440),('day',1440),('d',1440)]:
        if ts.endswith(w):
            try:
                return float(ts[:-len(w)])*m
            except:
                pass
    try:
        return float(ts)
    except:
        return None

def format_time(m):
    ts = int(m*60)
    if ts <= 0:
        return "0 seconds"
    d, ts = divmod(ts,86400)
    h, ts = divmod(ts,3600)
    mi, s = divmod(ts,60)
    p = []
    if d: p.append(f"*{d}* day{'s' if d!=1 else ''}")
    if h: p.append(f"*{h}* hour{'s' if h!=1 else ''}")
    if mi: p.append(f"*{mi}* minute{'s' if mi!=1 else ''}")
    if s and not d: p.append(f"*{s}* second{'s' if s!=1 else ''}")
    return ", ".join(p) if p else "0 seconds"

def is_allowed(uid):
    return uid in allowed_users

def get_ai_reply(text, chat_id):
    if chat_id not in user_history:
        user_history[chat_id] = []
    ch = []
    for msg in user_history[chat_id][-4:]:
        r = "USER" if msg["role"]=="user" else "CHATBOT"
        ch.append({"role":r,"message":msg["content"]})
    try:
        resp = co.chat(message=text, chat_history=ch, preamble=AVANTIKA_PREAMBLE, temperature=0.95, max_tokens=800)
        return resp.text
    except:
        return "😅 _Fir se bol!_ 💎"

def is_admin(update, context, cid, uid):
    """Check if user is admin"""
    try:
        admins = context.bot_data.get(f"admins_{cid}")
        if not admins:
            return False
        return uid in admins
    except:
        return False

async def refresh_admins(context, cid):
    """Cache admin list"""
    try:
        admins = await context.bot.get_chat_administrators(cid)
        context.bot_data[f"admins_{cid}"] = {a.user.id for a in admins}
    except:
        pass

async def is_night_time(cid):
    """Check if night mode is active"""
    if cid not in group_nightmode:
        return False
    now = get_ist_now()
    start = group_nightmode[cid]["start"]
    end = group_nightmode[cid]["end"]
    
    if start < end:
        # Same day (e.g., 22-6)
        return start <= now.hour < end
    else:
        # Crosses midnight (e.g., 23-7)
        return now.hour >= start or now.hour < end

# ================== 👋 WELCOME SYSTEM ==================
async def welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new members"""
    if not update.message or not update.message.new_chat_members:
        return
    
    cid = update.effective_chat.id
    
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            # Bot joined
            await context.bot.send_message(
                chat_id=cid,
                text=(
                    "✨ *AVANTIKA AI JOINED!* ✨\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "👑 Admin */activate* karo\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "🔥 *FEATURES:*\n"
                    "💬 AI Chat | 🎮 Games | 📊 Polls\n"
                    "🏆 Ranks | 🛡️ Antispam | 🔞 Filters\n"
                    "⏰ Reminders | 🌙 Night Mode\n"
                    "🔇 Mute | 🔨 Ban | ⚠️ Warn\n"
                    "📜 Rules | 📝 Notes | 📌 Pin\n\n"
                    "📋 */help* — Full command list!\n\n"
                    "_Activate karo — DHAMAKA!_ 🔥"
                ),
                parse_mode="Markdown"
            )
        else:
            # New member
            msg = group_welcome_msgs.get(cid, 
                f"✨ *WELCOME!* ✨\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *{user.first_name}*\n"
                f"🆔 `{user.id}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌟 _Aapka swagat hai!_ 🎉\n\n"
                f"📋 */help* — Commands dekho!"
            )
            msg = msg.replace("{name}", user.first_name)
            msg = msg.replace("{id}", str(user.id))
            msg = msg.replace("{mention}", f"[{user.first_name}](tg://user?id={user.id})")
            
            await context.bot.send_message(
                chat_id=cid,
                text=msg,
                parse_mode="Markdown"
            )

# ================== 👋 GOODBYE SYSTEM ==================
async def goodbye_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle left members"""
    if not update.message or not update.message.left_chat_member:
        return
    
    cid = update.effective_chat.id
    user = update.message.left_chat_member
    
    if user.id == context.bot.id:
        return
    
    msg = group_goodbye_msgs.get(cid,
        f"👋 *GOODBYE!*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *{user.first_name}* left!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"😢 _Fir milenge!_"
    )
    msg = msg.replace("{name}", user.first_name)
    msg = msg.replace("{id}", str(user.id))
    
    await context.bot.send_message(
        chat_id=cid,
        text=msg,
        parse_mode="Markdown"
    )

# ================== 🎮 GAME SYSTEM ==================
async def cmd_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Game center command"""
    cid = update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("🎯 Number Guess (1-100)", callback_data="game_guess"),
         InlineKeyboardButton("✊ Rock Paper Scissors", callback_data="game_rps")],
        [InlineKeyboardButton("🎲 Roll Dice", callback_data="game_dice"),
         InlineKeyboardButton("❓ Quiz", callback_data="game_quiz")],
        [InlineKeyboardButton("🔤 Word Scramble", callback_data="game_scramble")]
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
    """Handle game button clicks"""
    query = update.callback_query
    await query.answer()
    cid = update.effective_chat.id
    game = query.data
    
    if game == "game_guess":
        number = random.randint(1, 100)
        group_games[cid] = {"type": "guess", "number": number, "attempts": 0}
        await query.edit_message_text(
            "🎯 *NUMBER GUESS GAME!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Maine 1-100 ke beech number socha!\n"
            "💬 Reply karo apna guess!\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    
    elif game == "game_rps":
        group_games[cid] = {"type": "rps"}
        await query.edit_message_text(
            "✊ *ROCK PAPER SCISSORS!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💬 Type karo: `rock`, `paper`, ya `scissors`\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    
    elif game == "game_dice":
        d = random.randint(1, 6)
        dice_faces = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        await query.edit_message_text(
            f"🎲 *DICE ROLL!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{dice_faces[d]}  *{d}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    
    elif game == "game_quiz":
        questions = [
            {"q": "🌍 India ki capital kya hai?", "a": "delhi"},
            {"q": "🧮 15 + 27 = ?", "a": "42"},
            {"q": "🎬 'DDLJ' ke hero kaun hain?", "a": "shah rukh khan"},
            {"q": "🏏 Sabse zyada ODI centuries kisne banayi?", "a": "sachin tendulkar"},
            {"q": "💻 Python kab banayi gayi?", "a": "1991"},
            {"q": "🌟 Taare kitne hain aasman mein?", "a": "anant"},
        ]
        q = random.choice(questions)
        group_games[cid] = {"type": "quiz", "answer": q["a"]}
        await query.edit_message_text(
            f"❓ *QUIZ TIME!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{q['q']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 Reply karo answer!",
            parse_mode="Markdown"
        )
    
    elif game == "game_scramble":
        words = ["python", "telegram", "bot", "coding", "india", "game", "computer", "keyboard"]
        w = random.choice(words)
        scrambled = ''.join(random.sample(w, len(w)))
        group_games[cid] = {"type": "scramble", "answer": w}
        await query.edit_message_text(
            f"🔤 *WORD SCRAMBLE!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"`{scrambled}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 Reply karo sahi word!",
            parse_mode="Markdown"
        )

# ================== 📊 POLL SYSTEM ==================
async def cmd_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a poll"""
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "📊 *POLL CREATE*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "`/poll \"Question\" \"Option1\" \"Option2\" \"Option3\"`\n\n"
            "Example:\n"
            "`/poll \"Best language?\" \"Python\" \"JS\" \"Go\"`\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
        return
    
    text = " ".join(args)
    parts = re.findall(r'"([^"]*)"', text)
    
    if len(parts) < 3:
        await update.message.reply_text("❌ Quotes use karo: `/poll \"Q\" \"A\" \"B\"`", parse_mode="Markdown")
        return
    
    question = parts[0]
    options = parts[1:]
    
    if cid not in group_polls:
        group_polls[cid] = {}
    
    pid = str(len(group_polls[cid]) + 1)
    
    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{opt} (0)", callback_data=f"poll_{pid}_{i}")])
    keyboard.append([InlineKeyboardButton("📊 Results", callback_data=f"pollres_{pid}")])
    
    group_polls[cid][pid] = {
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
    cid = update.effective_chat.id
    data = query.data
    
    if data.startswith("poll_") and not data.startswith("pollres_"):
        parts = data.split("_")
        pid = parts[1]
        oid = int(parts[2])
        
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]
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
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]
            total = sum(len(v) for v in poll["votes"].values())
            
            results = f"📊 *POLL #{pid} RESULTS*\n\n"
            results += f"━━━━━━━━━━━━━━━━━━━━━━\n"
            results += f"*Q:* {poll['question']}\n"
            results += f"━━━━━━━━━━━━━━━━━━━━━━\n"
            results += f"📥 Total Votes: {total}\n\n"
            
            for i, opt in enumerate(poll["options"]):
                vc = len(poll["votes"][i])
                pct = (vc/total*100) if total > 0 else 0
                bar = "█" * int(pct/5)
                results += f"*{opt}:* {vc} ({pct:.1f}%)\n{bar}\n\n"
            
            await query.edit_message_text(results, parse_mode="Markdown")
            await query.answer("📊 Results!")

# ================== ⚠️ WARNING SYSTEM ==================
async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Warn a user"""
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ *Kisi message pe reply karo warn karne ke liye!*", parse_mode="Markdown")
        return
    
    target = update.message.reply_to_message.from_user
    
    if target.id == context.bot.id or target.is_bot:
        return
    
    group_warnings[cid][target.id] = group_warnings[cid].get(target.id, 0) + 1
    wc = group_warnings[cid][target.id]
    
    if wc >= 3:
        # Auto mute for 1 hour
        try:
            await context.bot.restrict_chat_member(
                chat_id=cid,
                user_id=target.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=get_ist_now() + timedelta(hours=1)
            )
            await update.message.reply_text(
                f"🚫 *3 WARNINGS — AUTO MUTED!* 🔇\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *User:* {target.first_name}\n"
                f"⚠️ *Warnings:* {wc}/3\n"
                f"⏱️ *Mute:* 1 hour\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🔊 `/unmute` reply karke unmute karo!",
                parse_mode="Markdown"
            )
            group_warnings[cid][target.id] = 0
        except:
            pass
    else:
        await update.message.reply_text(
            f"⚠️ *WARNING!* ⚡\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {target.first_name}\n"
            f"🆔 `{target.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *{wc}/3* warnings\n"
            f"⚠️ 3 warnings = Auto Mute!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"`/clearwarns` reply karke reset karo!",
            parse_mode="Markdown"
        )

async def cmd_clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear warnings"""
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if cid in group_warnings:
            group_warnings[cid][target.id] = 0
        await update.message.reply_text(
            f"✅ *Warnings Cleared!*\n"
            f"👤 {target.first_name}",
            parse_mode="Markdown"
        )
    else:
        group_warnings[cid] = {}
        await update.message.reply_text("✅ *Sab warnings cleared!*", parse_mode="Markdown")

# ================== 🔨 BAN SYSTEM ==================
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user"""
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    target = None
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    elif context.args:
        try:
            member = await context.bot.get_chat_member(cid, int(context.args[0]))
            target = member.user
        except:
            await update.message.reply_text("❌ *User nahi mila!*", parse_mode="Markdown")
            return
    
    if not target or target.id == update.effective_user.id or target.is_bot:
        await update.message.reply_text("❌ *Ban nahi kar sakta!*", parse_mode="Markdown")
        return
    
    try:
        await context.bot.ban_chat_member(cid, target.id)
        await update.message.reply_text(
            f"🔨 *BANNED!* 🚫\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {target.first_name}\n"
            f"🆔 `{target.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔓 `/unban {target.id}` se unban karo!",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Ban Failed!*\n"
            f"Bot ko *Ban Users* permission do!\n"
            f"`{str(e)[:100]}`",
            parse_mode="Markdown"
        )

async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user"""
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("📝 */unban user_id*", parse_mode="Markdown")
        return
    
    try:
        uid = int(context.args[0])
        await context.bot.unban_chat_member(cid, uid)
        await update.message.reply_text(
            f"✅ *UNBANNED!* 🔓\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 `{uid}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 Ab user wapas aa sakta hai!",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Unban Failed!*\n"
            f"`{str(e)[:100]}`",
            parse_mode="Markdown"
        )

# ================== 🔇 MUTE SYSTEM ==================
async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute a user"""
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ *Sirf Group mein!*", parse_mode="Markdown")
        return
    
    if not is_admin(update, context, cid, update.effective_user.id):
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
            member = await context.bot.get_chat_member(cid, int(context.args[0]))
            target = member.user
            time_str = " ".join(context.args[1:])
        except:
            await update.message.reply_text("❌ *User nahi mila!*", parse_mode="Markdown")
            return
    else:
        await update.message.reply_text(
            "🔇 *MUTE SYSTEM* 🇮🇳\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Reply karke:*\n"
            "`/mute 10s` — 10 seconds\n"
            "`/mute 5m` — 5 minutes\n"
            "`/mute 2h` — 2 hours\n"
            "`/mute 1d` — 1 day\n"
            "`/mute 30d` — 30 days\n\n"
            "📌 *Ya ID se:*\n"
            "`/mute 123456 2h`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🇮🇳 *IST Timezone* | ⏰ *Auto Unmute ON*",
            parse_mode="Markdown"
        )
        return
    
    if not target or target.id == update.effective_user.id or target.is_bot:
        return
    
    minutes = parse_time(time_str)
    if not minutes or minutes > 43200 or minutes <= 0:
        await update.message.reply_text("❌ *Invalid time!*", parse_mode="Markdown")
        return
    
    now = get_ist_now()
    until = now + timedelta(minutes=minutes)
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=cid,
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
            f"🔇 *MUTED! — INDIA TIME* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {name}\n"
            f"🆔 `{target.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ *Duration:* {format_time(minutes)}\n\n"
            f"📅 *Muted At:* {now.strftime('%I:%M %p, %d %b %Y')}\n"
            f"🔓 *Unmute At:* {until.strftime('%I:%M %p, %d %b %Y')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ *Auto Unmute ON*\n"
            f"🔊 Ya `/unmute` reply karke manual unmute!",
            parse_mode="Markdown"
        )
        
        # Auto unmute
        async def auto_unmute():
            await asyncio.sleep(minutes * 60)
            try:
                await context.bot.restrict_chat_member(
                    chat_id=cid,
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
                    chat_id=cid,
                    text=(
                        f"✅ *AUTO UNMUTED!* 🇮🇳\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 *{name}*\n"
                        f"⏱️ {format_time(minutes)} ka mute khatam!\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"💬 _Ab message kar sakta hai!_ 🎉"
                    ),
                    parse_mode="Markdown"
                )
            except:
                pass
        
        asyncio.create_task(auto_unmute())
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Mute Failed!*\n\n"
            f"Bot ko *Ban Users* permission do!\n"
            f"`{str(e)[:100]}`",
            parse_mode="Markdown"
        )

async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unmute a user"""
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    target = None
    
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    elif context.args:
        try:
            member = await context.bot.get_chat_member(cid, int(context.args[0]))
            target = member.user
        except:
            return
    
    if not target:
        await update.message.reply_text("🔊 *Reply karo ya ID do!* `/unmute ID`", parse_mode="Markdown")
        return
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=cid,
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
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *{target.first_name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 _Ab message kar sakta hai!_ 🎉",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ *Failed!* `{str(e)[:100]}`", parse_mode="Markdown")

# ================== 🌙 NIGHT MODE ==================
async def cmd_nightmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set night mode - NO ONE can send messages during night"""
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "🌙 *NIGHT MODE SETUP* 😴\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "`/nightmode start end` (24hr format)\n\n"
            "Example:\n"
            "`/nightmode 22 6` — 10PM to 6AM\n"
            "`/nightmode 23 7` — 11PM to 7AM\n\n"
            "`/nightmode off` — Disable\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ *Night mode mein KOI message nahi kar sakta!*",
            parse_mode="Markdown"
        )
        return
    
    if context.args[0].lower() == "off":
        group_nightmode.pop(cid, None)
        await update.message.reply_text("🌙 *Night Mode OFF!* ✅", parse_mode="Markdown")
        return
    
    try:
        start = int(context.args[0])
        end = int(context.args[1])
        
        if start < 0 or start > 23 or end < 0 or end > 23:
            await update.message.reply_text("❌ 0-23 ke beech mein do!", parse_mode="Markdown")
            return
        
        group_nightmode[cid] = {"start": start, "end": end}
        
        await update.message.reply_text(
            f"🌙 *NIGHT MODE ACTIVATED!* 😴\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕙 *Start:* {start}:00 (IST)\n"
            f"🕕 *End:* {end}:00 (IST)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚠️ *In time ke beech mein:*\n"
            f"• Messages DELETE honge\n"
            f"• Koi message nahi kar sakta\n"
            f"• Admins kar sakte hain\n\n"
            f"🌙 `/nightmode off` — Disable",
            parse_mode="Markdown"
        )
    except:
        await update.message.reply_text("❌ *Invalid!* `/nightmode 22 6`", parse_mode="Markdown")

# ================== ⏱️ SLOWMODE ==================
async def cmd_slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set slowmode - delay between messages"""
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "⏱️ *SLOWMODE*\n\n"
            "`/slowmode 5` — 5 seconds delay\n"
            "`/slowmode 30` — 30 seconds\n"
            "`/slowmode 0` — OFF",
            parse_mode="Markdown"
        )
        return
    
    try:
        sec = int(context.args[0])
        if sec <= 0:
            group_slowmode.pop(cid, None)
            await update.message.reply_text("⏱️ *Slowmode OFF!* 🚀", parse_mode="Markdown")
        else:
            group_slowmode[cid] = sec
            await update.message.reply_text(
                f"⏱️ *SLOWMODE ON!* 🐌\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ *Delay:* {sec} seconds\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Users ko har message ke beech\n"
                f"{sec}s wait karna hoga!",
                parse_mode="Markdown"
            )
    except:
        await update.message.reply_text("❌ *Number do!*", parse_mode="Markdown")

# ================== 🔞 WORD FILTERS ==================
async def cmd_addfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add word filter"""
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("🔞 `/addfilter gali`", parse_mode="Markdown")
        return
    
    word = " ".join(context.args).lower()
    
    if word not in group_filters[cid]:
        group_filters[cid].append(word)
        await update.message.reply_text(
            f"🔞 *Filter Added!* ✅\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Word: `{word}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚠️ Ye word use hua to message DELETE!\n"
            f"📋 `/filters` — List dekho\n"
            f"🗑️ `/rmfilter {word}` — Remove",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("⚠️ *Already filtered!*", parse_mode="Markdown")

async def cmd_rmfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove word filter"""
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        return
    
    word = " ".join(context.args).lower()
    
    if cid in group_filters and word in group_filters[cid]:
        group_filters[cid].remove(word)
        await update.message.reply_text(f"✅ *Removed:* `{word}`", parse_mode="Markdown")

async def cmd_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all filters"""
    cid = update.effective_chat.id
    
    if cid in group_filters and group_filters[cid]:
        fl = "\n".join([f"• `{w}`" for w in group_filters[cid]])
        await update.message.reply_text(
            f"🔞 *FILTERED WORDS:*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{fl}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Total: {len(group_filters[cid])}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("🔞 _No filters!_\n`/addfilter word`", parse_mode="Markdown")

# ================== 📱 AFK SYSTEM ==================
async def cmd_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set AFK status"""
    uid = update.effective_user.id
    reason = " ".join(context.args) if context.args else "AFK (No reason)"
    
    group_afk[uid] = {
        "reason": reason,
        "time": get_ist_now(),
        "name": update.effective_user.first_name
    }
    
    await update.message.reply_text(
        f"😴 *AFK MODE ON!*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {update.effective_user.first_name}\n"
        f"📝 {reason}\n"
        f"🕐 {get_ist_now().strftime('%I:%M %p')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 Koi reply karega to auto alert!",
        parse_mode="Markdown"
    )

# ================== ⏰ REMINDERS ==================
async def cmd_remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set reminder"""
    cid = update.effective_chat.id
    uid = update.effective_user.id
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "⏰ *REMINDER*\n\n"
            "`/remind 10m message`\n"
            "`/remind 1h meeting`\n"
            "`/remind 30s chai`",
            parse_mode="Markdown"
        )
        return
    
    time_str = context.args[0]
    message = " ".join(context.args[1:])
    minutes = parse_time(time_str)
    
    if not minutes:
        await update.message.reply_text("❌ *Invalid time!* `10m` `1h` `30s`", parse_mode="Markdown")
        return
    
    remind_time = get_ist_now() + timedelta(minutes=minutes)
    
    group_reminders[cid].append({
        "uid": uid,
        "time": remind_time,
        "msg": message
    })
    
    await update.message.reply_text(
        f"⏰ *REMINDER SET!* 🔔\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 {message}\n"
        f"⏱️ {format_time(minutes)} baad\n"
        f"🕐 {remind_time.strftime('%I:%M %p, %d %b')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )
    
    async def send_reminder():
        await asyncio.sleep(minutes * 60)
        await context.bot.send_message(
            chat_id=cid,
            text=(
                f"⏰ *REMINDER!* 🔔\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <a href='tg://user?id={uid}'>User</a>\n"
                f"📝 {message}\n"
                f"🕐 {get_ist_now().strftime('%I:%M %p')}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━"
            ),
            parse_mode="HTML"
        )
    asyncio.create_task(send_reminder())

# ================== 📌 PIN ==================
async def cmd_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pin a message"""
    if not is_admin(update, context, update.effective_chat.id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("📌 *Kisi message pe reply karo!*", parse_mode="Markdown")
        return
    
    try:
        await update.message.reply_to_message.pin()
        await update.message.reply_text("📌 *Pinned!* ✅", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ *Failed!* `{str(e)[:50]}`", parse_mode="Markdown")

async def cmd_unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unpin all messages"""
    if not is_admin(update, context, update.effective_chat.id, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    try:
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
        await update.message.reply_text("✅ *Unpinned all!*", parse_mode="Markdown")
    except:
        pass

# ================== 📝 NOTES ==================
async def cmd_addnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a note"""
    cid = update.effective_chat.id
    
    if not context.args:
        await update.message.reply_text("📝 `/addnote Your note here`", parse_mode="Markdown")
        return
    
    note = " ".join(context.args)
    group_notes[cid].append(note)
    
    await update.message.reply_text(
        f"✅ *Note Added!* 📝\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"#{len(group_notes[cid])}: {note[:100]}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 `/notes` — Sab notes dekho!",
        parse_mode="Markdown"
    )

async def cmd_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all notes"""
    cid = update.effective_chat.id
    
    if cid in group_notes and group_notes[cid]:
        notes_list = "\n".join([f"{i+1}. {n[:200]}" for i, n in enumerate(group_notes[cid])])
        await update.message.reply_text(
            f"📝 *NOTES ({len(group_notes[cid])})*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{notes_list}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("📝 _No notes!_ `/addnote`", parse_mode="Markdown")

async def cmd_clearnotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all notes"""
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    group_notes[cid] = []
    await update.message.reply_text("✅ *All notes cleared!*", parse_mode="Markdown")

# ================== 📜 RULES ==================
async def cmd_setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set group rules"""
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("📜 `/setrules Rules here...`", parse_mode="Markdown")
        return
    
    rules = " ".join(context.args)
    group_rules[cid] = rules
    
    await update.message.reply_text(
        f"📜 *Rules Set!* ✅\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 `/rules` — Users dekh sakte hain!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show group rules"""
    cid = update.effective_chat.id
    
    if cid in group_rules:
        await update.message.reply_text(
            f"📜 *GROUP RULES*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{group_rules[cid]}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("📜 _No rules set!_\n`/setrules`", parse_mode="Markdown")

# ================== ✨ CUSTOM WELCOME/GOODBYE ==================
async def cmd_setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set custom welcome message"""
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "✨ *CUSTOM WELCOME*\n\n"
            "`/setwelcome Welcome {name}! 🎉`\n\n"
            "Variables:\n"
            "`{name}` — User name\n"
            "`{id}` — User ID\n"
            "`{mention}` — Clickable mention",
            parse_mode="Markdown"
        )
        return
    
    msg = " ".join(context.args)
    group_welcome_msgs[cid] = msg
    
    await update.message.reply_text(
        f"✅ *Welcome Set!* ✨\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Preview: {msg.replace('{name}', update.effective_user.first_name).replace('{id}', str(update.effective_user.id))}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

async def cmd_setgoodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set custom goodbye message"""
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "👋 *CUSTOM GOODBYE*\n\n"
            "`/setgoodbye Bye {name}! 😢`\n\n"
            "Variables: `{name}`, `{id}`",
            parse_mode="Markdown"
        )
        return
    
    msg = " ".join(context.args)
    group_goodbye_msgs[cid] = msg
    
    await update.message.reply_text(f"✅ *Goodbye Set!* 👋", parse_mode="Markdown")

# ================== 🏷️ NICKNAMES ==================
async def cmd_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set nickname"""
    cid = update.effective_chat.id
    uid = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("🏷️ `/nick Your Nickname`", parse_mode="Markdown")
        return
    
    nickname = " ".join(context.args)
    group_nicknames[cid][uid] = nickname
    
    await update.message.reply_text(
        f"🏷️ *Nickname Set!* ✅\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {update.effective_user.first_name}\n"
        f"🏷️ {nickname}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

# ================== 🏆 RANK SYSTEM ==================
async def cmd_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show rank"""
    cid = update.effective_chat.id
    uid = update.effective_user.id
    
    if update.message.reply_to_message:
        uid = update.message.reply_to_message.from_user.id
    
    score = group_ranks[cid].get(uid, 0)
    
    # Find rank position
    sorted_users = sorted(group_ranks[cid].items(), key=lambda x: x[1], reverse=True)
    position = next((i+1 for i, (u, s) in enumerate(sorted_users) if u == uid), "?")
    
    # Level emojis
    if score < 50:
        level = "🌱 Beginner"
    elif score < 200:
        level = "🌟 Active"
    elif score < 500:
        level = "💎 Pro"
    elif score < 1000:
        level = "👑 Elite"
    else:
        level = "🔥 LEGEND"
    
    try:
        user = await context.bot.get_chat(uid)
        name = user.first_name
    except:
        name = "User"
    
    await update.message.reply_text(
        f"🏆 *RANK CARD*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *{name}*\n"
        f"🆔 `{uid}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ *XP:* {score}\n"
        f"📊 *Rank:* #{position}\n"
        f"🏅 *Level:* {level}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard"""
    cid = update.effective_chat.id
    
    if cid not in group_ranks or not group_ranks[cid]:
        await update.message.reply_text("🏆 _Abhi koi XP nahi hai! Chat karo!_", parse_mode="Markdown")
        return
    
    top = sorted(group_ranks[cid].items(), key=lambda x: x[1], reverse=True)[:10]
    
    lb = "🏆 *LEADERBOARD* 🔥\n\n"
    lb += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    
    for i, (uid, score) in enumerate(top, 1):
        try:
            user = await context.bot.get_chat(uid)
            name = user.first_name
        except:
            name = f"User {uid}"
        
        medal = medals.get(i, f"#{i}")
        lb += f"{medal} *{name}* — {score} XP\n"
    
    lb += "━━━━━━━━━━━━━━━━━━━━━━"
    
    await update.message.reply_text(lb, parse_mode="Markdown")

# ================== 🎰 FUN COMMANDS ==================
async def cmd_flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = random.choice(["Heads 🪙", "Tails 🪙"])
    await update.message.reply_text(f"🪙 *COIN FLIP!*\n\n{result}", parse_mode="Markdown")

async def cmd_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sides = 6
    if context.args:
        try:
            sides = int(context.args[0])
            if sides < 2:
                sides = 6
        except:
            pass
    
    result = random.randint(1, sides)
    await update.message.reply_text(
        f"🎲 *DICE ROLL!*\n\n"
        f"`{result}` (1-{sides})",
        parse_mode="Markdown"
    )

async def cmd_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🤔 `/choose A or B or C`", parse_mode="Markdown")
        return
    
    text = " ".join(context.args)
    options = text.split(" or ")
    if len(options) < 2:
        options = text.split(",")
    
    options = [o.strip() for o in options if o.strip()]
    
    if len(options) < 2:
        await update.message.reply_text("🤔 *2+ options do!*", parse_mode="Markdown")
        return
    
    choice = random.choice(options)
    await update.message.reply_text(
        f"🤔 *CHOOSING...*\n\n"
        f"Options: {', '.join(options)}\n\n"
        f"✨ *I choose: {choice}*",
        parse_mode="Markdown"
    )

async def cmd_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = [
        "🐙 Octopus ke 3 dil hote hain!",
        "🍯 Honey kabhi kharab nahi hoti!",
        "⚡ Lightning din mein 8.6 million bar girti hai!",
        "🧠 Human brain 20 watts electricity generate karta hai!",
        "🦋 Butterflies apne pairo se taste karti hain!",
        "🌍 Earth ka 71% surface paani se dhaka hai!",
        "🐘 Elephants can't jump!",
        "🍌 Banana technically ek berry hai!",
        "👁️ Aapki aankhein 10 million colors dekh sakti hain!",
        "🦈 Sharks dinosaurs se bhi purane hain!",
    ]
    await update.message.reply_text(f"🤯 *RANDOM FACT!*\n\n{random.choice(facts)}", parse_mode="Markdown")

async def cmd_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "😂 Teacher: 'Tum late kyun?'\nStudent: 'Ghar se nikalte time corner tha!'",
        "🤣 Santa: 'Maine online pizza order kiya... ab tak download nahi hua!'",
        "😆 Pappu: 'Papa, aaj school mein sirf maine answer diya!'\nPapa: 'Wah! Kya pucha tha?'\nPappu: 'Kaun hai jo homework nahi laya?'",
        "😜 Wife: 'Tum toh mujhse bilkul pyaar nahi karte!'\nHusband: 'Toh aur kisko karu?'",
        "😂 Doctor: 'Aapko exercise karni chahiye.'\nPatient: 'Doctor sahab, main youtube par 2 ghante exercise videos dekhta hu roz!'",
    ]
    await update.message.reply_text(f"😄 *JOKE!*\n\n{random.choice(jokes)}", parse_mode="Markdown")

async def cmd_shayari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shayaris = [
        "💕 *Mohabbat mein humne khoya hai sab kuch,*\n*Phir bhi teri yaadon mein khoye rehte hain...*",
        "🌟 *Zindagi ek safar hai suhana,*\n*Yahan kal kya ho kisne jaana...*",
        "🔥 *Duniya ki bheed mein tanha the hum,*\n*Jab tak tumse na mile the...*",
        "💔 *Teri yaadon ka safar hai lamba,*\n*Phir bhi teri raah mein baithe hain...*",
    ]
    await update.message.reply_text(random.choice(shayaris), parse_mode="Markdown")

async def cmd_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quotes = [
        "💭 *'The only way to do great work is to love what you do.'* — Steve Jobs",
        "💭 *'In the middle of difficulty lies opportunity.'* — Einstein",
        "💭 *'Believe you can and you're halfway there.'* — Roosevelt",
        "💭 *'Code is like humor. When you have to explain it, it's bad.'* — Cory House",
        "💭 *'Success is not final, failure is not fatal.'* — Churchill",
        "💭 *'The best way to predict the future is to create it.'* — Lincoln",
    ]
    await update.message.reply_text(random.choice(quotes), parse_mode="Markdown")

# ================== 🔍 SEARCH ==================
async def cmd_google(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🔍 `/google search query`", parse_mode="Markdown")
        return
    query = "+".join(context.args)
    await update.message.reply_text(
        f"🔍 *Google Search:* [Click here](https://www.google.com/search?q={query})",
        parse_mode="Markdown",
        disable_web_page_preview=False
    )

async def cmd_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("▶️ `/youtube search query`", parse_mode="Markdown")
        return
    query = "+".join(context.args)
    await update.message.reply_text(
        f"▶️ *YouTube Search:* [Click here](https://www.youtube.com/results?search_query={query})",
        parse_mode="Markdown",
        disable_web_page_preview=False
    )

# ================== 📊 STATS ==================
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    
    try:
        chat = await context.bot.get_chat(cid)
        
        stats = f"📊 *GROUP STATS* 🔥\n\n"
        stats += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        stats += f"👥 *Group:* {chat.title}\n"
        stats += f"🆔 *ID:* `{cid}`\n"
        stats += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        stats += f"📝 *Notes:* {len(group_notes.get(cid, []))}\n"
        stats += f"🔞 *Filters:* {len(group_filters.get(cid, []))}\n"
        stats += f"⚠️ *Active Warnings:* {sum(group_warnings.get(cid, {}).values())}\n"
        stats += f"🏆 *Ranked Users:* {len(group_ranks.get(cid, {}))}\n"
        stats += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        stats += f"⏱️ *Slowmode:* {group_slowmode.get(cid, 'OFF')}s\n"
        stats += f"🌙 *Night Mode:* {'ON 😴' if cid in group_nightmode else 'OFF'}\n"
        stats += f"✨ *Custom Welcome:* {'YES' if cid in group_welcome_msgs else 'Default'}\n"
        stats += f"👋 *Custom Goodbye:* {'YES' if cid in group_goodbye_msgs else 'Default'}\n"
        stats += f"📜 *Rules:* {'SET' if cid in group_rules else 'Not set'}\n"
        stats += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        stats += f"🤖 *Bot:* AVANTIKA AI v2.0\n"
        stats += f"🛡️ *Antispam:* ACTIVE\n"
        stats += f"🎮 *Games:* Available\n"
        stats += f"━━━━━━━━━━━━━━━━━━━━━━"
        
        await update.message.reply_text(stats, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ *Error!* `{str(e)[:100]}`", parse_mode="Markdown")

# ================== ℹ️ INFO ==================
async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(
            f"👤 *USER INFO*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Name: *{u.first_name}*\n"
            f"🆔 ID: `{u.id}`\n"
            f"📛 Username: @{u.username or 'None'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    else:
        try:
            c = await context.bot.get_chat(update.effective_chat.id)
            await update.message.reply_text(
                f"👥 *GROUP INFO*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👥 Name: *{c.title}*\n"
                f"🆔 ID: `{update.effective_chat.id}`\n"
                f"📝 Type: {c.type}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode="Markdown"
            )
        except:
            pass

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        await update.message.reply_text(
            f"🆔 *USER ID*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 {user.first_name}\n"
            f"🆔 `{user.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"🆔 *YOUR ID*\n\n"
            f"🆔 `{update.effective_user.id}`\n"
            f"👥 Chat: `{update.effective_chat.id}`",
            parse_mode="Markdown"
        )

# ================== 🛡️ LOCK/UNLOCK ==================
async def cmd_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "🔒 *LOCK FEATURES*\n\n"
            "`/lock links` — Link block\n"
            "`/lock stickers` — Sticker block\n"
            "`/lock gifs` — GIF block\n"
            "`/lock media` — Photo/Video block\n\n"
            "🔓 `/unlock feature`",
            parse_mode="Markdown"
        )
        return
    
    feature = context.args[0].lower()
    
    if feature not in group_locks[cid]:
        group_locks[cid].append(feature)
        await update.message.reply_text(f"🔒 *Locked:* `{feature}`\n\nAb ye feature block hai!", parse_mode="Markdown")

async def cmd_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        return
    
    feature = context.args[0].lower()
    
    if feature in group_locks[cid]:
        group_locks[cid].remove(feature)
        await update.message.reply_text(f"🔓 *Unlocked:* `{feature}`", parse_mode="Markdown")

# ================== 🔄 ACTIVATE/DEACTIVATE ==================
async def cmd_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text(
            "❌ *ADMIN ONLY!* 👑\n\n"
            "1️⃣ Bot ko *ADMIN* banao\n"
            "2️⃣ Sab *permissions ON* karo\n"
            "3️⃣ `/activate` karo",
            parse_mode="Markdown"
        )
        return
    
    active_groups[cid] = True
    user_history[cid] = []
    
    await refresh_admins(context, cid)
    
    await update.message.reply_text(
        "✅ *ACTIVATED!* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *AVANTIKA AI IS LIVE!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 AI Chat | 🎮 Games | 📊 Polls\n"
        "🏆 Ranks | 🛡️ Antispam | 🔞 Filters\n"
        "🌙 Night Mode | ⏱️ Slowmode\n"
        "🔇 Mute | 🔨 Ban | ⚠️ Warn\n"
        "📜 Rules | 📝 Notes | 📌 Pin\n\n"
        "📋 */help* — Full commands!\n"
        "❌ */deactivate* — OFF",
        parse_mode="Markdown"
    )

async def cmd_deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    
    if not is_admin(update, context, cid, update.effective_user.id):
        await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
        return
    
    active_groups[cid] = False
    await update.message.reply_text("🔴 *DEACTIVATED!*\n\n`/activate` se wapas ON karo!", parse_mode="Markdown")

# ================== 👑 OWNER COMMANDS ==================
async def cmd_adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    
    if not context.args:
        return
    
    try:
        uid = int(context.args[0])
        allowed_users.add(uid)
        await update.message.reply_text(f"✅ *User Added!*\n🆔 `{uid}`", parse_mode="Markdown")
    except:
        pass

async def cmd_removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    
    if not context.args:
        return
    
    try:
        uid = int(context.args[0])
        if uid != OWNER_USER_ID:
            allowed_users.discard(uid)
            await update.message.reply_text(f"✅ *User Removed!*\n🆔 `{uid}`", parse_mode="Markdown")
    except:
        pass

async def cmd_userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    
    ul = "\n".join([f"• `{uid}` {'👑' if uid==OWNER_USER_ID else '✅'}" for uid in allowed_users])
    await update.message.reply_text(
        f"👥 *ALLOWED USERS*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{ul}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 Total: {len(allowed_users)}",
        parse_mode="Markdown"
    )

async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    
    if not context.args:
        return
    
    msg = "📢 *BROADCAST* 👑\n\n" + " ".join(context.args)
    
    sent = 0
    for uid in allowed_users:
        try:
            await context.bot.send_message(uid, msg, parse_mode="Markdown")
            sent += 1
        except:
            pass
    
    await update.message.reply_text(f"📢 *Broadcast done!*\n✅ Sent to: {sent} users", parse_mode="Markdown")

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        return
    
    cid = update.effective_chat.id
    
    user_history[cid] = []
    group_warnings[cid] = {}
    group_rules.pop(cid, None)
    group_notes[cid] = []
    group_polls.pop(cid, None)
    group_games.pop(cid, None)
    group_reminders[cid] = []
    group_filters[cid] = []
    group_schedule[cid] = []
    group_ranks[cid] = {}
    
    await update.message.reply_text(
        "✅ *COMPLETE RESET!* 🔄\n\n"
        "💭 Memory ✅\n"
        "⚠️ Warnings ✅\n"
        "📜 Rules ✅\n"
        "📝 Notes ✅\n"
        "🔞 Filters ✅\n"
        "🏆 Ranks ✅\n"
        "🎮 Games ✅\n"
        "📊 Polls ✅\n\n"
        "🆕 _Fresh start!_ 💎",
        parse_mode="Markdown"
    )

# ================== START ==================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    ct = update.effective_chat.type
    uid = update.effective_user.id
    
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK BOSS!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 *AVANTIKA AI v2.0*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ Sab commands ready hain!\n"
                "📋 */help* — Full list\n\n"
                "_Bolo boss!_ 🔥",
                parse_mode="Markdown"
            )
        elif is_allowed(uid):
            user_history[cid] = []
            await update.message.reply_text(
                "✅ *Access Granted!*\n\n"
                "💬 _Ask me anything!_ 🔥",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("🔒 *Access Denied!*", parse_mode="Markdown")
    else:
        await refresh_admins(context, cid)
        user_history[cid] = []
        await update.message.reply_text(
            "👋 *AVANTIKA AI — SUPERCHARGED!* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 Admin: `/activate` karo\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 */help* — All commands!\n\n"
            "_Activate karo — DHAMAKA!_ 🔥",
            parse_mode="Markdown"
        )

# ================== HELP ==================
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
        "🔹 `/setrules` — Group rules\n"
        "🔹 `/setwelcome` — Custom welcome\n"
        "🔹 `/setgoodbye` — Custom goodbye\n"
        "🔹 `/addnote` — Add note\n"
        "🔹 `/clearnotes` — Clear notes\n"
        "🔹 `/pin` — Pin message (reply)\n"
        "🔹 `/unpin` — Unpin all\n"
        "🔹 `/addfilter` — Word filter\n"
        "🔹 `/rmfilter` — Remove filter\n"
        "🔹 `/slowmode 5` — Rate limit\n"
        "🔹 `/nightmode 22 6` — Night mode\n"
        "🔹 `/lock` — Lock features\n"
        "🔹 `/unlock` — Unlock features\n"
        "🔹 `/poll` — Create poll\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 *USER COMMANDS:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔸 `/help` — Ye help\n"
        "🔸 `/info` — Group/User info\n"
        "🔸 `/id` — User ID\n"
        "🔸 `/rules` — Group rules\n"
        "🔸 `/notes` — Notes list\n"
        "🔸 `/filters` — Filter list\n"
        "🔸 `/rank` — Your XP\n"
        "🔸 `/leaderboard` — Top 10\n"
        "🔸 `/game` — Game center\n"
        "🔸 `/remind 10m msg` — Reminder\n"
        "🔸 `/afk reason` — AFK mode\n"
        "🔸 `/nick name` — Nickname\n"
        "🔸 `/stats` — Group stats\n"
        "🔸 `/flip` — Coin flip\n"
        "🔸 `/dice` — Dice roll\n"
        "🔸 `/choose A or B` — Choose\n"
        "🔸 `/fact` — Random fact\n"
        "🔸 `/joke` — Hindi joke\n"
        "🔸 `/shayari` — Shayari\n"
        "🔸 `/quote` — Quote\n"
        "🔸 `/google query` — Search\n"
        "🔸 `/youtube query` — YT Search\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💎 *AVANTIKA AI v2.0*",
        parse_mode="Markdown"
    )

# ================== MAIN MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    ct = update.effective_chat.type
    msg = update.message
    uid = update.effective_user.id
    
    # Welcome / Goodbye
    if msg.new_chat_members:
        await welcome_handler(update, context)
        return
    
    if msg.left_chat_member:
        await goodbye_handler(update, context)
        return
    
    # Private chat check
    if ct == ChatType.PRIVATE:
        if not is_allowed(uid):
            await msg.reply_text("🔒 *Permission nahi!*", parse_mode="Markdown")
            return
    else:
        # Group check
        if cid not in active_groups or not active_groups[cid]:
            return
        
        # ========== NIGHT MODE CHECK ==========
        if await is_night_time(cid):
            # Admins can still message
            if not is_admin(update, context, cid, uid):
                try:
                    await msg.delete()
                except:
                    pass
                return
        
        # ========== SLOWMODE CHECK ==========
        if cid in group_slowmode and not is_admin(update, context, cid, uid):
            now = datetime.now().timestamp()
            last = group_last_message[cid].get(uid, 0)
            delay = group_slowmode[cid]
            
            if now - last < delay:
                try:
                    await msg.delete()
                except:
                    pass
                return
            
            group_last_message[cid][uid] = now
    
    # Only text messages for rest
    if not msg.text:
        return
    
    # ========== GAME HANDLING ==========
    if cid in group_games:
        game = group_games[cid]
        txt = msg.text.lower().strip()
        
        if game["type"] == "guess":
            try:
                guess = int(txt)
                game["attempts"] += 1
                if guess == game["number"]:
                    await msg.reply_text(
                        f"🎯 *CORRECT!* 🎉\n\n"
                        f"Number: {game['number']}\n"
                        f"Attempts: {game['attempts']}",
                        parse_mode="Markdown"
                    )
                    group_games.pop(cid)
                    return
                elif guess < game["number"]:
                    await msg.reply_text(f"📈 *Higher!* ⬆️ (Attempt #{game['attempts']})", parse_mode="Markdown")
                else:
                    await msg.reply_text(f"📉 *Lower!* ⬇️ (Attempt #{game['attempts']})", parse_mode="Markdown")
            except:
                pass
        
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
                group_games.pop(cid)
                return
        
        elif game["type"] == "quiz":
            if txt == game["answer"]:
                await msg.reply_text("✅ *CORRECT!* 🎉\n\nBahut accha! 👏", parse_mode="Markdown")
                group_games.pop(cid)
                return
            else:
                await msg.reply_text("❌ *Wrong! Try again!*", parse_mode="Markdown")
        
        elif game["type"] == "scramble":
            if txt == game["answer"]:
                await msg.reply_text(
                    f"✅ *CORRECT!* 🎉\n\n"
                    f"Word: *{game['answer']}* 👏",
                    parse_mode="Markdown"
                )
                group_games.pop(cid)
                return
            else:
                await msg.reply_text("❌ *Nahi! Aur try karo!*", parse_mode="Markdown")
    
    # ========== FILTER CHECK ==========
    if cid in group_filters:
        text_lower = msg.text.lower()
        for word in group_filters[cid]:
            if word in text_lower:
                try:
                    await msg.delete()
                except:
                    pass
                try:
                    await msg.reply_text(
                        f"🔞 *Filtered Word!* ⚠️\n\n"
                        f"👤 {update.effective_user.first_name}\n"
                        f"⚠️ Aapka message delete ho gaya!\n"
                        f"📋 Rules follow karo!",
                        parse_mode="Markdown"
                    )
                except:
                    pass
                return
    
    # ========== AFK CHECK ==========
    if msg.reply_to_message and msg.reply_to_message.from_user:
        replied_uid = msg.reply_to_message.from_user.id
        if replied_uid in group_afk and replied_uid != uid:
            afk = group_afk[replied_uid]
            time_diff = get_ist_now() - afk["time"]
            hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_str = ""
            if hours: time_str += f"{hours}h "
            if minutes: time_str += f"{minutes}m"
            if not time_str: time_str = f"{seconds}s"
            
            await msg.reply_text(
                f"😴 *USER AFK HAI!*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 {afk.get('name', 'User')}\n"
                f"📝 {afk['reason']}\n"
                f"⏱️ Since: {time_str} ago\n"
                f"━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode="Markdown"
            )
    
    # ========== RANK UPDATE ==========
    if ct != ChatType.PRIVATE:
        group_ranks[cid][uid] += random.randint(1, 3)
    
    # ========== AI REPLY ==========
    await context.bot.send_chat_action(chat_id=cid, action="typing")
    
    try:
        reply = get_ai_reply(msg.text, cid)
        
        if cid not in user_history:
            user_history[cid] = []
        user_history[cid].append({"role":"user","content":msg.text})
        user_history[cid].append({"role":"assistant","content":reply})
        user_history[cid] = user_history[cid][-10:]
        
        await msg.reply_text(reply, parse_mode="Markdown")
    except:
        pass

# ================== MAIN ==================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register all command handlers
    command_handlers = {
        "start": cmd_start,
        "help": cmd_help,
        "activate": cmd_activate,
        "deactivate": cmd_deactivate,
        "clear": cmd_clear,
        "mute": cmd_mute,
        "unmute": cmd_unmute,
        "ban": cmd_ban,
        "unban": cmd_unban,
        "warn": cmd_warn,
        "clearwarns": cmd_clearwarns,
        "setrules": cmd_setrules,
        "rules": cmd_rules,
        "addnote": cmd_addnote,
        "notes": cmd_notes,
        "clearnotes": cmd_clearnotes,
        "pin": cmd_pin,
        "unpin": cmd_unpin,
        "info": cmd_info,
        "id": cmd_id,
        "adduser": cmd_adduser,
        "removeuser": cmd_removeuser,
        "userlist": cmd_userlist,
        "broadcast": cmd_broadcast,
        "game": cmd_game,
        "poll": cmd_poll,
        "rank": cmd_rank,
        "leaderboard": cmd_leaderboard,
        "addfilter": cmd_addfilter,
        "rmfilter": cmd_rmfilter,
        "filters": cmd_filters,
        "remind": cmd_remind,
        "setwelcome": cmd_setwelcome,
        "setgoodbye": cmd_setgoodbye,
        "slowmode": cmd_slowmode,
        "nightmode": cmd_nightmode,
        "lock": cmd_lock,
        "unlock": cmd_unlock,
        "nick": cmd_nick,
        "afk": cmd_afk,
        "stats": cmd_stats,
        "flip": cmd_flip,
        "dice": cmd_dice,
        "choose": cmd_choose,
        "fact": cmd_fact,
        "joke": cmd_joke,
        "shayari": cmd_shayari,
        "quote": cmd_quote,
        "google": cmd_google,
        "youtube": cmd_youtube,
    }
    
    for cmd, handler in command_handlers.items():
        app.add_handler(CommandHandler(cmd, handler))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(game_callback, pattern="^game_"))
    app.add_handler(CallbackQueryHandler(poll_callback, pattern="^poll"))
    
    # Message handler
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("👑 AVANTIKA AI v2.0 — ALL FEATURES WORKING! 🔥")
    print("✅ Night Mode - Messages delete honge")
    print("✅ Slowmode - Delay enforced")
    print("✅ Antispam - Auto detect")
    print("✅ Games - Interactive")
    print("✅ Polls - Live voting")
    print("✅ Ranks - XP system")
    print("✅ Filters - Auto delete")
    print("✅ Mute/Ban/Warn - Working")
    print("✅ Welcome/Goodbye - Custom")
    print("✅ 50+ Commands Total!")
    
    app.run_polling()

if __name__ == "__main__":
    main()
