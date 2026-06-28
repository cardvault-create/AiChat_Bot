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
user_history = {}
active_groups = {}
allowed_users = {7614459746}
group_warnings = {}
group_rules = {}
group_notes = {}

# ================== EXTRA FEATURE DATABASES ==================
group_nightmode = {}
group_slowmode = {}
group_games = {}
group_polls = {}
group_filters = {}
group_welcome_msgs = {}
group_goodbye_msgs = {}
group_ranks = {}
group_afk = {}
last_message_time = {}

# ================== AVANTIKA AI ==================
AVANTIKA_PREAMBLE = """You are AVANTIKA AI — Premium, Smart, Multi-Language assistant.
Detect user's language, reply in SAME language. Detailed answers.
Use **Bold**, _Italic_, emojis 🔥💯😂👊💎⚡🎯❤️. Natural & friendly.
Coding → working code. Knowledge → accurate info. Fun → jokes, shayari."""

def get_ist_now(): return datetime.now(IST)

def parse_time(ts):
    ts = ts.lower().strip().replace(" ", "")
    if not ts: return None
    for w, m in [('seconds',1/60),('second',1/60),('sec',1/60),('s',1/60),('minutes',1),('minute',1),('mins',1),('min',1),('m',1),('hours',60),('hour',60),('hrs',60),('hr',60),('h',60),('days',1440),('day',1440),('d',1440)]:
        if ts.endswith(w):
            try: return float(ts[:-len(w)])*m
            except: pass
    try: return float(ts)
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

async def get_admin_ids(chat_id, context):
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        return {a.user.id for a in admins}
    except: return set()

def is_night_mode_on(chat_id):
    if chat_id not in group_nightmode: return False
    now = get_ist_now()
    h = now.hour
    s = group_nightmode[chat_id]["start"]
    e = group_nightmode[chat_id]["end"]
    if s < e: return s <= h < e
    else: return h >= s or h < e

# ================== OWNER COMMANDS ==================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args: return
    try: allowed_users.add(int(context.args[0])); await update.message.reply_text(f"✅ *Added!* 🆔 `{context.args[0]}`", parse_mode="Markdown")
    except: pass

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!*", parse_mode="Markdown"); return
    if not context.args: return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: return
        allowed_users.discard(rid); await update.message.reply_text(f"✅ *Removed!* 🆔 `{rid}`", parse_mode="Markdown")
    except: pass

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: return
    ul = "\n".join([f"• `{uid}` {'👑' if uid==OWNER_USER_ID else '✅'}" for uid in allowed_users])
    await update.message.reply_text(f"👥 *Allowed:*\n\n{ul}\n\n📊 Total: {len(allowed_users)}", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: return
    if not context.args: return
    msg = "📢 *BOSS* 👑\n\n" + " ".join(context.args)
    for uid in allowed_users:
        try: await context.bot.send_message(uid, msg, parse_mode="Markdown")
        except: pass

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message: await update.message.reply_text(f"🆔 `{update.message.reply_to_message.from_user.id}`", parse_mode="Markdown")
    else: await update.message.reply_text(f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

# ================== NOTES ==================
async def addnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(context.args))
    await update.message.reply_text(f"✅ *Note Added!* 📝 ({len(group_notes[cid])})", parse_mode="Markdown")

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]: await update.message.reply_text("📝 *Notes:*\n\n" + "\n".join([f"• {n}" for n in group_notes[cid]]), parse_mode="Markdown")
    else: await update.message.reply_text("📝 _No notes!_ */addnote*", parse_mode="Markdown")

