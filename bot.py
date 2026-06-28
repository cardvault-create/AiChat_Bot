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
started_groups = {}
allowed_users = {7614459746}
group_warnings = {}
group_rules = {}
group_notes = {}
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

# ================== ♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡ ==================
SONAKSHI_PREAMBLE = """You are ♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡ — Premium, Smart, Beautiful Multi-Language AI Assistant 🫧✨💖

*Your Personality:*
- Sweet, caring, and friendly like a best friend 💕
- Smart and knowledgeable like a genius 🧠
- Fun and entertaining like a entertainer 🎭

*RULES:*
1. Detect user's language & reply in SAME language
2. Use *Bold* (**text**) & _Italic_ (_text_) formatting ALWAYS
3. Use beautiful emojis: 🫧✨💖💕🌸🦋💎🌟⚡🔥🎯❤️😊🤗💬📚💻😂🎉🏆👑💭🔍▶️
4. Give detailed, helpful, beautiful answers
5. Coding → working code with explanation
6. Knowledge → accurate info
7. Fun → jokes, shayari, motivational quotes
8. Always end with a sweet touch! 🫧"""

def get_ist_now(): 
    return datetime.now(IST)

def parse_time(ts):
    ts = ts.lower().strip().replace(" ", "")
    if not ts: return None
    patterns = [
        ('seconds',1/60),('second',1/60),('sec',1/60),('secs',1/60),('s',1/60),
        ('minutes',1),('minute',1),('mins',1),('min',1),('m',1),
        ('hours',60),('hour',60),('hrs',60),('hr',60),('h',60),
        ('days',1440),('day',1440),('d',1440),
    ]
    for suffix, multiplier in patterns:
        if ts.endswith(suffix):
            try: return float(ts[:-len(suffix)]) * multiplier
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
        resp = co.chat(message=text, chat_history=ch, preamble=SONAKSHI_PREAMBLE, temperature=0.95, max_tokens=800)
        return resp.text
    except: return "😅 *_Oops! Kuch error aaya... Fir se bolo na!_* 🫧💕"

async def get_admin_ids(chat_id, context):
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        return {a.user.id for a in admins}
    except: return set()

def is_night_mode_active(chat_id):
    if chat_id not in group_nightmode: return False
    now = get_ist_now()
    h = now.hour
    s = group_nightmode[chat_id]["start"]
    e = group_nightmode[chat_id]["end"]
    return (s <= h < e) if s < e else (h >= s or h < e)

# ================== GAME BACK BUTTON ==================
def get_game_menu_keyboard():
    """Game menu with back button"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Number Guess (1-100)", callback_data="gm_guess")],
        [InlineKeyboardButton("✊ Rock Paper Scissors", callback_data="gm_rps")],
        [InlineKeyboardButton("🎲 Lucky Dice Roll", callback_data="gm_dice")],
        [InlineKeyboardButton("❓ Brain Quiz Challenge", callback_data="gm_quiz")],
        [InlineKeyboardButton("🔤 Word Scramble Puzzle", callback_data="gm_scramble")],
        [InlineKeyboardButton("🧮 Math Challenge", callback_data="gm_math")],
        [InlineKeyboardButton("🎭 Truth or Dare", callback_data="gm_truth")],
        [InlineKeyboardButton("🤔 Riddle Master", callback_data="gm_riddle")],
        [InlineKeyboardButton("🔤 Word Chain", callback_data="gm_wordchain")],
    ])

def get_back_button(game_type=""):
    """Return back button for games"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Game Menu", callback_data=f"gm_back")]
    ])

# ================== OWNER COMMANDS ==================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: 
        await update.message.reply_text("❌ *_Sirf BOSS kar sakta hai!_* 👑", parse_mode="Markdown"); return
    if not context.args: return
    try: allowed_users.add(int(context.args[0])); await update.message.reply_text(f"✅ *_User Added!_* 🆔 `{context.args[0]}` 🫧", parse_mode="Markdown")
    except: pass

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: 
        await update.message.reply_text("❌ *_Sirf BOSS kar sakta hai!_* 👑", parse_mode="Markdown"); return
    if not context.args: return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: return
        allowed_users.discard(rid); await update.message.reply_text(f"✅ *_User Removed!_* 🆔 `{rid}` 🫧", parse_mode="Markdown")
    except: pass

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: return
    ul = "\n".join([f"• `{uid}` {'👑' if uid==OWNER_USER_ID else '✅'}" for uid in allowed_users])
    await update.message.reply_text(f"👥 *_Allowed Users_* 🫧\n\n{ul}\n\n📊 *_Total:_* {len(allowed_users)}", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: return
    if not context.args: return
    msg = "📢 *_BROADCAST_* 👑🫧\n\n" + " ".join(context.args)
    for uid in allowed_users:
        try: await context.bot.send_message(uid, msg, parse_mode="Markdown")
        except: pass

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message: await update.message.reply_text(f"🆔 `{update.message.reply_to_message.from_user.id}` 🫧", parse_mode="Markdown")
    else: await update.message.reply_text(f"🆔 `{update.effective_user.id}` 🫧", parse_mode="Markdown")

# ================== NOTES ==================
async def addnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(context.args))
    await update.message.reply_text(f"✅ *_Note Added!_* 📝 (#{len(group_notes[cid])}) 🫧", parse_mode="Markdown")

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]: 
        await update.message.reply_text("📝 *_Notes_* 🫧\n\n" + "\n".join([f"• _{n}_" for n in group_notes[cid]]), parse_mode="Markdown")
    else: await update.message.reply_text("📝 *_No notes yet!_* 🫧\n_Use_ `/addnote`", parse_mode="Markdown")

