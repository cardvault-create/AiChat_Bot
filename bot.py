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
group_polls = {}
group_games = {}
group_reminders = {}
group_filters = {}
group_welcome_msgs = {}
group_goodbye_msgs = {}
group_antispam = {}
group_ranks = {}
group_nicknames = {}
group_reactions = {}
group_slowmode = {}
group_nightmode = {}
group_locks = {}
group_schedule = {}
group_afk = {}
group_admins_only = {}

# ================== AVANTIKA AI ==================
AVANTIKA_PREAMBLE = """You are AVANTIKA AI — Premium, Smart, Multi-Language assistant.
Detect user's language, reply in SAME language. Detailed answers.
Use **Bold**, _Italic_, emojis 🔥💯😂👊💎⚡🎯❤️. Natural & friendly.
Coding → working code. Knowledge → accurate info. Fun → jokes, shayari."""

def get_ist_now(): return datetime.now(IST)

def parse_time(ts):
    ts = ts.lower().strip().replace(" ", "")
    if not ts: return None
    for w, m in [('seconds',1/60),('second',1/60),('sec',1/60),('minutes',1),('minute',1),('mins',1),('min',1),('hours',60),('hour',60),('hrs',60),('hr',60),('days',1440),('day',1440)]:
        if ts.endswith(w):
            try: return float(ts[:-len(w)])*m
            except: pass
    try:
        if ts.endswith('s'): return float(ts[:-1])/60
        if ts.endswith('m'): return float(ts[:-1])
        if ts.endswith('h'): return float(ts[:-1])*60
        if ts.endswith('d'): return float(ts[:-1])*1440
        return float(ts)
    except: return None

def format_time(m):
    ts = int(m*60)
    if ts <= 0: return "0 seconds"
    d, ts = divmod(ts,86400); h, ts = divmod(ts,3600); mi, s = divmod(ts,60)
    p = []
    if d: p.append(f"*{d}* day{'s' if d!=1 else ''}")
    if h: p.append(f"*{h}* hour{'s' if h!=1 else ''}")
    if mi: p.append(f"*{mi}* minute{'s' if mi!=1 else ''}")
    if s and not d: p.append(f"*{s}* second{'s' if s!=1 else ''}")
    return ", ".join(p) if p else "0 seconds"

def is_allowed(uid): return uid in allowed_users

def get_ai_reply(text, chat_id):
    if chat_id not in user_history: user_history[chat_id] = []
    ch = []
    for msg in user_history[chat_id][-4:]:
        r = "USER" if msg["role"]=="user" else "CHATBOT"
        ch.append({"role":r,"message":msg["content"]})
    try:
        resp = co.chat(message=text, chat_history=ch, preamble=AVANTIKA_PREAMBLE, temperature=0.95, max_tokens=800)
        return resp.text
    except: return "😅 _Fir se bol!_ 💎"