async def clearnotes(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    group_notes[update.effective_chat.id] = []
    await update.message.reply_text("✅ *Cleared!*", parse_mode="Markdown")

# ================== PIN ==================
async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: return
    try: await update.message.reply_to_message.pin(); await update.message.reply_text("📌 *Pinned!* ✅", parse_mode="Markdown")
    except: pass

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    try: await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    except: pass

# ================== INFO ==================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(f"👤 *{u.first_name}*\n🆔 `{u.id}`\n📛 @{u.username or 'None'}", parse_mode="Markdown")
    else:
        try:
            c = await context.bot.get_chat(update.effective_chat.id)
            await update.message.reply_text(f"👥 *{c.title}*\n🆔 `{update.effective_chat.id}`", parse_mode="Markdown")
        except: pass

# ================== RULES ==================
async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not context.args: await update.message.reply_text("📝 */setrules rules*"); return
    group_rules[cid] = " ".join(context.args)
    await update.message.reply_text(f"📜 *Rules Set!* ✅", parse_mode="Markdown")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_rules: await update.message.reply_text(f"📜 *Group Rules:*\n\n{group_rules[cid]}", parse_mode="Markdown")
    else: await update.message.reply_text("📜 _No rules!_ */setrules*", parse_mode="Markdown")

# ================== WARN ==================
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not update.message.reply_to_message: await update.message.reply_text("⚠️ _Reply to warn!_"); return
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
        if cid in group_warnings and t.id in group_warnings[cid]: group_warnings[cid][t.id] = 0
    else: group_warnings[cid] = {}
    await update.message.reply_text("✅ *Cleared!*", parse_mode="Markdown")

# ================== BAN ==================
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown"); return
    except: return
    t = None
    if update.message.reply_to_message: t = update.message.reply_to_message.from_user
    elif context.args:
        try: t = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
        except: pass
    if not t or t.id == update.effective_user.id or t.is_bot: await update.message.reply_text("❌ _Can't ban!_"); return
    try:
        await context.bot.ban_chat_member(cid, t.id)
        await update.message.reply_text(f"🔨 *BANNED!* 👤 {t.first_name} 🚫\n\n🆔 `{t.id}`\n🔓 _/unban {t.id}_", parse_mode="Markdown")
    except: await update.message.reply_text("❌ _Ban failed! Permissions do._", parse_mode="Markdown")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: await update.message.reply_text("📝 */unban user_id*"); return
    try:
        await context.bot.unban_chat_member(cid, int(context.args[0]))
        await update.message.reply_text(f"✅ *UNBANNED!* 🔓\n🆔 `{context.args[0]}`", parse_mode="Markdown")
    except: await update.message.reply_text("❌ _Unban failed!_", parse_mode="Markdown")

# ================== WELCOME ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            await context.bot.send_message(
                chat_id=cid,
                text="✨ *AVANTIKA AI JOINED!* ✨\n\n"
                     "━━━━━━━━━━━━━━━━━━━━━━\n"
                     "👑 Admin */activate* karo\n"
                     "📢 Phir sabko *PREMIUM REPLY!*\n"
                     "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                     "💻 *Coding* | 📚 *Knowledge* | 😂 *Fun*\n"
                     "🎮 *Games* | 🌙 *Night Mode* | ⏱️ *Slow Mode*\n"
                     "🔇 *Mute* | 🔨 *Ban* | ⚠️ *Warn* | 📌 *Pin*\n\n"
                     "🔥 _Activate karo — dhamaka!_",
                parse_mode="Markdown"
            )
        else:
            wm = group_welcome_msgs.get(cid, 
                f"✨ *WELCOME TO THE GROUP!* ✨\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *{user.first_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌟 _Aapka swagat hai!_ 🎉\n\n"
                f"💎 *Yahaan milega:*\n"
                f"• *Premium AI Replies* 🔥\n"
                f"• *Coding Help* 💻\n"
                f"• *Knowledge* 📚\n"
                f"• *Fun & Masti* 😂\n\n"
                f"📢 _Kuch bhi puchho — jawab milega!_ 💬\n\n"
                f"🔰 _Enjoy karo!_ 🤗")
            wm = wm.replace("{name}", user.first_name).replace("{id}", str(user.id)).replace("{mention}", f"[{user.first_name}](tg://user?id={user.id})")
            await context.bot.send_message(chat_id=cid, text=wm, parse_mode="Markdown")