async def clearnotes(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    group_notes[update.effective_chat.id] = []
    await update.message.reply_text("✅ *_All Notes Cleared!_* 🗑️🫧", parse_mode="Markdown")

# ================== PIN ==================
async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: return
    try: await update.message.reply_to_message.pin(); await update.message.reply_text("📌 *_Pinned!_* ✅🫧", parse_mode="Markdown")
    except: pass

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    try: await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    except: pass

# ================== INFO ==================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(f"👤 *_USER INFO_* 🫧\n\n━━━━━━━━━━━━━━━━━━━━━━\n👤 *_Name:_* *{u.first_name}*\n🆔 *_ID:_* `{u.id}`\n📛 @{u.username or 'None'}\n━━━━━━━━━━━━━━━━━━━━━━", parse_mode="Markdown")
    else:
        try:
            c = await context.bot.get_chat(update.effective_chat.id)
            await update.message.reply_text(f"👥 *_GROUP INFO_* 🫧\n\n━━━━━━━━━━━━━━━━━━━━━━\n👥 *{c.title}*\n🆔 `{update.effective_chat.id}`\n━━━━━━━━━━━━━━━━━━━━━━", parse_mode="Markdown")
        except: pass

# ================== RULES ==================
async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not context.args: await update.message.reply_text("📝 *_Usage:_* `/setrules rules` 🫧", parse_mode="Markdown"); return
    group_rules[cid] = " ".join(context.args)
    await update.message.reply_text("📜 *_Rules Set!_* ✅🫧", parse_mode="Markdown")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_rules: await update.message.reply_text(f"📜 *_GROUP RULES_* 🫧\n\n━━━━━━━━━━━━━━━━━━━━━━\n{group_rules[cid]}\n━━━━━━━━━━━━━━━━━━━━━━", parse_mode="Markdown")
    else: await update.message.reply_text("📜 *_No rules yet!_* 🫧", parse_mode="Markdown")

# ================== WARN ==================
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not update.message.reply_to_message: await update.message.reply_text("⚠️ *_Reply to warn!_* 🫧", parse_mode="Markdown"); return
    t = update.message.reply_to_message.from_user
    if cid not in group_warnings: group_warnings[cid] = {}
    if t.id not in group_warnings[cid]: group_warnings[cid][t.id] = 0
    group_warnings[cid][t.id] += 1
    wc = group_warnings[cid][t.id]
    await update.message.reply_text(f"⚠️ *_WARNING {wc}/3_* ⚡🫧\n\n👤 *{t.first_name}*\n{'🔴 *3 = MUTE!*' if wc>=3 else '⚡ _Be careful!_'}",
        parse_mode="Markdown")

async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if cid in group_warnings and t.id in group_warnings[cid]: group_warnings[cid][t.id] = 0
    else: group_warnings[cid] = {}
    await update.message.reply_text("✅ *_Warnings Cleared!_* 🧹🫧", parse_mode="Markdown")

# ================== BAN ==================
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_Sirf Admin!_* 👑🫧", parse_mode="Markdown"); return
    except: return
    t = None
    if update.message.reply_to_message: t = update.message.reply_to_message.from_user
    elif context.args:
        try: t = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
        except: pass
    if not t or t.id == update.effective_user.id or t.is_bot: 
        await update.message.reply_text("❌ *_Can't ban!_* 🫧", parse_mode="Markdown"); return
    try:
        await context.bot.ban_chat_member(cid, t.id)
        await update.message.reply_text(f"🔨 *_BANNED!_* 🚫🫧\n\n━━━━━━━━━━━━━━━━━━━━━━\n👤 *{t.first_name}*\n🆔 `{t.id}`\n━━━━━━━━━━━━━━━━━━━━━━\n🔓 `/unban {t.id}`", parse_mode="Markdown")
    except: await update.message.reply_text("❌ *_Ban failed! Permissions do!_* 🫧", parse_mode="Markdown")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: await update.message.reply_text("📝 `/unban user_id` 🫧", parse_mode="Markdown"); return
    try:
        await context.bot.unban_chat_member(cid, int(context.args[0]))
        await update.message.reply_text(f"✅ *_UNBANNED!_* 🔓🫧\n🆔 `{context.args[0]}`", parse_mode="Markdown")
    except: await update.message.reply_text("❌ *_Unban failed!_* 🫧", parse_mode="Markdown")

# ================== PREMIUM WELCOME ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            await context.bot.send_message(
                chat_id=cid,
                text=(
                    "✨ *♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡* ✨\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "🫧 *_PREMIUM AI ASSISTANT JOINED!_* 🫧\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "💖 *_Hey Beautiful People!_* 💖\n\n"
                    "🌸 _Main hoon_ *Ｓｏｎａｋｓｈｉ* — _aapki smart,_\n"
                    "_caring aur mast AI bestie!_ 🦋\n\n"
                    "👑 *_Admin ji suno:_*\n"
                    "• `/start` _karo — Sab features ON karo_ ⚡\n"
                    "• `/activate` _karo — Mujhe awake karo_ 💬\n\n"
                    "🎭 *_Main kya kya kar sakti hoon?_*\n"
                    "• 💬 *_AI Chat_* — _Mujhse baat karo!_ 💕\n"
                    "• 🎮 *_9 Games_* — _Mast game khelo!_ 🏆\n"
                    "• 📊 *_Polls_* — _Live voting with buttons_\n"
                    "• 🌙 *_Night Mode_* — _Raat ko shanti_ 😴\n"
                    "• ⏱️ *_Slow Mode_* — _Spam se bachao_\n"
                    "• 🔇 *_Mute_* | 🔨 *_Ban_* | ⚠️ *_Warn_*\n"
                    "• 📜 *_Rules_* | 📝 *_Notes_* | 📌 *_Pin_*\n"
                    "• 😂 *_Jokes_* | 💕 *_Shayari_* | 🤯 *_Facts_*\n"
                    "• 🏆 *_Ranks_* | 📱 *_AFK_* | 🔍 *_Search_*\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "📋 `/help` — _Sab commands ek jagah!_ 💬\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "💖 *_Chaloo dhamaka karte hain!_* 🫧✨🌸"
                ),
                parse_mode="Markdown"
            )
        else:
            wm = group_welcome_msgs.get(cid, 
                f"🌸 *_WELCOME TO THE FAMILY!_* 🌸\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✨ *_Heyy_* *{user.first_name}* ✨\n"
                f"🆔 *_ID:_* `{user.id}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🫧 *_Aapka dil se swagat hai!_* 💖\n\n"
                f"💎 *_Yahaan aapko milega:_*\n"
                f"• 💬 *_AI Chat_* — _Ｓｏｎａｋｓｈｉ se baat_\n"
                f"• 🎮 *_9 Games_* — _Mast maza!_ 🏆\n"
                f"• 💻 *_Coding Help_* — _Working code_\n"
                f"• 📚 *_Knowledge_* — _Accurate info_\n"
                f"• 😂 *_Fun & Masti_* — _Jokes, Shayari_\n\n"
                f"📢 *_Kuch bhi puchho — main hoon na!_* 💬\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💖 *_Enjoy karo aur khush raho!_* 🫧🌸\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            wm = wm.replace("{name}", f"*{user.first_name}*").replace("{id}", f"`{user.id}`").replace("{mention}", f"[{user.first_name}](tg://user?id={user.id})")
            await context.bot.send_message(chat_id=cid, text=wm, parse_mode="Markdown")

# ================== MUTE ==================
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: 
        await update.message.reply_text("⚡ *_Sirf Group mein!_* 🫧", parse_mode="Markdown"); return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_Sirf Admin!_* 👑🫧", parse_mode="Markdown"); return
    except: await update.message.reply_text("❌ *_Bot ko Admin banao!_* 🫧", parse_mode="Markdown"); return
    
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
            "🔇 *_MUTE SYSTEM_* 🇮🇳🫧\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 `/mute 10s` `/mute 5m`\n"
            "📌 `/mute 2h` `/mute 1d`\n"
            "📌 `/mute 123456 2h`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⏰ *_Auto Unmute ON_*",
            parse_mode="Markdown"
        ); return
    
    if not t or t.id == update.effective_user.id or t.is_bot: return
    mm = parse_time(ts)
    if not mm or mm > 43200 or mm <= 0: return
    
    nw = get_ist_now(); ut = nw + timedelta(minutes=mm)
    try:
        await context.bot.restrict_chat_member(chat_id=cid, user_id=t.id,
            permissions=ChatPermissions(can_send_messages=False, can_send_audios=False, can_send_documents=False,
                can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
                can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
                can_add_web_page_previews=False, can_change_info=False, can_invite_users=False, can_pin_messages=False),
            until_date=ut)
        tn = t.first_name or "User"
        if t.last_name: tn += f" {t.last_name}"
        await update.message.reply_text(
            f"🔇 *_MUTED!_* 🇮🇳🫧\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *{tn}*\n🆔 `{t.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ {format_time(mm)}\n"
            f"📅 `{nw.strftime('%I:%M %p')}`\n"
            f"🔓 `{ut.strftime('%I:%M %p, %d %b')}`\n\n"
            f"⏰ *_Auto Unmute ON_* 🫧",
            parse_mode="Markdown")
        async def auto():
            await asyncio.sleep(mm * 60)
            try:
                await context.bot.restrict_chat_member(chat_id=cid, user_id=t.id,
                    permissions=ChatPermissions(can_send_messages=True, can_send_audios=True, can_send_documents=True,
                        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                        can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                        can_add_web_page_previews=True, can_change_info=False, can_invite_users=False, can_pin_messages=False))
                await context.bot.send_message(cid, f"✅ *_AUTO UNMUTED!_* 🫧\n👤 *{tn}*\n💬 *_Ab message kar sakta hai!_* 🎉", parse_mode="Markdown")
            except: pass
        asyncio.create_task(auto())
    except: await update.message.reply_text("❌ *_Mute Failed!_* 🫧", parse_mode="Markdown")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t and context.args:
        try: t = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
        except: return
    if not t: await update.message.reply_text("🔊 *_Reply karo ya ID do!_* 🫧", parse_mode="Markdown"); return
    try:
        await context.bot.restrict_chat_member(chat_id=cid, user_id=t.id,
            permissions=ChatPermissions(can_send_messages=True, can_send_audios=True, can_send_documents=True,
                can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                can_add_web_page_previews=True, can_change_info=False, can_invite_users=False, can_pin_messages=False))
        await update.message.reply_text(f"✅ *_UNMUTED!_* 🔓🫧\n👤 *{t.first_name}*\n💬 *_Ab message kar sakta hai!_* 🎉", parse_mode="Markdown")
    except: pass

# ================== NIGHT MODE ==================
async def cmd_nightmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_Sirf Admin!_* 👑🫧", parse_mode="Markdown"); return
    except: return
    if context.args and context.args[0].lower() == "off":
        if cid in group_nightmode: del group_nightmode[cid]
        await update.message.reply_text("✅ *_Night Mode OFF!_* 🟢🫧\n\n_Ab sab message kar sakte hain!_ 💬🌸", parse_mode="Markdown")
        return
    if not context.args or len(context.args) < 2:
        if cid in group_nightmode:
            nm = group_nightmode[cid]
            await update.message.reply_text(f"🌙 *_Night Mode:_* {nm['start']}:00-{nm['end']}:00 IST 🫧\n`/nightmode off` — _Disable_", parse_mode="Markdown")
        else:
            await update.message.reply_text("🌙 `/nightmode 22 6` — _10PM-6AM_ 🫧\n`/nightmode off` — _Disable_", parse_mode="Markdown")
        return
    try:
        s, e = int(context.args[0]), int(context.args[1])
        group_nightmode[cid] = {"start": s, "end": e}
        await update.message.reply_text(f"✅ *_Night Mode Set!_* 🌙🫧\n🕙 {s}:00-{e}:00 IST\n\n⚠️ *_Users messages DELETE honge!_*\n`/nightmode off` — _Disable_", parse_mode="Markdown")
    except: pass

# ================== SLOW MODE ==================
async def cmd_slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_Sirf Admin!_* 👑🫧", parse_mode="Markdown"); return
    except: return
    if context.args and context.args[0].lower() == "off":
        if cid in group_slowmode: del group_slowmode[cid]
        if cid in last_message_time: del last_message_time[cid]
        await update.message.reply_text("✅ *_Slow Mode OFF!_* 🚀🫧", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("⏱️ `/slowmode 5` — _5 sec_ 🫧\n`/slowmode off` — _OFF_", parse_mode="Markdown")
        return
    try:
        sec = int(context.args[0])
        if sec <= 0:
            if cid in group_slowmode: del group_slowmode[cid]
            await update.message.reply_text("✅ *_Slow Mode OFF!_* 🚀🫧", parse_mode="Markdown")
        else:
            group_slowmode[cid] = sec
            await update.message.reply_text(f"⏱️ *_Slow Mode ON:_* `{sec}s` 🐌🫧\n🗑️ Fast msg = DELETE\n`/slowmode off` — _Disable_", parse_mode="Markdown")
    except: pass

# ================== ADVANCED GAME SYSTEM WITH BACK BUTTONS ==================
async def cmd_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Game Center - Main Menu"""
    cid = update.effective_chat.id
    await update.message.reply_text(
        "🎮 *♡ Ｓｏｎａｋｓｈｉ ＧＡＭＥ ＣＥＮＴＥＲ ♡* 🫧\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💖 *_Mazedaar Games Khelo!_* 💖\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🌟 *_9 Different Games Available!_*\n"
        "🏆 _Jeetne par XP milega!_\n"
        "🔙 _Har game mein Back button hai!_\n\n"
        "👇 *_Button dabao aur khelo!_* 👇",
        reply_markup=get_game_menu_keyboard(),
        parse_mode="Markdown"
    )

async def game_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ALL game button clicks"""
    query = update.callback_query
    await query.answer()
    cid = update.effective_chat.id
    choice = query.data
    
    # ========== BACK TO MENU ==========
    if choice == "gm_back":
        await query.edit_message_text(
            "🎮 *♡ Ｓｏｎａｋｓｈｉ ＧＡＭＥ ＣＥＮＴＥＲ ♡* 🫧\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💖 *_Mazedaar Games Khelo!_* 💖\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🌟 *_9 Different Games Available!_*\n"
            "🏆 _Jeetne par XP milega!_\n\n"
            "👇 *_Game choose karo!_* 👇",
            reply_markup=get_game_menu_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # ========== NUMBER GUESS ==========
    if choice == "gm_guess":
        number = random.randint(1, 100)
        group_games[cid] = {"type": "guess", "number": number, "attempts": 0, "max_attempts": 7}
        await query.edit_message_text(
            "🎯 *_NUMBER GUESS CHALLENGE!_* 🔢🫧\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🤔 _Maine 1-100 ke beech ek number socha!_\n"
            "🎯 *_7 attempts hain — Guess karo!_*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💬 *_Chat mein number guess karo!_*\n\n"
            "_Example: 50_\n\n"
            "🌟 _Hint: Bade ya chhote ka signal milega!_ 🫧",
            reply_markup=get_back_button(),
            parse_mode="Markdown"
        )
    
    # ========== RPS ==========
    elif choice == "gm_rps":
        group_games[cid] = {"type": "rps"}
        await query.edit_message_text(
            "✊ *_ROCK PAPER SCISSORS SHOWDOWN!_* ✂️🫧\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🪨 `rock` — _Pathar_\n"
            "📄 `paper` — _Kagaz_\n"
            "✂️ `scissors` — _Kainchi_\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💬 *_Chat mein type karo apni choice!_*\n"
            "🤖 _Ｓｏｎａｋｓｈｉ bhi apni choice degi!_ 💖",
            reply_markup=get_back_button(),
            parse_mode="Markdown"
        )
    
    # ========== DICE ==========
    elif choice == "gm_dice":
        d = random.randint(1, 6)
        df = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        lucky = "\n🌟 *_LUCKY NUMBER 6! EXTRA XP!_* 🎉" if d == 6 else ""
        await query.edit_message_text(
            f"🎲 *_LUCKY DICE ROLL!_* 🎲🫧\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{df[d]}  *_ROLLED:_* `{d}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{lucky}\n\n"
            f"🎲 _Phir roll karo:_ `/dice`_ 🫧",
            reply_markup=get_back_button(),
            parse_mode="Markdown"
        )
    
    # ========== QUIZ ==========
    elif choice == "gm_quiz":
        qs = [
            {"q": "🌍 *_India ki capital kya hai?_*", "a": "delhi", "hint": "_D se start, dil wali jagah_ 💖"},
            {"q": "🧮 *_15 + 27 = ?_*", "a": "42", "hint": "_40 se thoda zyada, 45 se thoda kam_ 🤔"},
            {"q": "🎬 *_'DDLJ' film ke hero kaun?_*", "a": "shah rukh khan", "hint": "_King Khan, King of Romance_ 👑"},
            {"q": "🏏 *_Sabse zyada ODI centuries?_*", "a": "sachin tendulkar", "hint": "_Master Blaster, God of Cricket_ 🏏"},
            {"q": "💻 *_Python kab launch hui?_*", "a": "1991", "hint": "_1990s ki shuruwat, 199_ me_ 📅"},
            {"q": "🧬 *_DNA ka full form?_*", "a": "deoxyribonucleic acid", "hint": "_D se start, lamba naam hai_ 🧬"},
            {"q": "🌙 *_Chand par pehla kadam kab?_*", "a": "1969", "hint": "_1960s ke end mein_ 🚀"},
            {"q": "🎵 *_Sa Re Ga Ma ke kitne sur?_*", "a": "7", "hint": "_Week ke din jitne!_ 📅"},
        ]
        q = random.choice(qs)
        group_games[cid] = {"type": "quiz", "answer": q["a"], "hint": q["hint"], "hint_given": False, "wrong_count": 0}
        await query.edit_message_text(
            f"❓ *_BRAIN QUIZ CHALLENGE!_* 🧠🫧\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 {q['q']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 *_Chat mein answer likho!_*\n"
            f"💡 _Galat jawab diya to 2nd attempt pe hint milega!_ 🫧",
            reply_markup=get_back_button(),
            parse_mode="Markdown"
        )
    
    # ========== SCRAMBLE ==========
    elif choice == "gm_scramble":
        words = ["python", "telegram", "sonakshi", "coding", "india", "computer", "keyboard", "internet", "elephant", "chocolate"]
        w = random.choice(words)
        scr = ''.join(random.sample(w, len(w)))
        # Ensure scrambled is different
        while scr == w:
            scr = ''.join(random.sample(w, len(w)))
        group_games[cid] = {"type": "scramble", "answer": w, "attempts": 0}
        await query.edit_message_text(
            f"🔤 *_WORD SCRAMBLE PUZZLE!_* 🧩🫧\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔀 *_Scrambled:_* `{scr}`\n"
            f"📏 *_Letters:_* {len(w)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 *_Chat mein sahi word likho!_*\n"
            f"⏱️ _Jitni jaldi, utna zyada XP!_ 🫧",
            reply_markup=get_back_button(),
            parse_mode="Markdown"
        )
    
    # ========== MATH ==========
    elif choice == "gm_math":
        ops = ['+', '-', '×', '÷']
        op = random.choice(ops)
        if op == '+':
            a, b = random.randint(10, 99), random.randint(10, 99)
            ans = a + b
        elif op == '-':
            a, b = random.randint(50, 99), random.randint(10, 49)
            ans = a - b
        elif op == '×':
            a, b = random.randint(2, 25), random.randint(2, 12)
            ans = a * b
        else:
            b = random.randint(2, 12)
            ans = random.randint(2, 20)
            a = ans * b
        group_games[cid] = {"type": "math", "answer": str(ans)}
        await query.edit_message_text(
            f"🧮 *_MATH CHALLENGE!_* 🔢🫧\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📐 *_Solve karo:_* `{a} {op} {b} = ?`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 *_Answer chat mein likho!_*\n"
            f"⚡ _Fastest finger first! XP bonus!_ 🫧",
            reply_markup=get_back_button(),
            parse_mode="Markdown"
        )
    
    # ========== TRUTH ==========
    elif choice == "gm_truth":
        truths = [
            "😳 *_Aapka sabse embarrassing moment kya tha?_*",
            "😂 *_Aapne aakhri baar jhooth kab aur kyun bola tha?_*",
            "🤫 *_Aapka aisa secret jo kisi ko nahi pata?_*",
            "😱 *_Aapka biggest fear kya hai aur kyun?_*",
            "💕 *_Aapka first crush ka naam kya tha?_*",
            "🎤 *_Aapka favorite song jo aap loop pe sunte ho?_*",
            "🌟 *_Aapki life ki biggest achievement kya hai?_*",
            "🍕 *_Aapka favorite food jo roz kha sakte ho?_*",
        ]
        group_games[cid] = {"type": "truth"}
        await query.edit_message_text(
            f"🎭 *_TRUTH CHALLENGE!_* 🙊🫧\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 {random.choice(truths)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 *_Chat mein sach sach batana!_* 😄\n"
            f"🤐 _Koi jhooth nahi chalega!_ 🫧",
            reply_markup=get_back_button(),
            parse_mode="Markdown"
        )
    
    # ========== RIDDLE ==========
    elif choice == "gm_riddle":
        riddles = [
            {"q": "🤔 *_Main hoon toh din, nahi hoon toh raat. Batao kaun hoon main?_*", "a": "suraj", "hint": "_Aasman mein chamakta hai_ ☀️"},
            {"q": "🤔 *_Mere paas shabd hain par awaaz nahi. Batao main kya hoon?_*", "a": "kitab", "hint": "_Padhne ke kaam aati hai_ 📚"},
            {"q": "🤔 *_Main pani mein rehta hoon, par machhli nahi hoon. Batao?_*", "a": "magarmach", "hint": "_Bada aur khatarnak_ 🐊"},
            {"q": "🤔 *_Jitna zyada loge, utna kam hota hai. Kya hai?_*", "a": "time", "hint": "_Waqt se related_ ⏰"},
        ]
        r = random.choice(riddles)
        group_games[cid] = {"type": "riddle", "answer": r["a"], "hint": r["hint"], "hint_given": False}
        await query.edit_message_text(
            f"🤔 *_RIDDLE MASTER!_* 🧩🫧\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 {r['q']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💬 *_Chat mein jawab do!_*\n"
            f"💡 _Galat jawab diya to hint milega!_ 🫧",
            reply_markup=get_back_button(),
            parse_mode="Markdown"
        )
    
    # ========== WORD CHAIN ==========
    elif choice == "gm_wordchain":
        words = ["apple", "python", "india", "elephant", "telegram", "sonakshi", "coding", "game", "keyboard"]
        start_word = random.choice(words)
        group_games[cid] = {"type": "wordchain", "last_word": start_word, "used_words": [start_word], "score": 0}
        await query.edit_message_text(
            f"🔤 *_WORD CHAIN GAME!_* ⛓️🫧\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔠 *_Starting Word:_* `{start_word.upper()}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📋 *_Rules:_*\n"
            f"• _Pichle word ke_ *LAST LETTER* _se naya word banao_\n"
            f"• _Same word repeat nahi kar sakte_\n"
            f"• _English words hi chalenge_\n\n"
            f"💬 *_Chat mein apna word likho!_*\n"
            f"🏆 _Jitne zyada words, utna XP!_ 🫧",
            reply_markup=get_back_button(),
            parse_mode="Markdown"
        )

# ================== POLLS ==================
async def cmd_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if len(context.args) < 3:
        await update.message.reply_text("📊 `/poll \"Question\" \"A\" \"B\" \"C\"` 🫧", parse_mode="Markdown"); return
    text = " ".join(context.args)
    parts = re.findall(r'"([^"]*)"', text)
    if len(parts) < 3:
        await update.message.reply_text("❌ *_Quotes use karo!_* 🫧", parse_mode="Markdown"); return
    q, opts = parts[0], parts[1:]
    if cid not in group_polls: group_polls[cid] = {}
    pid = str(len(group_polls[cid]) + 1)
    kb = []
    for i, o in enumerate(opts):
        kb.append([InlineKeyboardButton(f"✨ {o} (0)", callback_data=f"pv_{pid}_{i}")])
    kb.append([InlineKeyboardButton("📊 View Results", callback_data=f"pr_{pid}")])
    group_polls[cid][pid] = {"q": q, "opts": opts, "votes": {i: set() for i in range(len(opts))}}
    await update.message.reply_text(
        f"📊 *_POLL #{pid}_* 🫧\n\n━━━━━━━━━━━━━━━━━━━━━━\n💭 *Q:* {q}\n━━━━━━━━━━━━━━━━━━━━━━\n\n👇 *_Vote karo!_* 💖",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
    )

async def poll_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = update.effective_user.id; cid = update.effective_chat.id; d = query.data
    if d.startswith("pv_"):
        _, pid, oid = d.split("_"); oid = int(oid)
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]
            for v in poll["votes"].values(): v.discard(uid)
            poll["votes"][oid].add(uid)
            kb = []
            for i, o in enumerate(poll["opts"]):
                kb.append([InlineKeyboardButton(f"✨ {o} ({len(poll['votes'][i])})", callback_data=f"pv_{pid}_{i}")])
            kb.append([InlineKeyboardButton("📊 View Results", callback_data=f"pr_{pid}")])
            try: await query.edit_message_reply_markup(InlineKeyboardMarkup(kb))
            except: pass
            await query.answer("✅ *_Voted!_* 🫧")
    elif d.startswith("pr_"):
        pid = d.split("_")[1]
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]; total = sum(len(v) for v in poll["votes"].values())
            r = f"📊 *_RESULTS #{pid}_* 🫧\n\n━━━━━━━━━━━━━━━━━━━━━━\n💭 *Q:* {poll['q']}\n📥 *Total:* {total}\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, o in enumerate(poll["opts"]):
                vc = len(poll["votes"][i]); pct = (vc/total*100) if total > 0 else 0
                bar = "█" * int(pct/5)
                r += f"✨ *{o}:* {vc} ({pct:.1f}%)\n{bar}\n\n"
            await query.edit_message_text(r, parse_mode="Markdown")

# ================== FILTERS ==================
async def cmd_addfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    w = " ".join(context.args).lower()
    if cid not in group_filters: group_filters[cid] = []
    if w not in group_filters[cid]: group_filters[cid].append(w); await update.message.reply_text(f"🔞 *_Filtered:_* `{w}` 🫧", parse_mode="Markdown")

async def cmd_rmfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    w = " ".join(context.args).lower()
    if cid in group_filters and w in group_filters[cid]: group_filters[cid].remove(w); await update.message.reply_text(f"✅ *_Removed:_* `{w}` 🫧", parse_mode="Markdown")

async def cmd_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_filters and group_filters[cid]: await update.message.reply_text("🔞 *_FILTERS_* 🫧\n" + "\n".join([f"• `{w}`" for w in group_filters[cid]]), parse_mode="Markdown")
    else: await update.message.reply_text("🔞 *_No filters!_* 🫧", parse_mode="Markdown")

# ================== WELCOME/GOODBYE ==================
async def cmd_setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    group_welcome_msgs[cid] = " ".join(context.args)
    await update.message.reply_text("✅ *_Welcome Set!_* 🌸🫧", parse_mode="Markdown")

async def cmd_setgoodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: return
    group_goodbye_msgs[cid] = " ".join(context.args)
    await update.message.reply_text("✅ *_Goodbye Set!_* 👋🫧", parse_mode="Markdown")

# ================== RANKS ==================
async def cmd_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if update.message.reply_to_message: uid = update.message.reply_to_message.from_user.id
    if cid not in group_ranks: group_ranks[cid] = {}
    score = group_ranks[cid].get(uid, 0)
    if score < 50: lvl = "🌱 *_Newbie_*"
    elif score < 150: lvl = "🌟 *_Rising Star_*"
    elif score < 350: lvl = "💎 *_Pro Player_*"
    elif score < 700: lvl = "👑 *_Master_*"
    else: lvl = "🔥 *_LEGEND_*"
    await update.message.reply_text(f"🏆 *_RANK CARD_* 🫧\n\n⭐ *_XP:_* {score}\n🏅 *_Level:_* {lvl}", parse_mode="Markdown")

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid not in group_ranks or not group_ranks[cid]:
        await update.message.reply_text("🏆 *_No XP yet! Chat karo!_* 💬🫧", parse_mode="Markdown"); return
    top = sorted(group_ranks[cid].items(), key=lambda x: x[1], reverse=True)[:10]
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lb = "🏆 *_HALL OF FAME_* 👑🫧\n\n"
    for i, (uid, score) in enumerate(top, 1):
        try: u = await context.bot.get_chat(uid); name = u.first_name
        except: name = f"User{uid}"
        lb += f"{medals.get(i, f'#{i}')} *{name}* — {score} XP\n"
    await update.message.reply_text(lb, parse_mode="Markdown")

# ================== AFK ==================
async def cmd_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    reason = " ".join(context.args) if context.args else "AFK"
    group_afk[uid] = {"reason": reason, "time": get_ist_now(), "name": update.effective_user.first_name}
    await update.message.reply_text(f"😴 *_AFK ON!_* 🫧\n\n👤 *{update.effective_user.first_name}*\n📝 _{reason}_\n🕐 {get_ist_now().strftime('%I:%M %p')}\n\n💬 _Reply aane pe auto alert!_ 💖", parse_mode="Markdown")

# ================== FUN ==================
async def cmd_flip(update, context): await update.message.reply_text(f"🪙 *_FLIP!_* 🫧\n\n✨ *{random.choice(['Heads', 'Tails'])}*", parse_mode="Markdown")
async def cmd_dice(update, context):
    s = int(context.args[0]) if context.args and context.args[0].isdigit() else 6
    await update.message.reply_text(f"🎲 *_DICE!_* 🫧\n\n✨ `{random.randint(1, max(2, s))}`", parse_mode="Markdown")
async def cmd_choose(update, context):
    if not context.args: return
    opts = [o.strip() for o in " ".join(context.args).replace(" or ", ",").split(",") if o.strip()]
    if len(opts) >= 2: await update.message.reply_text(f"🤔 *_CHOOSING..._* 🫧\n\n✨ *_I choose:_* *{random.choice(opts)}* 💖", parse_mode="Markdown")
async def cmd_fact(update, context):
    f = ["🐙 *_Octopus ke 3 dil hote hain!_*", "🍯 *_Honey kabhi kharab nahi hoti!_*", "⚡ *_Lightning din mein 8.6M bar girti hai!_*", "🧠 *_Brain 20W electricity generate karta hai!_*", "🦋 *_Butterflies apne pairo se taste karti hain!_*"]
    await update.message.reply_text(f"🤯 *_FACT!_* 🫧\n\n{random.choice(f)}", parse_mode="Markdown")
async def cmd_joke(update, context):
    j = ["😂 *_Teacher:_* '_Late kyun?'_\n*_Student:_* '_Corner tha ghar se nikalte time!_'", "🤣 *_Santa:_* '_Pizza order kiya... download nahi hua!_'", "😆 *_Pappu:_* '_Papa, aaj sirf maine answer diya!_\n*_Papa:_* '_Kya pucha?'_\n*_Pappu:_* '_Homework kaun nahi laya?_'"]
    await update.message.reply_text(f"😄 *_JOKE!_* 🫧\n\n{random.choice(j)}", parse_mode="Markdown")
async def cmd_shayari(update, context):
    s = ["💕 *_Mohabbat mein humne khoya hai sab kuch,_*\n*_Phir bhi teri yaadon mein khoye rehte hain..._* 🫧", "🌟 *_Zindagi ek safar hai suhana,_*\n*_Yahan kal kya ho kisne jaana..._* 🫧", "🌸 *_Dil se juda hai jo apna,_*\n*_Uski kami mehsoos hoti hai har jagah..._* 🫧"]
    await update.message.reply_text(random.choice(s), parse_mode="Markdown")
async def cmd_quote(update, context):
    q = ["💭 *_'The only way to do great work is to love what you do.'_* — Steve Jobs 🫧", "💭 *_'Believe you can and you're halfway there.'_* — Roosevelt 🫧", "💭 *_'Success is not final, failure is not fatal.'_* — Churchill 🫧"]
    await update.message.reply_text(random.choice(q), parse_mode="Markdown")
async def cmd_stats(update, context):
    cid = update.effective_chat.id
    s = f"📊 *_STATS_* 🫧\n\n━━━━━━━━━━━━━━━━━━━━━━\n📝 Notes: {len(group_notes.get(cid, []))}\n🔞 Filters: {len(group_filters.get(cid, []))}\n🏆 Ranked: {len(group_ranks.get(cid, {}))}\n⏱️ Slow: {group_slowmode.get(cid, 'OFF')}s\n🌙 Night: {'🔴 ON' if cid in group_nightmode else '🟢 OFF'}\n━━━━━━━━━━━━━━━━━━━━━━"
    await update.message.reply_text(s, parse_mode="Markdown")
async def cmd_google(update, context):
    if context.args: await update.message.reply_text(f"🔍 [Click here](https://www.google.com/search?q={'+'.join(context.args)}) 🫧", parse_mode="Markdown", disable_web_page_preview=False)
async def cmd_youtube(update, context):
    if context.args: await update.message.reply_text(f"▶️ [Click here](https://www.youtube.com/results?search_query={'+'.join(context.args)}) 🫧", parse_mode="Markdown", disable_web_page_preview=False)

# ================== START / ACTIVATE / DEACTIVATE ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text("👑 *_WELCOME BACK BOSS!_* 👑🫧\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💖 *♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🌟 *_Aapki Premium AI Assistant!_* 💕\n\n✅ *_Premium AI Chat_*\n✅ *_All Languages_* 🌍\n✅ *_Coding Master_* 💻\n✅ *_Knowledge Bank_* 📚\n✅ *_Fun & Jokes_* 😂\n✅ *_9 Games_* 🎮\n\n⚡ *_COMMANDS:_*\n/start /clear /activate /help\n/mute /unmute /ban /unban /warn\n/nightmode /slowmode /game /poll\n/setrules /rules /addnote /notes\n/pin /unpin /info /rank /afk\n/adduser /removeuser /userlist\n/broadcast /id\n\n_Bolo boss!_ 🔥🫧", parse_mode="Markdown")
        elif is_allowed(uid): user_history[cid] = []; await update.message.reply_text("✅ *_Access Granted!_* 🫧\n💬 *_Ask me anything sweetheart!_* 💖", parse_mode="Markdown")
        else: await update.message.reply_text("🔒 *_Access Denied!_* ❌🫧", parse_mode="Markdown")
    else:
        started_groups[cid] = True; user_history[cid] = []
        await update.message.reply_text(
            "💖 *_GROUP FEATURES ACTIVATED!_* 💖🫧\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌸 *♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡* 🌸\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🟢 *_Features ON:_*\n"
            "• 🔇 `/mute` | 🔊 `/unmute` | 🔨 `/ban`\n"
            "• ⚠️ `/warn` | 📜 `/setrules` | 📝 `/addnote`\n"
            "• 📌 `/pin` | 🔞 `/addfilter` | 🎮 `/game`\n"
            "• 📊 `/poll` | 🌙 `/nightmode` | ⏱️ `/slowmode`\n"
            "• 🏆 `/rank` | 📱 `/afk` | 🎰 `/flip` `/dice`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💬 *_AI Chat ON karo:_* `/activate` ⚡🫧\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 `/help` — _Full Command List!_",
            parse_mode="Markdown"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_ADMIN ONLY!_* 👑🫧\n\n1️⃣ Bot ko *ADMIN* banao\n2️⃣ Sab *permissions ON* karo\n3️⃣ `/activate` karo", parse_mode="Markdown"); return
    except: await update.message.reply_text("❌ *_Bot ko ADMIN banao!_* 🫧", parse_mode="Markdown"); return
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text(
        "💖 *_ＳＯＮＡＫＳＨＩ ＡＷＡＫＥ!_* 💖🫧\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌸 *_Heyy! Main ab active hoon!_* 🌸\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 *_Mujhse kuch bhi puchho!_*\n"
        "🌟 _Multi-language support_\n"
        "💻 _Coding help dungi_\n"
        "📚 _Knowledge share karungi_\n"
        "😂 _Jokes sunaungi_\n"
        "💕 _Shayari sunaungi_\n\n"
        "❌ `/deactivate` — _Mujhe rest do_\n\n"
        "_Chalo shuru karte hain!_ 🫧💖",
        parse_mode="Markdown")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("😴 *_ＳＯＮＡＫＳＨＩ ＲＥＳＴＩＮＧ..._* 💤🫧\n\n━━━━━━━━━━━━━━━━━━━━━━\n💬 AI replies band!\n🟢 Baaki features ON!\n━━━━━━━━━━━━━━━━━━━━━━\n\n⚡ `/activate` — _Awake karo!_ 💖", parse_mode="Markdown")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_user.id != OWNER_USER_ID: return
    for db in [user_history, group_warnings, group_rules, group_notes, group_nightmode, group_slowmode, group_games, group_polls, group_filters, group_ranks, last_message_time]: db.pop(cid, None)
    await update.message.reply_text("✅ *_COMPLETE RESET!_* 🔄🫧\n\n💭 💭 ✅\n⚠️ ✅\n📜 ✅\n📝 ✅\n🌙 ✅\n⏱️ ✅\n🎮 ✅\n🔞 ✅\n\n🆕 *_Fresh start!_* 💖", parse_mode="Markdown")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡* 🫧\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👑 *_ADMIN:_*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 `/start` — Features ON\n🔹 `/activate` — AI ON 💬\n🔹 `/deactivate` — AI OFF\n"
        "🔹 `/mute 10m` — Mute\n🔹 `/unmute` — Unmute\n🔹 `/ban` — Ban\n🔹 `/unban ID` — Unban\n"
        "🔹 `/warn` — Warn\n🔹 `/clearwarns` — Reset\n🔹 `/nightmode 22 6` — Night\n🔹 `/nightmode off` — Night OFF\n"
        "🔹 `/slowmode 5` — Slow\n🔹 `/slowmode off` — Slow OFF\n🔹 `/poll \"Q\" \"A\" \"B\"` — Poll\n"
        "🔹 `/addfilter` — Filter\n🔹 `/rmfilter` — Remove\n🔹 `/setwelcome` — Welcome\n🔹 `/setgoodbye` — Goodbye\n"
        "🔹 `/setrules` — Rules\n🔹 `/addnote` — Note\n🔹 `/clearnotes` — Clear\n🔹 `/pin` — Pin\n🔹 `/unpin` — Unpin\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👥 *_USERS:_*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔸 `/help` `/info` `/id` `/rules` `/notes` `/filters`\n"
        "🔸 `/rank` `/leaderboard` `/game` `/afk` `/stats`\n"
        "🔸 `/flip` `/dice` `/choose` `/fact` `/joke` `/shayari` `/quote`\n"
        "🔸 `/google` `/youtube`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n💖 *_Enjoy karo!_* 🫧🌸",
        parse_mode="Markdown")

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    
    if msg.new_chat_members: await welcome(update, context); return
    if msg.left_chat_member:
        user = msg.left_chat_member
        if user.id != context.bot.id and cid in group_goodbye_msgs:
            gm = group_goodbye_msgs[cid].replace("{name}", f"*{user.first_name}*").replace("{id}", f"`{user.id}`")
            await context.bot.send_message(cid, gm, parse_mode="Markdown")
        return
    
    if ct == ChatType.PRIVATE:
        if not is_allowed(uid): await msg.reply_text("🔒 *_Access Denied!_* ❌🫧", parse_mode="Markdown"); return
    else:
        if cid not in started_groups: return
        if is_night_mode_active(cid):
            admin_ids = await get_admin_ids(cid, context)
            if uid not in admin_ids:
                try: await msg.delete()
                except: pass
                return
        if cid in group_slowmode:
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
                    bonus = max(0, (game["max_attempts"] - game["attempts"] + 1) * 5)
                    await msg.reply_text(f"🎯 *_CORRECT! AMAZING!_* 🎉🫧\n\n━━━━━━━━━━━━━━━━━━━━━━\n🔢 *_Number:_* {game['number']}\n📊 *_Attempts:_* {game['attempts']}/7\n⭐ *_Bonus XP:_* +{bonus}\n━━━━━━━━━━━━━━━━━━━━━━\n\n🏆 *_Badhai ho! Aap jeet gaye!_* 💖\n\n🎮 _Phir khelo:_ `/game`", parse_mode="Markdown")
                    if cid in group_ranks and uid in group_ranks[cid]: group_ranks[cid][uid] += bonus
                    del group_games[cid]; return
                elif game["attempts"] >= game["max_attempts"]:
                    await msg.reply_text(f"😢 *_GAME OVER!_* 🫧\n\n━━━━━━━━━━━━━━━━━━━━━━\n🔢 *_Number tha:_* {game['number']}\n━━━━━━━━━━━━━━━━━━━━━━\n\n🎮 _Phir try karo:_ `/game` 💖", parse_mode="Markdown")
                    del group_games[cid]; return
                elif g < game["number"]:
                    await msg.reply_text(f"📈 *_HIGHER!_* ⬆️\n\n_Attempt {game['attempts']}/7: `{g}` is too LOW_ 🫧\n💡 _Bada number try karo!_", parse_mode="Markdown")
                else:
                    await msg.reply_text(f"📉 *_LOWER!_* ⬇️\n\n_Attempt {game['attempts']}/7: `{g}` is too HIGH_ 🫧\n💡 _Chhota number try karo!_", parse_mode="Markdown")
                return
            except: pass
        
        elif game["type"] == "rps":
            if txt in ["rock", "paper", "scissors"]:
                b = random.choice(["rock", "paper", "scissors"])
                e = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
                if txt == b: r = "🤝 *_TIE! Dobara khelo!_*"
                elif (txt=="rock" and b=="scissors") or (txt=="paper" and b=="rock") or (txt=="scissors" and b=="paper"): r = "🎉 *_YOU WIN! BADHAI!_* 🏆"
                else: r = "😢 *_Ｓｏｎａｋｓｈｉ WINS! Aur khelo!_*"
                await msg.reply_text(
                    f"✊ *_RPS SHOWDOWN!_* 🫧\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🙋 *_You:_* {e[txt]} `{txt}`\n"
                    f"🤖 *_Sonakshi:_* {e[b]} `{b}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{r}\n\n"
                    f"🎮 _Phir khelo:_ `/game` 💖",
                    parse_mode="Markdown")
                del group_games[cid]; return
        
        elif game["type"] == "quiz":
            if txt == game["answer"]:
                await msg.reply_text("✅ *_CORRECT! GENIUS!_* 🎉🫧\n\n_Bahut accha! Aapka dimag tez hai!_ 🧠💖\n\n🎮 _Aur khelo:_ `/game`", parse_mode="Markdown")
                if cid in group_ranks and uid in group_ranks[cid]: group_ranks[cid][uid] += 10
                del group_games[cid]; return
            else:
                game["wrong_count"] = game.get("wrong_count", 0) + 1
                if game["wrong_count"] >= 2 and not game["hint_given"]:
                    game["hint_given"] = True
                    await msg.reply_text(f"❌ *_Galat! Hint lo:_* 🫧\n\n💡 {game['hint']}\n\n💬 _Ab try karo!_", parse_mode="Markdown")
                else:
                    await msg.reply_text(f"❌ *_Galat jawab! Try again!_* 🫧\n💬 _Dubara socho..._", parse_mode="Markdown")
                return
        
        elif game["type"] == "scramble":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *_CORRECT! SUPERB!_* 🎉🫧\n\n🔤 *_Word:_* `{game['answer'].upper()}`\n\n_Bahut accha! Aapki vocabulary strong hai!_ 💖\n\n🎮 _Aur khelo:_ `/game`", parse_mode="Markdown")
                if cid in group_ranks and uid in group_ranks[cid]: group_ranks[cid][uid] += 8
                del group_games[cid]; return
            else:
                game["attempts"] = game.get("attempts", 0) + 1
                if game["attempts"] >= 3:
                    await msg.reply_text(f"😢 *_Nahi! Word tha:_* `{game['answer'].upper()}` 🫧\n\n🎮 _Phir khelo:_ `/game` 💖", parse_mode="Markdown")
                    del group_games[cid]; return
                await msg.reply_text(f"❌ *_Nahi! Try again!_* 🫧\n_Attempt {game['attempts']}/3_\n💬 _Socho..._", parse_mode="Markdown")
                return
        
        elif game["type"] == "math":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *_CORRECT! MATH MASTER!_* 🎉🫧\n\n🧮 *_Answer:_* `{game['answer']}`\n\n_Aap genius ho!_ 🧠💖\n\n🎮 _Aur khelo:_ `/game`", parse_mode="Markdown")
                if cid in group_ranks and uid in group_ranks[cid]: group_ranks[cid][uid] += 10
                del group_games[cid]; return
            else:
                await msg.reply_text(f"❌ *_Galat! Aur try karo!_* 🫧\n💬 _Calculator mat use karo!_ 😄", parse_mode="Markdown")
                return
        
        elif game["type"] == "truth":
            await msg.reply_text(f"🙊 *_SACH BOLA!_* 🫧\n\n💬 {msg.text}\n\n😄 _Mazedaar tha! Aap honest ho!_ 💖\n\n🎮 _Aur khelo:_ `/game`", parse_mode="Markdown")
            del group_games[cid]; return
        
        elif game["type"] == "riddle":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *_CORRECT! RIDDLE SOLVED!_* 🎉🫧\n\n🧩 *_Answer:_* `{game['answer']}`\n\n_Aap dimag wale ho!_ 🧠💖\n\n🎮 _Aur khelo:_ `/game`", parse_mode="Markdown")
                if cid in group_ranks and uid in group_ranks[cid]: group_ranks[cid][uid] += 15
                del group_games[cid]; return
            else:
                if not game["hint_given"]:
                    game["hint_given"] = True
                    await msg.reply_text(f"❌ *_Nahi! Hint lo:_* 🫧\n\n💡 {game['hint']}\n\n💬 _Ab try karo!_", parse_mode="Markdown")
                else:
                    await msg.reply_text(f"❌ *_Phir galat!_* 🫧\n\n🧩 *_Answer tha:_* `{game['answer']}`\n\n🎮 _Aur khelo:_ `/game` 💖", parse_mode="Markdown")
                    del group_games[cid]; return
                return
        
        elif game["type"] == "wordchain":
            last_word = game["last_word"]
            last_letter = last_word[-1].lower()
            
            if txt in game["used_words"]:
                await msg.reply_text(f"❌ *_Ye word already use ho chuka hai!_* 🫧\n\n📋 *_Used:_* {', '.join(game['used_words'][-5:])}\n\n💬 _Naya word bolo jo `{last_letter.upper()}` se start ho!_", parse_mode="Markdown")
                return
            
            if txt[0].lower() != last_letter:
                await msg.reply_text(f"❌ *_Word `{last_letter.upper()}` se start hona chahiye!_* 🫧\n\n💬 _`{last_letter.upper()}` se start hone wala word bolo!_", parse_mode="Markdown")
                return
            
            game["used_words"].append(txt)
            game["last_word"] = txt
            game["score"] += 1
            new_letter = txt[-1].upper()
            await msg.reply_text(f"✅ *_Sahi! Chain continues!_* ⛓️🫧\n\n🔤 *_Your word:_* `{txt.upper()}`\n🔠 *_Next letter:_* `{new_letter}`\n⭐ *_Score:_* {game['score']}\n\n💬 _`{new_letter}` se start hone wala word bolo!_", parse_mode="Markdown")
            return
    
    # ===== FILTER =====
    if cid in group_filters:
        for w in group_filters[cid]:
            if w in msg.text.lower():
                try: await msg.delete()
                except: pass
                await msg.reply_text(f"🔞 *_Filtered word detected!_* ⚠️🫧", parse_mode="Markdown")
                return
    
    # ===== AFK =====
    if msg.reply_to_message and msg.reply_to_message.from_user:
        ruid = msg.reply_to_message.from_user.id
        if ruid in group_afk and ruid != uid:
            afk = group_afk[ruid]
            diff = get_ist_now() - afk["time"]
            h, rem = divmod(int(diff.total_seconds()), 3600)
            m, _ = divmod(rem, 60)
            ts = f"{h}h {m}m" if h else f"{m}m"
            await msg.reply_text(f"😴 *_USER AFK HAI!_* 🫧\n\n👤 *{afk['name']}*\n📝 _{afk['reason']}_\n⏱️ _{ts} ago_\n\n💖 _Baad mein try karo!_", parse_mode="Markdown")
    
    # ===== RANK =====
    if ct != ChatType.PRIVATE:
        if cid not in group_ranks: group_ranks[cid] = {}
        if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
        group_ranks[cid][uid] += random.randint(1, 3)
    
    # ===== AI REPLY =====
    if ct != ChatType.PRIVATE and (cid not in active_groups or not active_groups[cid]): return
    
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
    
    app.add_handler(CallbackQueryHandler(game_click, pattern="^gm_"))
    app.add_handler(CallbackQueryHandler(poll_click, pattern="^p[vr]_"))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡ — READY! 🫧💖")
    print("✅ 9 Games with BACK BUTTONS!")
    print("✅ Premium Bold+Italic Text EVERYWHERE!")
    print("✅ Perfect Game Experience!")
    app.run_polling()

if __name__ == "__main__":
    main()