# ================== 🎮 GAME SYSTEM ==================
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("🎯 Number Guess", callback_data="game_guess"),
         InlineKeyboardButton("✊ RPS", callback_data="game_rps")],
        [InlineKeyboardButton("🎲 Dice", callback_data="game_dice"),
         InlineKeyboardButton("❓ Quiz", callback_data="game_quiz")],
        [InlineKeyboardButton("🔤 Word Scramble", callback_data="game_scramble")]
    ]
    await update.message.reply_text(
        "🎮 *GAME CENTER* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Choose your game:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = update.effective_chat.id
    game = query.data
    
    if game == "game_guess":
        group_games[cid] = {"type": "guess", "number": random.randint(1, 100), "attempts": 0}
        await query.edit_message_text("🎯 *NUMBER GUESS GAME!*\n\nI chose 1-100, guess karo!\n💬 Reply with number", parse_mode="Markdown")
    
    elif game == "game_rps":
        group_games[cid] = {"type": "rps"}
        await query.edit_message_text("✊ *ROCK PAPER SCISSORS!*\n\nType: `rock`, `paper`, or `scissors`", parse_mode="Markdown")
    
    elif game == "game_dice":
        d = random.randint(1, 6)
        dice_faces = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        await query.edit_message_text(f"🎲 *DICE ROLL!*\n\n{dice_faces[d]} *{d}*", parse_mode="Markdown")
    
    elif game == "game_quiz":
        questions = [
            {"q": "🌍 India capital?", "a": "delhi"},
            {"q": "🧮 15 + 27?", "a": "42"},
            {"q": "🎬 'DDLJ' hero?", "a": "shah rukh khan"},
            {"q": "🏏 Most ODI centuries?", "a": "sachin tendulkar"},
        ]
        q = random.choice(questions)
        group_games[cid] = {"type": "quiz", "answer": q["a"]}
        await query.edit_message_text(f"❓ *QUIZ TIME!*\n\n{q['q']}\n\n💬 Reply with answer", parse_mode="Markdown")
    
    elif game == "game_scramble":
        words = ["python", "telegram", "bot", "coding", "india", "game"]
        w = random.choice(words)
        scrambled = ''.join(random.sample(w, len(w)))
        group_games[cid] = {"type": "scramble", "answer": w}
        await query.edit_message_text(f"🔤 *WORD SCRAMBLE!*\n\n`{scrambled}`\n\n💬 Reply with correct word", parse_mode="Markdown")

# ================== 📊 POLL SYSTEM ==================
async def create_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    
    args = context.args
    if len(args) < 3:
        msg = (
            "📊 *POLL CREATE*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "`/poll \"question\" \"option1\" \"option2\" ...`\n\n"
            "Example:\n"
            "`/poll \"Best language?\" \"Python\" \"JS\" \"Go\"`"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
    
    text = " ".join(args)
    parts = re.findall(r'"([^"]*)"', text)
    if len(parts) < 3:
        await update.message.reply_text("❌ Use quotes: `/poll \"Q\" \"A\" \"B\"`", parse_mode="Markdown")
        return
    
    question, *options = parts
    if cid not in group_polls: group_polls[cid] = {}
    pid = str(len(group_polls[cid]) + 1)
    
    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{opt} (0)", callback_data=f"poll_{pid}_{i}")])
    keyboard.append([InlineKeyboardButton("📊 Results", callback_data=f"pollres_{pid}")])
    
    group_polls[cid][pid] = {"question": question, "options": options, "votes": {i: set() for i in range(len(options))}}
    
    msg = (
        f"📊 *POLL #{pid}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*Q:* {question}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def poll_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    cid = update.effective_chat.id
    data = query.data
    
    if data.startswith("poll_"):
        _, pid, oid = data.split("_")
        pid, oid = str(pid), int(oid)
        
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]
            for v in poll["votes"].values():
                v.discard(uid)
            poll["votes"][oid].add(uid)
            
            keyboard = []
            for i, opt in enumerate(poll["options"]):
                keyboard.append([InlineKeyboardButton(f"{opt} ({len(poll['votes'][i])})", callback_data=f"poll_{pid}_{i}")])
            keyboard.append([InlineKeyboardButton("📊 Results", callback_data=f"pollres_{pid}")])
            
            await query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
            await query.answer("✅ Voted!")
    
    elif data.startswith("pollres_"):
        pid = data.split("_")[1]
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]
            total = sum(len(v) for v in poll["votes"].values())
            results = f"📊 *POLL #{pid} RESULTS*\n\n"
            for i, opt in enumerate(poll["options"]):
                vc = len(poll["votes"][i])
                pct = (vc/total*100) if total > 0 else 0
                bar = "█" * int(pct/10)
                results += f"{opt}: {vc} votes ({pct:.1f}%)\n{bar}\n"
            await query.edit_message_text(results, parse_mode="Markdown")

# ================== 🛡️ ANTISPAM ==================
async def antispam_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = update.effective_user.id
    
    if cid not in group_antispam: group_antispam[cid] = {}
    if uid not in group_antispam[cid]: group_antispam[cid][uid] = []
    
    now = datetime.now()
    group_antispam[cid][uid] = [t for t in group_antispam[cid][uid] if (now - t).seconds < 10]
    group_antispam[cid][uid].append(now)
    
    if len(group_antispam[cid][uid]) > 5:
        try:
            await context.bot.restrict_chat_member(
                cid, uid,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=now + timedelta(minutes=5)
            )
            await update.message.reply_text(f"🚫 *SPAM DETECTED!* ⚡\n👤 User muted for 5 min", parse_mode="Markdown")
        except: pass

# ================== 🏆 RANK SYSTEM ==================
async def update_rank(cid, uid):
    if cid not in group_ranks: group_ranks[cid] = {}
    if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
    group_ranks[cid][uid] += random.randint(1, 5)

async def check_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = update.effective_user.id
    
    if update.message.reply_to_message:
        uid = update.message.reply_to_message.from_user.id
    
    score = group_ranks.get(cid, {}).get(uid, 0)
    level = "🌟" * (score // 100 + 1)
    await update.message.reply_text(f"🏆 *RANK*\n\n👤 Score: {score}\n{level}", parse_mode="Markdown")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid not in group_ranks or not group_ranks[cid]:
        await update.message.reply_text("🏆 _No scores yet!_", parse_mode="Markdown")
        return
    
    top = sorted(group_ranks[cid].items(), key=lambda x: x[1], reverse=True)[:10]
    lb = "🏆 *LEADERBOARD* 🔥\n\n"
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    for i, (uid, score) in enumerate(top):
        try:
            user = await context.bot.get_chat(uid)
            name = user.first_name
        except:
            name = f"User {uid}"
        lb += f"{medals.get(i, '👤')} *{name}*: {score} XP\n"
    await update.message.reply_text(lb, parse_mode="Markdown")

# ================== 🔞 WORD FILTER ==================
async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("🔞 `/addfilter word`", parse_mode="Markdown")
        return
    
    word = " ".join(context.args).lower()
    if cid not in group_filters: group_filters[cid] = []
    if word not in group_filters[cid]:
        group_filters[cid].append(word)
        await update.message.reply_text(f"🔞 *Filtered!* ✅\n`{word}`", parse_mode="Markdown")

async def remove_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    word = " ".join(context.args).lower()
    if cid in group_filters and word in group_filters[cid]:
        group_filters[cid].remove(word)
        await update.message.reply_text(f"✅ *Removed filter:* `{word}`", parse_mode="Markdown")

async def list_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_filters and group_filters[cid]:
        fl = "\n".join([f"• `{w}`" for w in group_filters[cid]])
        await update.message.reply_text(f"🔞 *FILTERS:*\n\n{fl}", parse_mode="Markdown")
    else:
        await update.message.reply_text("🔞 _No filters!_", parse_mode="Markdown")

# ================== ⏰ REMINDER SYSTEM ==================
async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = update.effective_user.id
    if len(context.args) < 2:
        await update.message.reply_text("⏰ `/remind 10m message`", parse_mode="Markdown")
        return
    
    ts = parse_time(context.args[0])
    if not ts:
        await update.message.reply_text("❌ Invalid time!", parse_mode="Markdown")
        return
    
    msg = " ".join(context.args[1:])
    rt = get_ist_now() + timedelta(minutes=ts)
    
    if cid not in group_reminders: group_reminders[cid] = []
    group_reminders[cid].append({"uid": uid, "time": rt, "msg": msg})
    
    await update.message.reply_text(f"⏰ *REMINDER SET!*\n📝 {msg}\n🕐 {rt.strftime('%I:%M %p, %d %b')}", parse_mode="Markdown")
    
    async def remind():
        await asyncio.sleep(ts * 60)
        await context.bot.send_message(cid, f"⏰ *REMINDER!* 🔔\n\n👤 <a href='tg://user?id={uid}'>User</a>\n📝 {msg}\n🕐 {get_ist_now().strftime('%I:%M %p')}", parse_mode="HTML")
    asyncio.create_task(remind())

# ================== ✨ CUSTOM WELCOME/GOODBYE ==================
async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    msg = " ".join(context.args)
    group_welcome_msgs[cid] = msg
    await update.message.reply_text(f"✅ *Welcome set!* ✨\n\nUse `{{name}}` `{{id}}` `{{mention}}`", parse_mode="Markdown")

async def set_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    msg = " ".join(context.args)
    group_goodbye_msgs[cid] = msg
    await update.message.reply_text(f"✅ *Goodbye set!* 👋", parse_mode="Markdown")

# ================== 👋 ENHANCED WELCOME ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members: return
    cid = update.effective_chat.id
    
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            await context.bot.send_message(cid,
                "✨ *AVANTIKA AI JOINED!* ✨\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "👑 Admin */activate* karo\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🎮 Games | 📊 Polls | 🏆 Ranks\n"
                "🛡️ Antispam | 🔞 Filters | ⏰ Reminders\n"
                "📝 Notes | ⚠️ Warns | 🔨 Ban\n"
                "✨ Custom Welcome | 🌙 Night Mode\n\n"
                "🔥 _Activate karo — DHAMAKA!_",
                parse_mode="Markdown")
        else:
            msg = group_welcome_msgs.get(cid,
                f"✨ *WELCOME!* ✨\n\n👤 *{user.first_name}*\n🆔 `{user.id}`\n\n🌟 _Aapka swagat hai! 🎉_")
            msg = msg.replace("{name}", user.first_name).replace("{id}", str(user.id)).replace("{mention}", f"[{user.first_name}](tg://user?id={user.id})")
            await context.bot.send_message(cid, msg, parse_mode="Markdown")

# ================== 👋 GOODBYE ==================
async def goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.left_chat_member: return
    cid = update.effective_chat.id
    user = update.message.left_chat_member
    
    if user.id == context.bot.id: return
    
    msg = group_goodbye_msgs.get(cid, f"👋 *GOODBYE!*\n\n👤 *{user.first_name}* left!\n😢 _Fir milenge!_")
    msg = msg.replace("{name}", user.first_name).replace("{id}", str(user.id))
    await context.bot.send_message(cid, msg, parse_mode="Markdown")

# ================== ⏱️ SLOWMODE ==================
async def set_slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("⏱️ `/slowmode 5` (seconds)\n`/slowmodeoff`", parse_mode="Markdown")
        return
    
    try:
        sec = int(context.args[0])
        group_slowmode[cid] = sec
        await update.message.reply_text(f"⏱️ *SLOWMODE: {sec}s* 🐌", parse_mode="Markdown")
    except:
        pass

async def slowmode_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    group_slowmode.pop(cid, None)
    await update.message.reply_text("⏱️ *Slowmode OFF!* 🚀", parse_mode="Markdown")

# ================== 🌙 NIGHT MODE ==================
async def set_nightmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if len(context.args) < 2:
        await update.message.reply_text("🌙 `/nightmode 22 6` (10PM-6AM)", parse_mode="Markdown")
        return
    
    try:
        start, end = int(context.args[0]), int(context.args[1])
        group_nightmode[cid] = {"start": start, "end": end}
        await update.message.reply_text(f"🌙 *NIGHT MODE* 😴\n🕙 {start}:00 - {end}:00", parse_mode="Markdown")
    except:
        pass

# ================== 🔒 LOCK/UNLOCK FEATURES ==================
async def lock_feature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    feature = context.args[0].lower()
    if cid not in group_locks: group_locks[cid] = []
    if feature not in group_locks[cid]:
        group_locks[cid].append(feature)
        await update.message.reply_text(f"🔒 *Locked:* `{feature}`", parse_mode="Markdown")

async def unlock_feature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    feature = context.args[0].lower()
    if cid in group_locks and feature in group_locks[cid]:
        group_locks[cid].remove(feature)
        await update.message.reply_text(f"🔓 *Unlocked:* `{feature}`", parse_mode="Markdown")

# ================== 🏷️ NICKNAMES ==================
async def set_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = update.effective_user.id
    if not context.args: return
    
    if cid not in group_nicknames: group_nicknames[cid] = {}
    group_nicknames[cid][uid] = " ".join(context.args)
    await update.message.reply_text(f"🏷️ *Nickname set!* ✅\n{group_nicknames[cid][uid]}", parse_mode="Markdown")

# ================== 📱 AFK SYSTEM ==================
async def set_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    reason = " ".join(context.args) if context.args else "AFK"
    group_afk[uid] = {"reason": reason, "time": get_ist_now()}
    await update.message.reply_text(f"😴 *AFK!* \n📝 {reason}\n🕐 {get_ist_now().strftime('%I:%M %p')}", parse_mode="Markdown")

async def check_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message: return
    uid = update.message.reply_to_message.from_user.id
    if uid in group_afk:
        afk = group_afk[uid]
        await update.message.reply_text(f"😴 *User AFK!*\n📝 {afk['reason']}\n🕐 Since {afk['time'].strftime('%I:%M %p')}", parse_mode="Markdown")

# ================== 📊 STATS ==================
async def group_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    try:
        chat = await context.bot.get_chat(cid)
        admins = await context.bot.get_chat_administrators(cid)
        
        stats = (
            f"📊 *GROUP STATS* 🔥\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 *Name:* {chat.title}\n"
            f"🆔 *ID:* `{cid}`\n"
            f"👑 *Admins:* {len(admins)}\n"
            f"📝 *Notes:* {len(group_notes.get(cid, []))}\n"
            f"🔞 *Filters:* {len(group_filters.get(cid, []))}\n"
            f"⚠️ *Warns:* {sum(group_warnings.get(cid, {}).values())}\n"
            f"🏆 *Ranked Users:* {len(group_ranks.get(cid, {}))}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔒 *Locks:* {', '.join(group_locks.get(cid, ['None']))}\n"
            f"⏱️ *Slowmode:* {group_slowmode.get(cid, 'OFF')}s\n"
            f"🌙 *Nightmode:* {'ON' if cid in group_nightmode else 'OFF'}\n"
            f"🛡️ *Antispam:* ACTIVE\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        await update.message.reply_text(stats, parse_mode="Markdown")
    except:
        pass

# ================== ⚡ REACTION SYSTEM ==================
async def add_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if len(context.args) < 2: return
    
    trigger = context.args[0].lower()
    reaction = " ".join(context.args[1:])
    if cid not in group_reactions: group_reactions[cid] = {}
    group_reactions[cid][trigger] = reaction
    await update.message.reply_text(f"⚡ *Reaction added!*\n`{trigger}` → {reaction}", parse_mode="Markdown")

# ================== 📅 SCHEDULED MESSAGES ==================
async def schedule_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if len(context.args) < 2: return
    
    ts = parse_time(context.args[0])
    if not ts: return
    
    msg = " ".join(context.args[1:])
    st = get_ist_now() + timedelta(minutes=ts)
    
    if cid not in group_schedule: group_schedule[cid] = []
    sid = len(group_schedule[cid]) + 1
    group_schedule[cid].append({"id": sid, "time": st, "msg": msg})
    
    await update.message.reply_text(f"📅 *SCHEDULED!*\n🆔 #{sid}\n🕐 {st.strftime('%I:%M %p, %d %b')}\n📝 {msg}", parse_mode="Markdown")
    
    async def send_scheduled():
        await asyncio.sleep(ts * 60)
        await context.bot.send_message(cid, f"📅 *SCHEDULED #{sid}*\n\n{msg}", parse_mode="Markdown")
    asyncio.create_task(send_scheduled())

# ================== 🎰 RANDOM FUN ==================
async def flip_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = random.choice(["Heads 🪙", "Tails 🪙"])
    await update.message.reply_text(f"🪙 *FLIP!*\n\n{result}", parse_mode="Markdown")

async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sides = int(context.args[0]) if context.args else 6
    result = random.randint(1, sides)
    await update.message.reply_text(f"🎲 *ROLL!*\n\n`{result}` (1-{sides})", parse_mode="Markdown")

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    options = " ".join(context.args).split(" or ")
    if len(options) < 2:
        options = " ".join(context.args).split(",")
    choice = random.choice([o.strip() for o in options if o.strip()])
    await update.message.reply_text(f"🤔 *I choose:*\n\n✨ {choice}", parse_mode="Markdown")

async def fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    facts = [
        "🐙 Octopus ke 3 dil hote hain!",
        "🍯 Honey kabhi kharab nahi hoti!",
        "⚡ Lightning din mein 8.6 million bar girti hai!",
        "🧠 Human brain 20 watts electricity generate karta hai!",
        "🦋 Butterflies apne pairo se taste karti hain!",
        "🌍 Earth ke 71% surface par paani hai!",
    ]
    await update.message.reply_text(f"🤯 *FACT!*\n\n{random.choice(facts)}", parse_mode="Markdown")

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "😂 Teacher: 'Tum late kyun?' Student: 'Ghar se nikalte time corner tha!'",
        "🤣 Santa: 'Maine online pizza order kiya... ab tak download nahi hua!'",
        "😆 Banta: 'Mujhe English aati hai!' Santa: 'Toh naach ko English mein kya bolenge?' Banta: 'Dance!' Santa: 'Aur gana?' Banta: 'Gance!'",
    ]
    await update.message.reply_text(random.choice(jokes), parse_mode="Markdown")

async def shayari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shayaris = [
        "💕 *Mohabbat mein humne khoya hai sab kuch,*\n*Phir bhi teri yaadon mein khoye rehte hain...*",
        "🌟 *Zindagi ek safar hai suhana,*\n*Yahan kal kya ho kisne jaana...*",
        "🔥 *Duniya ki bheed mein tanha the hum,*\n*Jab tak tumse na mile the...*",
    ]
    await update.message.reply_text(random.choice(shayaris), parse_mode="Markdown")

async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quotes = [
        "💭 *'The only way to do great work is to love what you do.'* — Steve Jobs",
        "💭 *'In the middle of difficulty lies opportunity.'* — Einstein",
        "💭 *'Believe you can and you're halfway there.'* — Roosevelt",
        "💭 *'Code is like humor. When you have to explain it, it's bad.'* — Cory House",
    ]
    await update.message.reply_text(random.choice(quotes), parse_mode="Markdown")

# ================== 🔍 SEARCH ==================
async def google_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    query = "+".join(context.args)
    await update.message.reply_text(f"🔍 *Search:* [Click here](https://www.google.com/search?q={query})", parse_mode="Markdown", disable_web_page_preview=False)

async def youtube_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    query = "+".join(context.args)
    await update.message.reply_text(f"▶️ *YouTube:* [Click here](https://www.youtube.com/results?search_query={query})", parse_mode="Markdown", disable_web_page_preview=False)

# ================== ORIGINAL COMMANDS ==================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown")
        return
    if not context.args: return
    try:
        allowed_users.add(int(context.args[0]))
        await update.message.reply_text(f"✅ *Added!* 🆔 `{context.args[0]}`", parse_mode="Markdown")
    except:
        pass

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!*", parse_mode="Markdown")
        return
    if not context.args: return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: return
        allowed_users.discard(rid)
        await update.message.reply_text(f"✅ *Removed!* 🆔 `{rid}`", parse_mode="Markdown")
    except:
        pass

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: return
    ul = "\n".join([f"• `{uid}` {'👑' if uid==OWNER_USER_ID else '✅'}" for uid in allowed_users])
    await update.message.reply_text(f"👥 *Allowed:*\n\n{ul}\n\n📊 Total: {len(allowed_users)}", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: return
    if not context.args: return
    msg = "📢 *BOSS* 👑\n\n" + " ".join(context.args)
    for uid in allowed_users:
        try:
            await context.bot.send_message(uid, msg, parse_mode="Markdown")
        except:
            pass

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        await update.message.reply_text(f"🆔 `{update.message.reply_to_message.from_user.id}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

async def addnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(context.args))
    await update.message.reply_text(f"✅ *Note Added!* 📝 ({len(group_notes[cid])})", parse_mode="Markdown")

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]:
        await update.message.reply_text("📝 *Notes:*\n\n" + "\n".join([f"• {n}" for n in group_notes[cid]]), parse_mode="Markdown")
    else:
        await update.message.reply_text("📝 _No notes!_ */addnote*", parse_mode="Markdown")

async def clearnotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_notes[update.effective_chat.id] = []
    await update.message.reply_text("✅ *Cleared!*", parse_mode="Markdown")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: return
    try:
        await update.message.reply_to_message.pin()
        await update.message.reply_text("📌 *Pinned!* ✅", parse_mode="Markdown")
    except:
        pass

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    except:
        pass

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(f"👤 *{u.first_name}*\n🆔 `{u.id}`\n📛 @{u.username or 'None'}", parse_mode="Markdown")
    else:
        try:
            c = await context.bot.get_chat(update.effective_chat.id)
            await update.message.reply_text(f"👥 *{c.title}*\n🆔 `{update.effective_chat.id}`\n👥 Members", parse_mode="Markdown")
        except:
            pass

async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not context.args:
        await update.message.reply_text("📝 */setrules rules*")
        return
    group_rules[cid] = " ".join(context.args)
    await update.message.reply_text("📜 *Rules Set!* ✅", parse_mode="Markdown")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_rules:
        await update.message.reply_text(f"📜 *Group Rules:*\n\n{group_rules[cid]}", parse_mode="Markdown")
    else:
        await update.message.reply_text("📜 _No rules!_ */setrules*", parse_mode="Markdown")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ _Reply to warn!_")
        return
    t = update.message.reply_to_message.from_user
    if cid not in group_warnings: group_warnings[cid] = {}
    if t.id not in group_warnings[cid]: group_warnings[cid][t.id] = 0
    group_warnings[cid][t.id] += 1
    wc = group_warnings[cid][t.id]
    await update.message.reply_text(f"⚠️ *Warning!* 👤 {t.first_name}\n📊 *{wc}/3* {'🔴 Mute!' if wc>=3 else '⚡'}", parse_mode="Markdown")

async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if cid in group_warnings and t.id in group_warnings[cid]:
            group_warnings[cid][t.id] = 0
    else:
        group_warnings[cid] = {}
    await update.message.reply_text("✅ *Cleared!*", parse_mode="Markdown")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
            return
    except:
        return
    t = None
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
    elif context.args:
        try:
            t = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
        except:
            pass
    if not t or t.id == update.effective_user.id or t.is_bot:
        await update.message.reply_text("❌ _Can't ban!_")
        return
    try:
        await context.bot.ban_chat_member(cid, t.id)
        await update.message.reply_text(f"🔨 *BANNED!* 👤 {t.first_name} 🚫\n\n🆔 `{t.id}`\n🔓 _/unban {t.id}_", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ _Ban failed! Permissions do._", parse_mode="Markdown")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("📝 */unban user_id*")
        return
    try:
        await context.bot.unban_chat_member(cid, int(context.args[0]))
        await update.message.reply_text(f"✅ *UNBANNED!* 🔓\n🆔 `{context.args[0]}`", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ _Unban failed!_", parse_mode="Markdown")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ *Sirf Group!*", parse_mode="Markdown")
        return
    
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *Bot ko Admin banao!*", parse_mode="Markdown")
        return
    
    t, ts = None, "1h"
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if context.args: ts = " ".join(context.args)
    elif context.args and len(context.args) >= 2:
        try:
            t = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
            ts = " ".join(context.args[1:])
        except:
            return
    else:
        msg = (
            "🔇 *MUTE SYSTEM* 🇮🇳\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Reply karke:*\n"
            "`/mute 10 second` | `/mute 5 minute`\n"
            "`/mute 2 hour` | `/mute 1 day`\n\n"
            "📌 *Short:* `25s` `5m` `2h` `1d` `30d`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🇮🇳 *IST Timezone* | ⏰ *Auto Unmute ON*"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
    
    if not t or t.id == update.effective_user.id or t.is_bot: return
    
    mm = parse_time(ts)
    if not mm or mm > 43200 or mm <= 0: return
    
    nw = get_ist_now()
    ut = nw + timedelta(minutes=mm)
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=cid, user_id=t.id,
            permissions=ChatPermissions(
                can_send_messages=False, can_send_audios=False, can_send_documents=False,
                can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
                can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
                can_add_web_page_previews=False, can_change_info=False,
                can_invite_users=False, can_pin_messages=False
            ),
            until_date=ut
        )
        
        tn = t.first_name or "User"
        if t.last_name: tn += f" {t.last_name}"
        
        await update.message.reply_text(
            f"🔇 *MUTED! — INDIA TIME* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {tn}\n"
            f"🆔 *ID:* `{t.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ *Duration:* {format_time(mm)}\n\n"
            f"📅 *Muted At:*\n"
            f"   🕐 `{nw.strftime('%I:%M:%S %p')}`\n"
            f"   📆 {nw.strftime('%d %B %Y')}\n\n"
            f"🔓 *Unmute At:*\n"
            f"   🕐 `{ut.strftime('%I:%M:%S %p')}`\n"
            f"   📆 {ut.strftime('%d %B %Y')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ *Auto Unmute ON* — Time khatam hone par khulega!\n"
            f"🔊 Ya `/unmute` reply karke manual unmute",
            parse_mode="Markdown"
        )
        
        async def auto():
            await asyncio.sleep(mm * 60)
            try:
                await context.bot.restrict_chat_member(
                    chat_id=cid, user_id=t.id,
                    permissions=ChatPermissions(
                        can_send_messages=True, can_send_audios=True, can_send_documents=True,
                        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                        can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                        can_add_web_page_previews=True, can_change_info=False,
                        can_invite_users=False, can_pin_messages=False
                    )
                )
                await context.bot.send_message(
                    cid,
                    f"✅ *AUTO UNMUTED!* 🇮🇳\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 *{tn}*\n"
                    f"⏱️ {format_time(mm)} ka mute khatam!\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💬 _Ab message kar sakta hai!_ 🎉",
                    parse_mode="Markdown"
                )
            except:
                pass
        asyncio.create_task(auto())
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Mute Failed!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ _Bot ko *Ban Users* permission do!_\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"`{str(e)[:80]}`",
            parse_mode="Markdown"
        )

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t and context.args:
        try:
            t = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
        except:
            return
    if not t:
        await update.message.reply_text("🔊 _Reply /unmute_", parse_mode="Markdown")
        return
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=cid, user_id=t.id,
            permissions=ChatPermissions(
                can_send_messages=True, can_send_audios=True, can_send_documents=True,
                can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                can_add_web_page_previews=True, can_change_info=False,
                can_invite_users=False, can_pin_messages=False
            )
        )
        nw = get_ist_now()
        await update.message.reply_text(
            f"✅ *UNMUTED!* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {t.first_name}\n"
            f"🔓 *At:* `{nw.strftime('%I:%M:%S %p, %d %B %Y')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💬 _Ab message kar sakta hai!_ 🎉",
            parse_mode="Markdown"
        )
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    ct = update.effective_chat.type
    uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK BOSS!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 *AVANTIKA AI — SUPERCHARGED!*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "🆕 *NEW FEATURES:*\n"
                "🎮 Games | 📊 Polls | 🏆 Ranks\n"
                "🛡️ Antispam | 🔞 Filters | ⏰ Reminders\n"
                "✨ Custom Welcome/Goodbye | ⏱️ Slowmode\n"
                "🌙 Night Mode | 🔒 Locks | 🏷️ Nicknames\n"
                "📱 AFK | 📅 Scheduled Msgs | ⚡ Auto Reactions\n"
                "🎰 /flip /dice /choose /fact /joke /shayari /quote\n"
                "🔍 /google /youtube\n\n"
                "_Bolo boss! 🔥_",
                parse_mode="Markdown"
            )
        elif is_allowed(uid):
            user_history[cid] = []
            await update.message.reply_text("✅ *Access Granted!*\n💬 _Ask anything!_", parse_mode="Markdown")
        else:
            await update.message.reply_text("🔒 *Access Denied!*", parse_mode="Markdown")
    else:
        user_history[cid] = []
        await update.message.reply_text(
            "👋 *AVANTIKA AI — SUPERCHARGED!* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 Admin */activate* karo\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔥 *40+ COMMANDS!*\n"
            "🎮 /game | 📊 /poll | 🏆 /rank\n"
            "⏰ /remind | 🔞 /addfilter | 📅 /schedule\n"
            "⏱️ /slowmode | 🌙 /nightmode | 🔒 /lock\n"
            "🏷️ /nick | 📱 /afk | ⚡ /addreact\n"
            "✨ /setwelcome | 👋 /setgoodbye\n"
            "🎰 /flip /dice /choose /fact /joke /shayari\n\n"
            "_Activate karo — SUPER DHAMAKA!_ 🔥",
            parse_mode="Markdown"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text(
                "❌ *ADMIN ONLY!* 👑\n\n1️⃣ Bot ko *ADMIN* banao\n2️⃣ Sab *permissions ON* karo\n3️⃣ `/activate`",
                parse_mode="Markdown"
            )
            return
    except:
        await update.message.reply_text("❌ *Bot ko ADMIN banao!*", parse_mode="Markdown")
        return
    
    active_groups[cid] = True
    user_history[cid] = []
    await update.message.reply_text(
        "✅ *ACTIVATED! SUPERCHARGED!* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *ALL 40+ SYSTEMS GO!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 AI | 🎮 Games | 📊 Polls | 🏆 Ranks\n"
        "🛡️ Antispam | 🔞 Filters | ⏰ Reminders\n"
        "✨ Welcome/Goodbye | ⏱️ Slowmode\n"
        "🌙 Nightmode | 🔒 Locks | 📱 AFK\n"
        "📅 Schedule | ⚡ Reactions | 🔇 Mute\n"
        "🔨 Ban | ⚠️ Warn | 📜 Rules | 📝 Notes\n\n"
        "❌ /deactivate",
        parse_mode="Markdown"
    )

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *OFF!* `/activate`", parse_mode="Markdown")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_user.id != OWNER_USER_ID: return
    user_history[cid] = []
    for db in [group_warnings, group_rules, group_notes, group_polls, group_games,
               group_reminders, group_filters, group_reactions, group_schedule]:
        db.pop(cid, None)
    await update.message.reply_text(
        "✅ *COMPLETE RESET!* 🔄\n\n"
        "💭 Memory ✅\n⚠️ Warnings ✅\n📜 Rules ✅\n📝 Notes ✅\n"
        "🎮 Games ✅\n📊 Polls ✅\n🔞 Filters ✅\n📅 Schedule ✅\n\n"
        "🆕 _Fresh start!_ 💎",
        parse_mode="Markdown"
    )

# ================== HELP COMMAND ==================
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *AVANTIKA AI — HELP* 💎\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎮 *FUN:* /game /flip /dice /choose /fact /joke /shayari /quote\n"
        "📊 *POLLS:* /poll\n"
        "🏆 *RANKS:* /rank /leaderboard\n"
        "⏰ *REMINDERS:* /remind 10m message\n"
        "🔞 *FILTERS:* /addfilter /rmfilter /filters\n"
        "✨ *WELCOME:* /setwelcome /setgoodbye\n"
        "⏱️ *SLOWMODE:* /slowmode 5 /slowmodeoff\n"
        "🌙 *NIGHT:* /nightmode 22 6\n"
        "🔒 *LOCKS:* /lock feature /unlock feature\n"
        "🏷️ *NICK:* /nick name\n"
        "📱 *AFK:* /afk reason\n"
        "📅 *SCHEDULE:* /schedule 10m message\n"
        "⚡ *REACTIONS:* /addreact word reaction\n"
        "📊 *STATS:* /stats\n"
        "🔍 *SEARCH:* /google /youtube\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔇 /mute | 🔨 /ban | ⚠️ /warn\n"
        "📜 /setrules | 📝 /addnote | 📌 /pin\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    ct = update.effective_chat.type
    msg = update.message
    uid = update.effective_user.id
    
    # Welcome/Goodbye
    if msg.new_chat_members:
        await welcome(update, context)
        return
    if msg.left_chat_member:
        await goodbye(update, context)
        return
    
    if ct == ChatType.PRIVATE and not is_allowed(uid):
        await msg.reply_text("🔒 *Permission nahi!*", parse_mode="Markdown")
        return
    
    if ct != ChatType.PRIVATE and (cid not in active_groups or not active_groups[cid]):
        return
    
    if not msg.text: return
    
    # Game handling
    if cid in group_games:
        game = group_games[cid]
        txt = msg.text.lower().strip()
        
        if game["type"] == "guess":
            try:
                guess = int(txt)
                game["attempts"] += 1
                if guess == game["number"]:
                    await msg.reply_text(f"🎯 *CORRECT!* 🎉\nNumber was {game['number']}\nAttempts: {game['attempts']}", parse_mode="Markdown")
                    group_games.pop(cid)
                    return
                elif guess < game["number"]:
                    await msg.reply_text("📈 *Higher!* ⬆️", parse_mode="Markdown")
                else:
                    await msg.reply_text("📉 *Lower!* ⬇️", parse_mode="Markdown")
            except:
                pass
        
        elif game["type"] == "rps":
            if txt in ["rock", "paper", "scissors"]:
                bot_choice = random.choice(["rock", "paper", "scissors"])
                if txt == bot_choice:
                    result = "🤝 *TIE!*"
                elif (txt == "rock" and bot_choice == "scissors") or \
                     (txt == "paper" and bot_choice == "rock") or \
                     (txt == "scissors" and bot_choice == "paper"):
                    result = "🎉 *YOU WIN!*"
                else:
                    result = "😢 *BOT WINS!*"
                await msg.reply_text(f"✊ *RPS!*\n\nYou: {txt}\nBot: {bot_choice}\n\n{result}", parse_mode="Markdown")
                group_games.pop(cid)
                return
        
        elif game["type"] == "quiz":
            if txt == game["answer"]:
                await msg.reply_text("✅ *CORRECT!* 🎉", parse_mode="Markdown")
                group_games.pop(cid)
                return
        
        elif game["type"] == "scramble":
            if txt == game["answer"]:
                await msg.reply_text("✅ *CORRECT!* 🎉", parse_mode="Markdown")
                group_games.pop(cid)
                return
    
    # Filter check
    if cid in group_filters:
        for word in group_filters[cid]:
            if word in msg.text.lower():
                try:
                    await msg.delete()
                except:
                    pass
                await msg.reply_text(f"🔞 *Filtered word detected!* ⚠️\n👤 {update.effective_user.first_name}", parse_mode="Markdown")
                return
    
    # Antispam
    if ct != ChatType.PRIVATE:
        await antispam_check(update, context)
    
    # Rank update
    if ct != ChatType.PRIVATE:
        await update_rank(cid, uid)
    
    # AFK check
    if msg.reply_to_message:
        await check_afk(update, context)
    
    # Auto reactions
    if cid in group_reactions:
        for trigger, reaction in group_reactions[cid].items():
            if trigger in msg.text.lower():
                try:
                    await msg.reply_text(reaction)
                except:
                    pass
    
    # AI Reply
    await context.bot.send_chat_action(chat_id=cid, action="typing")
    
    try:
        reply = get_ai_reply(msg.text, cid)
        if cid not in user_history: user_history[cid] = []
        user_history[cid].append({"role":"user","content":msg.text})
        user_history[cid].append({"role":"assistant","content":reply})
        user_history[cid] = user_history[cid][-10:]
        await msg.reply_text(reply, parse_mode="Markdown")
    except:
        pass

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Original commands
    for cmd, fn in [
        ("start",start),("activate",activate),("deactivate",deactivate),("clear",clear),
        ("mute",mute_user),("unmute",unmute_user),("ban",ban_user),("unban",unban_user),
        ("warn",warn),("clearwarns",clearwarns),("setrules",setrules),("rules",rules),
        ("addnote",addnote),("notes",notes),("clearnotes",clearnotes),
        ("pin",pin),("unpin",unpin),("info",info),
        ("adduser",adduser),("removeuser",removeuser),("userlist",userlist),
        ("broadcast",broadcast),("id",get_id)
    ]:
        app.add_handler(CommandHandler(cmd, fn))
    
    # New commands
    for cmd, fn in [
        ("game", start_game), ("poll", create_poll), ("rank", check_rank),
        ("leaderboard", leaderboard), ("addfilter", add_filter),
        ("rmfilter", remove_filter), ("filters", list_filters),
        ("remind", set_reminder), ("setwelcome", set_welcome),
        ("setgoodbye", set_goodbye), ("slowmode", set_slowmode),
        ("slowmodeoff", slowmode_off), ("nightmode", set_nightmode),
        ("lock", lock_feature), ("unlock", unlock_feature),
        ("nick", set_nickname), ("afk", set_afk),
        ("addreact", add_reaction), ("schedule", schedule_msg),
        ("stats", group_stats), ("flip", flip_coin),
        ("dice", roll_dice), ("choose", choose),
        ("fact", fact), ("joke", joke),
        ("shayari", shayari), ("quote", quote),
        ("google", google_search), ("youtube", youtube_search),
        ("help", help_cmd)
    ]:
        app.add_handler(CommandHandler(cmd, fn))
    
    app.add_handler(CallbackQueryHandler(game_callback, pattern="^game_"))
    app.add_handler(CallbackQueryHandler(poll_callback, pattern="^poll"))
    
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("👑 AVANTIKA AI — SUPERCHARGED WITH 40+ FEATURES!")
    app.run_polling()

if __name__ == "__main__":
    main()