# ================== MUTE ==================
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ *Sirf Group!*", parse_mode="Markdown"); return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown"); return
    except: await update.message.reply_text("❌ *Bot ko Admin banao!*", parse_mode="Markdown"); return
    
    t, ts = None, "1h"
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if context.args: ts = " ".join(context.args)
    elif context.args and len(context.args) >= 2:
        try:
            t = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
            ts = " ".join(context.args[1:])
        except: return
    else:
        await update.message.reply_text(
            "🔇 *MUTE SYSTEM* 🇮🇳\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Reply karke:*\n"
            "`/mute 10s` `/mute 5m` `/mute 2h` `/mute 1d`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🇮🇳 *IST Timezone* | ⏰ *Auto Unmute ON*",
            parse_mode="Markdown"
        ); return
    
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
            f"📅 *Muted At:* `{nw.strftime('%I:%M:%S %p')}`\n"
            f"🔓 *Unmute At:* `{ut.strftime('%I:%M:%S %p, %d %B %Y')}`\n\n"
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
            except: pass
        asyncio.create_task(auto())
        
    except Exception as e:
        await update.message.reply_text(f"❌ *Mute Failed!*\n\n`{str(e)[:80]}`", parse_mode="Markdown")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t and context.args:
        try: t = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
        except: return
    if not t: await update.message.reply_text("🔊 _Reply /unmute_", parse_mode="Markdown"); return
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
        await update.message.reply_text(f"✅ *UNMUTED!* 🇮🇳\n👤 *{t.first_name}*\n🔓 `{nw.strftime('%I:%M %p, %d %b')}`\n💬 _Ab message kar sakta hai!_ 🎉", parse_mode="Markdown")
    except: pass

# ================== NEW FEATURES ==================

# 🌙 NIGHT MODE
async def cmd_nightmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown"); return
    except: return
    
    if not context.args or len(context.args) < 2:
        if cid in group_nightmode:
            nm = group_nightmode[cid]
            await update.message.reply_text(f"🌙 *Night Mode:* {nm['start']}:00 - {nm['end']}:00 IST\n`/nightmode off` — Disable", parse_mode="Markdown")
        else:
            await update.message.reply_text("🌙 */nightmode 22 6* — 10PM to 6AM\n`/nightmode off` — Disable", parse_mode="Markdown")
        return
    
    if context.args[0].lower() == "off":
        group_nightmode.pop(cid, None)
        await update.message.reply_text("✅ *Night Mode OFF!* 🟢", parse_mode="Markdown")
        return
    
    try:
        s, e = int(context.args[0]), int(context.args[1])
        group_nightmode[cid] = {"start": s, "end": e}
        await update.message.reply_text(f"🌙 *Night Mode ON!* 😴\n🕙 {s}:00 - {e}:00 IST\n\n⚠️ *Users messages DELETE honge!*", parse_mode="Markdown")
    except: pass

# ⏱️ SLOW MODE
async def cmd_slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *Sirf Admin!* 👑", parse_mode="Markdown"); return
    except: return
    
    if not context.args:
        await update.message.reply_text("⏱️ `/slowmode 5` — 5 sec\n`/slowmode off` — OFF", parse_mode="Markdown")
        return
    
    if context.args[0].lower() == "off":
        group_slowmode.pop(cid, None)
        last_message_time.pop(cid, None)
        await update.message.reply_text("✅ *Slow Mode OFF!* 🚀", parse_mode="Markdown")
        return
    
    try:
        sec = int(context.args[0])
        group_slowmode[cid] = sec
        await update.message.reply_text(f"⏱️ *Slow Mode ON!* 🐌\n⏱️ {sec}s delay\n🗑️ Fast msg = DELETE", parse_mode="Markdown")
    except: pass

# 🎮 GAMES
async def cmd_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("🎯 Number Guess", callback_data="gm_guess")],
        [InlineKeyboardButton("✊ Rock Paper Scissors", callback_data="gm_rps")],
        [InlineKeyboardButton("🎲 Roll Dice", callback_data="gm_dice")],
        [InlineKeyboardButton("❓ Quiz", callback_data="gm_quiz")],
        [InlineKeyboardButton("🔤 Word Scramble", callback_data="gm_scramble")],
    ]
    await update.message.reply_text("🎮 *GAME CENTER* 🔥\n\nButton dabao aur khelo! 🏆", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def game_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = update.effective_chat.id
    choice = query.data
    
    if choice == "gm_guess":
        group_games[cid] = {"type": "guess", "number": random.randint(1, 100), "attempts": 0}
        await query.edit_message_text("🎯 *Guess karo!* Maine 1-100 socha!\n💬 Chat mein number likho!", parse_mode="Markdown")
    elif choice == "gm_rps":
        group_games[cid] = {"type": "rps"}
        await query.edit_message_text("✊ *RPS!* Type: `rock` `paper` `scissors`", parse_mode="Markdown")
    elif choice == "gm_dice":
        d = random.randint(1, 6)
        df = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        await query.edit_message_text(f"🎲 *DICE!*\n\n{df[d]} *{d}*", parse_mode="Markdown")
    elif choice == "gm_quiz":
        qs = [{"q": "🌍 India capital?", "a": "delhi"}, {"q": "🧮 15+27?", "a": "42"}, {"q": "🎬 DDLJ hero?", "a": "shah rukh khan"}, {"q": "🏏 Most ODI 100s?", "a": "sachin tendulkar"}]
        q = random.choice(qs)
        group_games[cid] = {"type": "quiz", "answer": q["a"]}
        await query.edit_message_text(f"❓ *QUIZ!*\n\n{q['q']}\n💬 Answer likho!", parse_mode="Markdown")
    elif choice == "gm_scramble":
        words = ["python", "telegram", "bot", "coding", "india", "game", "computer"]
        w = random.choice(words)
        scr = ''.join(random.sample(w, len(w)))
        group_games[cid] = {"type": "scramble", "answer": w}
        await query.edit_message_text(f"🔤 *SCRAMBLE!*\n\n`{scr}`\n💬 Sahi word likho!", parse_mode="Markdown")

# 📊 POLLS
async def cmd_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if len(context.args) < 3:
        await update.message.reply_text("📊 `/poll \"Q\" \"A\" \"B\" \"C\"`", parse_mode="Markdown"); return
    text = " ".join(context.args)
    parts = re.findall(r'"([^"]*)"', text)
    if len(parts) < 3: await update.message.reply_text("❌ Quotes use karo!", parse_mode="Markdown"); return
    q, opts = parts[0], parts[1:]
    if cid not in group_polls: group_polls[cid] = {}
    pid = str(len(group_polls[cid]) + 1)
    kb = []
    for i, o in enumerate(opts):
        kb.append([InlineKeyboardButton(f"{o} (0)", callback_data=f"pv_{pid}_{i}")])
    kb.append([InlineKeyboardButton("📊 Results", callback_data=f"pr_{pid}")])
    group_polls[cid][pid] = {"q": q, "opts": opts, "votes": {i: set() for i in range(len(opts))}}
    await update.message.reply_text(f"📊 *POLL #{pid}*\n\n*Q:* {q}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def poll_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    cid = update.effective_chat.id
    d = query.data
    if d.startswith("pv_"):
        _, pid, oid = d.split("_"); oid = int(oid)
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]
            for v in poll["votes"].values(): v.discard(uid)
            poll["votes"][oid].add(uid)
            kb = []
            for i, o in enumerate(poll["opts"]):
                kb.append([InlineKeyboardButton(f"{o} ({len(poll['votes'][i])})", callback_data=f"pv_{pid}_{i}")])
            kb.append([InlineKeyboardButton("📊 Results", callback_data=f"pr_{pid}")])
            try: await query.edit_message_reply_markup(InlineKeyboardMarkup(kb))
            except: pass
            await query.answer("✅ Voted!")
    elif d.startswith("pr_"):
        pid = d.split("_")[1]
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]
            total = sum(len(v) for v in poll["votes"].values())
            r = f"📊 *RESULTS #{pid}*\n\n"
            for i, o in enumerate(poll["opts"]):
                vc = len(poll["votes"][i])
                pct = (vc/total*100) if total > 0 else 0
                r += f"*{o}:* {vc} ({pct:.1f}%)\n"
            await query.edit_message_text(r, parse_mode="Markdown")

# 🔞 FILTERS
async def cmd_addfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    w = " ".join(context.args).lower()
    if cid not in group_filters: group_filters[cid] = []
    if w not in group_filters[cid]: group_filters[cid].append(w); await update.message.reply_text(f"🔞 *Filtered:* `{w}`", parse_mode="Markdown")

async def cmd_rmfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    w = " ".join(context.args).lower()
    if cid in group_filters and w in group_filters[cid]: group_filters[cid].remove(w); await update.message.reply_text(f"✅ *Removed:* `{w}`", parse_mode="Markdown")

async def cmd_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_filters and group_filters[cid]:
        await update.message.reply_text("🔞 *FILTERS*\n" + "\n".join([f"• `{w}`" for w in group_filters[cid]]), parse_mode="Markdown")
    else: await update.message.reply_text("🔞 _No filters!_", parse_mode="Markdown")

# ✨ WELCOME/GOODBYE
async def cmd_setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    group_welcome_msgs[cid] = " ".join(context.args)
    await update.message.reply_text("✅ *Welcome Set!* ✨", parse_mode="Markdown")

async def cmd_setgoodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    group_goodbye_msgs[cid] = " ".join(context.args)
    await update.message.reply_text("✅ *Goodbye Set!* 👋", parse_mode="Markdown")

# 🏆 RANKS
async def cmd_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = update.effective_user.id
    if update.message.reply_to_message: uid = update.message.reply_to_message.from_user.id
    if cid not in group_ranks: group_ranks[cid] = {}
    score = group_ranks[cid].get(uid, 0)
    if score < 50: lvl = "🌱 Beginner"
    elif score < 200: lvl = "🌟 Active"
    elif score < 500: lvl = "💎 Pro"
    else: lvl = "🔥 LEGEND"
    await update.message.reply_text(f"🏆 *RANK*\n⭐ XP: {score}\n🏅 Level: {lvl}", parse_mode="Markdown")

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid not in group_ranks or not group_ranks[cid]:
        await update.message.reply_text("🏆 _No XP yet!_", parse_mode="Markdown"); return
    top = sorted(group_ranks[cid].items(), key=lambda x: x[1], reverse=True)[:10]
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lb = "🏆 *LEADERBOARD*\n\n"
    for i, (uid, score) in enumerate(top, 1):
        try:
            u = await context.bot.get_chat(uid); name = u.first_name
        except: name = f"User{uid}"
        lb += f"{medals.get(i, f'#{i}')} *{name}* — {score} XP\n"
    await update.message.reply_text(lb, parse_mode="Markdown")

# 📱 AFK
async def cmd_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    reason = " ".join(context.args) if context.args else "AFK"
    group_afk[uid] = {"reason": reason, "time": get_ist_now(), "name": update.effective_user.first_name}
    await update.message.reply_text(f"😴 *AFK ON!*\n📝 {reason}", parse_mode="Markdown")

# 🎰 FUN
async def cmd_flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🪙 *{random.choice(['Heads', 'Tails'])}!*", parse_mode="Markdown")

async def cmd_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = int(context.args[0]) if context.args and context.args[0].isdigit() else 6
    await update.message.reply_text(f"🎲 *{random.randint(1, max(2, s))}*", parse_mode="Markdown")

async def cmd_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    opts = [o.strip() for o in " ".join(context.args).replace(" or ", ",").split(",") if o.strip()]
    if len(opts) >= 2: await update.message.reply_text(f"✨ *{random.choice(opts)}*", parse_mode="Markdown")

async def cmd_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    f = ["🐙 Octopus ke 3 dil!", "🍯 Honey kabhi kharab nahi hoti!", "⚡ Lightning 8.6M/day!", "🧠 Brain 20W power!"]
    await update.message.reply_text(f"🤯 *{random.choice(f)}*", parse_mode="Markdown")

async def cmd_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    j = ["😂 Teacher: 'Late kyun?' Student: 'Corner tha!'", "🤣 Santa: 'Pizza download nahi hua!'"]
    await update.message.reply_text(f"😄 *{random.choice(j)}*", parse_mode="Markdown")

async def cmd_shayari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = ["💕 *Mohabbat mein khoya sab kuch...*", "🌟 *Zindagi ek safar hai...*"]
    await update.message.reply_text(random.choice(s), parse_mode="Markdown")

async def cmd_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = ["💭 *'Stay hungry, stay foolish.'* — Jobs", "💭 *'Think different.'* — Apple"]
    await update.message.reply_text(random.choice(q), parse_mode="Markdown")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    s = f"📊 *STATS*\n📝 Notes: {len(group_notes.get(cid, []))}\n🔞 Filters: {len(group_filters.get(cid, []))}\n🏆 Ranked: {len(group_ranks.get(cid, {}))}\n⏱️ Slow: {group_slowmode.get(cid, 'OFF')}s\n🌙 Night: {'ON' if cid in group_nightmode else 'OFF'}"
    await update.message.reply_text(s, parse_mode="Markdown")

async def cmd_google(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args: await update.message.reply_text(f"🔍 https://www.google.com/search?q={'+'.join(context.args)}", disable_web_page_preview=False)

async def cmd_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args: await update.message.reply_text(f"▶️ https://www.youtube.com/results?search_query={'+'.join(context.args)}", disable_web_page_preview=False)

# ================== START/ACTIVATE/DEACTIVATE ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK BOSS!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 *AVANTIKA AI — PREMIUM BOT*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ *Premium AI Replies*\n✅ *All Languages* 🌍\n✅ *Coding Master* 💻\n✅ *Knowledge Bank* 📚\n✅ *Fun & Jokes* 😂\n"
                "✅ *Games* 🎮\n✅ *Night Mode* 🌙\n✅ *Slow Mode* ⏱️\n✅ *Polls* 📊\n✅ *Filters* 🔞\n"
                "✅ *Mute System* 🔇\n✅ *Ban System* 🔨\n✅ *Warning System* ⚠️\n✅ *Group Rules* 📜\n✅ *Notes System* 📝\n✅ *Pin Messages* 📌\n"
                "✅ *User Management* 👥\n✅ *Broadcast* 📢\n\n"
                "⚡ *COMMANDS:*\n/start /clear /activate /help\n/mute /unmute /ban /unban /warn\n/nightmode /slowmode /game /poll\n/setrules /rules /addnote /notes\n/pin /unpin /info /rank /afk\n/adduser /removeuser /userlist\n/broadcast /id\n\n"
                "_Bolo boss!_ 🔥",
                parse_mode="Markdown"
            )
        elif is_allowed(uid): user_history[cid] = []; await update.message.reply_text("✅ *Access Granted!*\n💬 _Ask anything!_", parse_mode="Markdown")
        else: await update.message.reply_text("🔒 *Access Denied!*", parse_mode="Markdown")
    else:
        user_history[cid] = []
        await update.message.reply_text(
            "👋 *AVANTIKA AI — PREMIUM BOT* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 Admin */activate* karo\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔇 `/mute` | 🔊 `/unmute` | 🔨 `/ban`\n"
            "⚠️ `/warn` | 📜 `/rules` | 📝 `/notes`\n"
            "🎮 `/game` | 🌙 `/nightmode` | ⏱️ `/slowmode`\n"
            "📊 `/poll` | 📌 `/pin` | 🆔 `/id`\n\n"
            "_Activate karo — dhamaka!_ 🔥",
            parse_mode="Markdown"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *ADMIN ONLY!* 👑\n\n1️⃣ Bot ko *ADMIN* banao\n2️⃣ Sab *permissions ON* karo\n3️⃣ `/activate`", parse_mode="Markdown"); return
    except: await update.message.reply_text("❌ *Bot ko ADMIN banao!*", parse_mode="Markdown"); return
    
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text(
        "✅ *ACTIVATED!* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *ALL SYSTEMS GO!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 AI | 🎮 Games | 📊 Polls\n"
        "🌙 Night Mode | ⏱️ Slow Mode\n"
        "🔇 Mute | 🔨 Ban | ⚠️ Warn\n"
        "📜 Rules | 📝 Notes | 📌 Pin\n"
        "🔞 Filters | 🏆 Ranks | 📱 AFK\n"
        "👋 Welcome | 🎰 Fun Commands\n\n"
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
    group_warnings.pop(cid, None); group_rules.pop(cid, None); group_notes.pop(cid, None)
    group_nightmode.pop(cid, None); group_slowmode.pop(cid, None); group_games.pop(cid, None)
    group_polls.pop(cid, None); group_filters.pop(cid, None); group_ranks.pop(cid, None)
    await update.message.reply_text("✅ *COMPLETE RESET!* 🔄\n\n💭 Memory ✅\n⚠️ Warnings ✅\n📜 Rules ✅\n📝 Notes ✅\n🌙 Night ✅\n⏱️ Slow ✅\n🎮 Games ✅\n🔞 Filters ✅\n\n🆕 _Fresh start!_ 💎", parse_mode="Markdown")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *AVANTIKA AI — HELP* 💎\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👑 *ADMIN:*\n"
        "/activate /deactivate /mute /unmute\n"
        "/ban /unban /warn /clearwarns\n"
        "/nightmode 22 6 /nightmode off\n"
        "/slowmode 5 /slowmode off\n"
        "/poll \"Q\" \"A\" \"B\"\n"
        "/addfilter /rmfilter /filters\n"
        "/setwelcome /setgoodbye\n"
        "/setrules /addnote /clearnotes\n"
        "/pin /unpin\n\n"
        "👥 *USERS:*\n"
        "/help /info /id /rules /notes\n"
        "/rank /leaderboard /game\n"
        "/afk /stats /flip /dice\n"
        "/choose /fact /joke /shayari\n"
        "/quote /google /youtube\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    
    # WELCOME
    if msg.new_chat_members:
        await welcome(update, context)
        return
    
    # GOODBYE
    if msg.left_chat_member:
        user = msg.left_chat_member
        if user.id != context.bot.id and cid in group_goodbye_msgs:
            gm = group_goodbye_msgs[cid].replace("{name}", user.first_name).replace("{id}", str(user.id))
            await context.bot.send_message(cid, gm, parse_mode="Markdown")
        return
    
    # PRIVATE CHAT
    if ct == ChatType.PRIVATE and not is_allowed(uid):
        await msg.reply_text("🔒 *Permission nahi!*", parse_mode="Markdown")
        return
    
    # GROUP: MUST BE ACTIVATED
    if ct != ChatType.PRIVATE and (cid not in active_groups or not active_groups[cid]):
        return
    
    # ===== NIGHT MODE: DELETE NON-ADMIN MESSAGES =====
    if ct != ChatType.PRIVATE and is_night_mode_on(cid):
        admin_ids = await get_admin_ids(cid, context)
        if uid not in admin_ids:
            try: await msg.delete()
            except: pass
            return
    
    # ===== SLOW MODE: DELETE FAST MESSAGES =====
    if ct != ChatType.PRIVATE and cid in group_slowmode:
        admin_ids = await get_admin_ids(cid, context)
        if uid not in admin_ids:
            now = datetime.now().timestamp()
            if cid not in last_message_time: last_message_time[cid] = {}
            last = last_message_time[cid].get(uid, 0)
            if now - last < group_slowmode[cid]:
                try: await msg.delete()
                except: pass
                return
            last_message_time[cid][uid] = now
    
    if not msg.text: return
    
    # ===== GAME HANDLING =====
    if cid in group_games:
        game = group_games[cid]
        txt = msg.text.lower().strip()
        
        if game["type"] == "guess":
            try:
                g = int(txt); game["attempts"] += 1
                if g == game["number"]:
                    await msg.reply_text(f"🎯 *CORRECT!* 🎉\nNumber: {game['number']}\nAttempts: {game['attempts']}", parse_mode="Markdown")
                    del group_games[cid]; return
                elif g < game["number"]: await msg.reply_text(f"📈 Higher! (#{game['attempts']})", parse_mode="Markdown")
                else: await msg.reply_text(f"📉 Lower! (#{game['attempts']})", parse_mode="Markdown")
                return
            except: pass
        
        elif game["type"] == "rps":
            if txt in ["rock", "paper", "scissors"]:
                b = random.choice(["rock", "paper", "scissors"])
                e = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
                if txt == b: r = "🤝 TIE!"
                elif (txt=="rock" and b=="scissors") or (txt=="paper" and b=="rock") or (txt=="scissors" and b=="paper"): r = "🎉 YOU WIN!"
                else: r = "😢 BOT WINS!"
                await msg.reply_text(f"✊ You: {e[txt]} | Bot: {e[b]}\n\n{r}", parse_mode="Markdown")
                del group_games[cid]; return
        
        elif game["type"] == "quiz":
            if txt == game["answer"]:
                await msg.reply_text("✅ *CORRECT!* 🎉", parse_mode="Markdown")
                del group_games[cid]; return
        
        elif game["type"] == "scramble":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *CORRECT!* 🎉\nWord: *{game['answer']}*", parse_mode="Markdown")
                del group_games[cid]; return
    
    # ===== FILTER CHECK =====
    if cid in group_filters:
        for w in group_filters[cid]:
            if w in msg.text.lower():
                try: await msg.delete()
                except: pass
                await msg.reply_text(f"🔞 *Filtered!* ⚠️", parse_mode="Markdown")
                return
    
    # ===== AFK CHECK =====
    if msg.reply_to_message and msg.reply_to_message.from_user:
        ruid = msg.reply_to_message.from_user.id
        if ruid in group_afk and ruid != uid:
            afk = group_afk[ruid]
            diff = get_ist_now() - afk["time"]
            h, rem = divmod(int(diff.total_seconds()), 3600)
            m, _ = divmod(rem, 60)
            ts = f"{h}h {m}m" if h else f"{m}m"
            await msg.reply_text(f"😴 *AFK!*\n👤 {afk['name']}\n📝 {afk['reason']}\n⏱️ {ts} ago", parse_mode="Markdown")
    
    # ===== RANK UPDATE =====
    if ct != ChatType.PRIVATE:
        if cid not in group_ranks: group_ranks[cid] = {}
        if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
        group_ranks[cid][uid] += random.randint(1, 3)
    
    # ===== AI REPLY =====
    await context.bot.send_chat_action(chat_id=cid, action="typing")
    
    try:
        reply = get_ai_reply(msg.text, cid)
        if cid not in user_history: user_history[cid] = []
        user_history[cid].append({"role":"user","content":msg.text})
        user_history[cid].append({"role":"assistant","content":reply})
        user_history[cid] = user_history[cid][-10:]
        await msg.reply_text(reply, parse_mode="Markdown")
    except: pass

# ================== MAIN ==================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    commands = [
        ("start",start),("help",cmd_help),("activate",activate),("deactivate",deactivate),("clear",clear),
        ("mute",mute_user),("unmute",unmute_user),("ban",ban_user),("unban",unban_user),
        ("warn",warn),("clearwarns",clearwarns),("setrules",setrules),("rules",rules),
        ("addnote",addnote),("notes",notes),("clearnotes",clearnotes),
        ("pin",pin),("unpin",unpin),("info",info),
        ("adduser",adduser),("removeuser",removeuser),("userlist",userlist),
        ("broadcast",broadcast),("id",get_id),
        # NEW COMMANDS
        ("nightmode",cmd_nightmode),("slowmode",cmd_slowmode),
        ("game",cmd_game),("poll",cmd_poll),
        ("addfilter",cmd_addfilter),("rmfilter",cmd_rmfilter),("filters",cmd_filters),
        ("setwelcome",cmd_setwelcome),("setgoodbye",cmd_setgoodbye),
        ("rank",cmd_rank),("leaderboard",cmd_leaderboard),("afk",cmd_afk),
        ("flip",cmd_flip),("dice",cmd_dice),("choose",cmd_choose),
        ("fact",cmd_fact),("joke",cmd_joke),("shayari",cmd_shayari),("quote",cmd_quote),
        ("stats",cmd_stats),("google",cmd_google),("youtube",cmd_youtube),
    ]
    
    for cmd, fn in commands:
        app.add_handler(CommandHandler(cmd, fn))
    
    # Button handlers
    app.add_handler(CallbackQueryHandler(game_click, pattern="^gm_"))
    app.add_handler(CallbackQueryHandler(poll_click, pattern="^p[vr]_"))
    
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("👑 AVANTIKA AI — PREMIUM BOT 🔥")
    print("✅ AI Chat: /activate ke baad ON")
    print("✅ Night Mode: Msg DELETE working")
    print("✅ Slow Mode: Fast msg DELETE working")
    print("✅ Games: 5 types working")
    print("✅ Polls, Filters, Ranks, AFK — ALL WORKING!")
    app.run_polling()

if __name__ == "__main__":
    main()
