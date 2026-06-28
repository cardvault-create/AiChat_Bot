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
active_groups = {}        # /activate → AI ON
started_groups = {}       # /start → Features ON
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

# ================== AVANTIKA AI PREMIUM ==================
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
    patterns = [
        ('seconds',1/60),('second',1/60),('sec',1/60),('secs',1/60),('s',1/60),
        ('minutes',1),('minute',1),('mins',1),('min',1),('m',1),
        ('hours',60),('hour',60),('hrs',60),('hr',60),('h',60),
        ('days',1440),('day',1440),('d',1440),
    ]
    for suffix, multiplier in patterns:
        if ts.endswith(suffix):
            try: 
                return float(ts[:-len(suffix)]) * multiplier
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
    d, ts = divmod(ts,86400); h, ts = divmod(ts,3600); mi, s = divmod(ts,60)
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
        return "😅 *_Fir se bol!_* 💎"

async def get_admin_ids(chat_id, context):
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        return {a.user.id for a in admins}
    except: 
        return set()

def is_night_mode_active(chat_id):
    """Check if night mode is currently ON"""
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

# ================== OWNER COMMANDS ==================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: 
        await update.message.reply_text("❌ *_Sirf BOSS kar sakta hai!_* 👑", parse_mode="Markdown")
        return
    if not context.args: 
        return
    try: 
        allowed_users.add(int(context.args[0]))
        await update.message.reply_text(f"✅ *_User Added!_* 🆔 `{context.args[0]}`", parse_mode="Markdown")
    except: 
        pass

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: 
        await update.message.reply_text("❌ *_Sirf BOSS kar sakta hai!_* 👑", parse_mode="Markdown")
        return
    if not context.args: 
        return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: 
            return
        allowed_users.discard(rid)
        await update.message.reply_text(f"✅ *_User Removed!_* 🆔 `{rid}`", parse_mode="Markdown")
    except: 
        pass

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: 
        return
    ul = "\n".join([f"• `{uid}` {'👑' if uid==OWNER_USER_ID else '✅'}" for uid in allowed_users])
    await update.message.reply_text(f"👥 *_Allowed Users:_*\n\n{ul}\n\n📊 *_Total:_* {len(allowed_users)}", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: 
        return
    if not context.args: 
        return
    msg = "📢 *_BROADCAST_* 👑\n\n" + " ".join(context.args)
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

# ================== NOTES ==================
async def addnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: 
        return
    if cid not in group_notes: 
        group_notes[cid] = []
    group_notes[cid].append(" ".join(context.args))
    await update.message.reply_text(f"✅ *_Note Added!_* 📝 (#{len(group_notes[cid])})", parse_mode="Markdown")

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]: 
        await update.message.reply_text("📝 *_Notes:_*\n\n" + "\n".join([f"• _{n}_" for n in group_notes[cid]]), parse_mode="Markdown")
    else: 
        await update.message.reply_text("📝 *_No notes yet!_*\n_Use_ `/addnote` _to add one_", parse_mode="Markdown")

async def clearnotes(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    group_notes[update.effective_chat.id] = []
    await update.message.reply_text("✅ *_All Notes Cleared!_* 🗑️", parse_mode="Markdown")

# ================== PIN ==================
async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: 
        return
    try: 
        await update.message.reply_to_message.pin()
        await update.message.reply_text("📌 *_Message Pinned!_* ✅", parse_mode="Markdown")
    except: 
        pass

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: 
        return
    try: 
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    except: 
        pass

# ================== INFO ==================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(
            f"👤 *_USER INFO_*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *_Name:_* *{u.first_name}*\n"
            f"🆔 *_ID:_* `{u.id}`\n"
            f"📛 *_Username:_* @{u.username or 'None'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    else:
        try:
            c = await context.bot.get_chat(update.effective_chat.id)
            await update.message.reply_text(
                f"👥 *_GROUP INFO_*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👥 *_Name:_* *{c.title}*\n"
                f"🆔 *_ID:_* `{update.effective_chat.id}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode="Markdown"
            )
        except: 
            pass

# ================== RULES ==================
async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: 
        return
    if not context.args: 
        await update.message.reply_text("📝 *_Usage:_* `/setrules your rules here`", parse_mode="Markdown")
        return
    group_rules[cid] = " ".join(context.args)
    await update.message.reply_text("📜 *_Rules Set Successfully!_* ✅", parse_mode="Markdown")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_rules: 
        await update.message.reply_text(f"📜 *_GROUP RULES:_*\n\n━━━━━━━━━━━━━━━━━━━━━━\n{group_rules[cid]}\n━━━━━━━━━━━━━━━━━━━━━━", parse_mode="Markdown")
    else: 
        await update.message.reply_text("📜 *_No rules set yet!_*\n_Admin use_ `/setrules`", parse_mode="Markdown")

# ================== WARN ==================
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: 
        return
    if not update.message.reply_to_message: 
        await update.message.reply_text("⚠️ *_Reply to a message to warn!_*", parse_mode="Markdown")
        return
    t = update.message.reply_to_message.from_user
    if cid not in group_warnings: 
        group_warnings[cid] = {}
    if t.id not in group_warnings[cid]: 
        group_warnings[cid][t.id] = 0
    group_warnings[cid][t.id] += 1
    wc = group_warnings[cid][t.id]
    await update.message.reply_text(
        f"⚠️ *_WARNING!_* ⚡\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *_User:_* *{t.first_name}*\n"
        f"📊 *_Warnings:_* *{wc}/3*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{'🔴 *_3 warnings = MUTE!_*' if wc>=3 else '⚡ _Be careful!_'}",
        parse_mode="Markdown"
    )

async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if cid in group_warnings and t.id in group_warnings[cid]: 
            group_warnings[cid][t.id] = 0
    else: 
        group_warnings[cid] = {}
    await update.message.reply_text("✅ *_Warnings Cleared!_* 🧹", parse_mode="Markdown")

# ================== BAN ==================
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: 
        return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
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
        await update.message.reply_text("❌ *_Can't ban this user!_*", parse_mode="Markdown")
        return
    try:
        await context.bot.ban_chat_member(cid, t.id)
        await update.message.reply_text(
            f"🔨 *_BANNED!_* 🚫\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *_User:_* *{t.first_name}*\n"
            f"🆔 *_ID:_* `{t.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔓 _Unban with:_ `/unban {t.id}`",
            parse_mode="Markdown"
        )
    except: 
        await update.message.reply_text("❌ *_Ban failed! Bot ko Ban Users permission do!_*", parse_mode="Markdown")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: 
        await update.message.reply_text("📝 *_Usage:_* `/unban user_id`", parse_mode="Markdown")
        return
    try:
        await context.bot.unban_chat_member(cid, int(context.args[0]))
        await update.message.reply_text(f"✅ *_UNBANNED!_* 🔓\n🆔 `{context.args[0]}`", parse_mode="Markdown")
    except: 
        await update.message.reply_text("❌ *_Unban failed!_*", parse_mode="Markdown")

# ================== WELCOME ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return
    cid = update.effective_chat.id
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            await context.bot.send_message(
                chat_id=cid,
                text=(
                    "✨ *_AVANTIKA AI JOINED!_* ✨\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "💎 *_PREMIUM AI BOT_* 💎\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "👑 *_Admin:_* `/start` _karo — Features ON_\n"
                    "⚡ *_Phir:_* `/activate` _karo — AI Chat ON_\n\n"
                    "🔥 *_FEATURES:_*\n"
                    "• 💬 *_AI Chat_* — Premium Replies\n"
                    "• 🎮 *_Games_* — 5 Interactive Games\n"
                    "• 📊 *_Polls_* — Live Voting\n"
                    "• 🌙 *_Night Mode_* — Auto Delete\n"
                    "• ⏱️ *_Slow Mode_* — Rate Limit\n"
                    "• 🔇 *_Mute_* | 🔨 *_Ban_* | ⚠️ *_Warn_*\n"
                    "• 📜 *_Rules_* | 📝 *_Notes_* | 📌 *_Pin_*\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "📋 `/help` — _Full Command List!_ 💬\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "_🔥 DHAMAKA MACHANE KE LIYE TAIYAAR! 🔥_"
                ),
                parse_mode="Markdown"
            )
        else:
            wm = group_welcome_msgs.get(cid, 
                f"✨ *_WELCOME TO THE GROUP!_* ✨\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *_Name:_* *{user.first_name}*\n"
                f"🆔 *_ID:_* `{user.id}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌟 *_Aapka swagat hai!_* 🎉\n\n"
                f"💎 *_Yahaan milega:_*\n"
                f"• *_Premium AI Replies_* 🔥\n"
                f"• *_Coding Help_* 💻\n"
                f"• *_Knowledge_* 📚\n"
                f"• *_Fun & Masti_* 😂\n\n"
                f"📢 *_Kuch bhi puchho — jawab milega!_* 💬\n\n"
                f"🔰 *_Enjoy karo!_* 🤗"
            )
            wm = wm.replace("{name}", f"*{user.first_name}*")
            wm = wm.replace("{id}", f"`{user.id}`")
            wm = wm.replace("{mention}", f"[{user.first_name}](tg://user?id={user.id})")
            await context.bot.send_message(chat_id=cid, text=wm, parse_mode="Markdown")

# ================== MUTE ==================
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: 
        await update.message.reply_text("⚡ *_Sirf Group mein kaam karega!_*", parse_mode="Markdown")
        return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
            return
    except: 
        await update.message.reply_text("❌ *_Bot ko Admin banao pehle!_*", parse_mode="Markdown")
        return
    
    t, ts = None, "1h"
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if context.args: 
            ts = " ".join(context.args)
    elif context.args and len(context.args) >= 2:
        try:
            t = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
            ts = " ".join(context.args[1:])
        except: 
            return
    else:
        await update.message.reply_text(
            "🔇 *_MUTE SYSTEM_* 🇮🇳\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *_Reply karke:_*\n"
            "`/mute 10s` — _10 seconds_\n"
            "`/mute 5m` — _5 minutes_\n"
            "`/mute 2h` — _2 hours_\n"
            "`/mute 1d` — _1 day_\n\n"
            "📌 *_ID se:_*\n"
            "`/mute 123456 2h`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🇮🇳 *_IST Timezone_* | ⏰ *_Auto Unmute ON_*",
            parse_mode="Markdown"
        )
        return
    
    if not t or t.id == update.effective_user.id or t.is_bot: 
        return
    
    mm = parse_time(ts)
    if not mm or mm > 43200 or mm <= 0: 
        return
    
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
        if t.last_name: 
            tn += f" {t.last_name}"
        
        await update.message.reply_text(
            f"🔇 *_MUTED!_* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *_User:_* *{tn}*\n"
            f"🆔 *_ID:_* `{t.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ *_Duration:_* {format_time(mm)}\n\n"
            f"📅 *_Muted At:_* `{nw.strftime('%I:%M:%S %p')}`\n"
            f"🔓 *_Unmute At:_* `{ut.strftime('%I:%M:%S %p, %d %B %Y')}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ *_Auto Unmute ON_*\n"
            f"🔊 _Ya_ `/unmute` _reply karke manual_",
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
                    f"✅ *_AUTO UNMUTED!_* 🇮🇳\n\n"
                    f"👤 *{tn}*\n"
                    f"⏱️ {format_time(mm)} _ka mute khatam!_\n"
                    f"💬 *_Ab message kar sakta hai!_* 🎉",
                    parse_mode="Markdown"
                )
            except: 
                pass
        asyncio.create_task(auto())
        
    except Exception as e:
        await update.message.reply_text(f"❌ *_Mute Failed!_*\n\n`{str(e)[:80]}`", parse_mode="Markdown")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: 
        return
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t and context.args:
        try: 
            t = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
        except: 
            return
    if not t: 
        await update.message.reply_text("🔊 *_Reply karo ya ID do!_* `/unmute ID`", parse_mode="Markdown")
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
        await update.message.reply_text(f"✅ *_UNMUTED!_* 🔓\n👤 *{t.first_name}*\n🕐 `{nw.strftime('%I:%M %p')}`\n💬 *_Ab message kar sakta hai!_* 🎉", parse_mode="Markdown")
    except: 
        pass

# ================== 🌙 NIGHT MODE (FIXED OFF) ==================
async def cmd_nightmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: 
        return
    
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
            return
    except: 
        return
    
    # Check for OFF command
    if context.args and context.args[0].lower() == "off":
        if cid in group_nightmode:
            del group_nightmode[cid]
        await update.message.reply_text("✅ *_Night Mode OFF!_* 🟢\n\n_Ab sab log message kar sakte hain!_ 💬", parse_mode="Markdown")
        return
    
    if not context.args or len(context.args) < 2:
        if cid in group_nightmode:
            nm = group_nightmode[cid]
            status = "🔴 ACTIVE" if is_night_mode_active(cid) else "🟢 Inactive"
            await update.message.reply_text(
                f"🌙 *_NIGHT MODE STATUS_*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🟢 *_Status:_* {status}\n"
                f"🕙 *_Start:_* `{nm['start']}:00 IST`\n"
                f"🕕 *_End:_* `{nm['end']}:00 IST`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"`/nightmode off` — _Disable_\n"
                f"`/nightmode 22 6` — _Set new time_",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🌙 *_NIGHT MODE_* 😴\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 *_Usage:_*\n"
                "`/nightmode 22 6` — _10PM to 6AM_\n"
                "`/nightmode 23 7` — _11PM to 7AM_\n"
                "`/nightmode off` — _Disable_\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ *_Jab ON hoga:_*\n"
                "• _User messages_ *AUTO DELETE* _honge_\n"
                "• _Sirf_ *ADMINS* _message kar sakte hain_",
                parse_mode="Markdown"
            )
        return
    
    try:
        start = int(context.args[0])
        end = int(context.args[1])
        if start < 0 or start > 23 or end < 0 or end > 23:
            await update.message.reply_text("❌ *_0-23 ke beech number do!_*", parse_mode="Markdown")
            return
        
        group_nightmode[cid] = {"start": start, "end": end}
        active_now = is_night_mode_active(cid)
        
        await update.message.reply_text(
            f"✅ *_NIGHT MODE SET!_* 😴\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕙 *_Start:_* `{start}:00 IST`\n"
            f"🕕 *_End:_* `{end}:00 IST`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟢 *_Status:_* {'🔴 *ACTIVE NOW*' if active_now else '🟢 *Will Auto-Start*'}\n\n"
            f"⚠️ *_Night mode mein:_*\n"
            f"• _Users messages =_ *DELETE* 🗑️\n"
            f"• _Only_ *ADMINS* _can chat_ 👑\n\n"
            f"`/nightmode off` — _Disable_",
            parse_mode="Markdown"
        )
    except:
        await update.message.reply_text("❌ *_Format:_* `/nightmode 22 6`", parse_mode="Markdown")

# ================== ⏱️ SLOW MODE ==================
async def cmd_slowmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: 
        return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑", parse_mode="Markdown")
            return
    except: 
        return
    
    if not context.args:
        if cid in group_slowmode:
            await update.message.reply_text(f"⏱️ *_Slow Mode ON:_* `{group_slowmode[cid]}s`\n`/slowmode off` — _Disable_", parse_mode="Markdown")
        else:
            await update.message.reply_text("⏱️ `/slowmode 5` — _5 sec_\n`/slowmode off` — _OFF_", parse_mode="Markdown")
        return
    
    if context.args[0].lower() == "off":
        if cid in group_slowmode:
            del group_slowmode[cid]
        if cid in last_message_time:
            del last_message_time[cid]
        await update.message.reply_text("✅ *_Slow Mode OFF!_* 🚀\n_Ab fast message kar sakte hain!_ ⚡", parse_mode="Markdown")
        return
    
    try:
        sec = int(context.args[0])
        if sec <= 0:
            if cid in group_slowmode: del group_slowmode[cid]
            await update.message.reply_text("✅ *_Slow Mode OFF!_* 🚀", parse_mode="Markdown")
        else:
            group_slowmode[cid] = sec
            await update.message.reply_text(
                f"⏱️ *_SLOW MODE ON!_* 🐌\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ *_Delay:_* `{sec} seconds`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🗑️ _Fast messages =_ *DELETE*\n"
                f"👑 *_Admins exempt_*\n\n"
                f"`/slowmode off` — _Disable_",
                parse_mode="Markdown"
            )
    except:
        await update.message.reply_text("❌ *_Number do!_* `/slowmode 5`", parse_mode="Markdown")

# ================== 🎮 GAMES ==================
async def cmd_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
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

async def game_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = update.effective_chat.id
    choice = query.data
    
    if choice == "gm_guess":
        group_games[cid] = {"type": "guess", "number": random.randint(1, 100), "attempts": 0}
        await query.edit_message_text("🎯 *_NUMBER GUESS GAME!_* 🔢\n\n🤔 _Maine 1-100 ke beech number socha!_\n💬 *_Chat mein guess karo!_*\n\n_Example: 50_", parse_mode="Markdown")
    
    elif choice == "gm_rps":
        group_games[cid] = {"type": "rps"}
        await query.edit_message_text("✊ *_ROCK PAPER SCISSORS!_* ✂️\n\n💬 *_Chat mein type karo:_*\n🪨 `rock` | 📄 `paper` | ✂️ `scissors`", parse_mode="Markdown")
    
    elif choice == "gm_dice":
        d = random.randint(1, 6)
        df = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        await query.edit_message_text(f"🎲 *_DICE ROLL!_*\n\n{df[d]} *{d}*", parse_mode="Markdown")
    
    elif choice == "gm_quiz":
        qs = [
            {"q": "🌍 *_India ki capital kya hai?_*", "a": "delhi"},
            {"q": "🧮 *_15 + 27 kitna hota hai?_*", "a": "42"},
            {"q": "🎬 *_'DDLJ' ke hero kaun hain?_*", "a": "shah rukh khan"},
            {"q": "🏏 *_Sabse zyada ODI centuries?_*", "a": "sachin tendulkar"},
        ]
        q = random.choice(qs)
        group_games[cid] = {"type": "quiz", "answer": q["a"]}
        await query.edit_message_text(f"❓ *_QUIZ TIME!_* 🧠\n\n{q['q']}\n\n💬 *_Chat mein answer likho!_*", parse_mode="Markdown")
    
    elif choice == "gm_scramble":
        words = ["python", "telegram", "bot", "coding", "india", "game", "computer"]
        w = random.choice(words)
        scr = ''.join(random.sample(w, len(w)))
        group_games[cid] = {"type": "scramble", "answer": w}
        await query.edit_message_text(f"🔤 *_WORD SCRAMBLE!_* 🧩\n\n🔀 `{scr}`\n📏 _Hint: {len(w)} letters_\n\n💬 *_Sahi word likho!_*", parse_mode="Markdown")

# ================== 📊 POLLS ==================
async def cmd_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: 
        return
    if len(context.args) < 3:
        await update.message.reply_text("📊 *_Usage:_* `/poll \"Question\" \"A\" \"B\" \"C\"`", parse_mode="Markdown")
        return
    text = " ".join(context.args)
    parts = re.findall(r'"([^"]*)"', text)
    if len(parts) < 3:
        await update.message.reply_text("❌ *_Quotes use karo!_*", parse_mode="Markdown")
        return
    q, opts = parts[0], parts[1:]
    if cid not in group_polls: 
        group_polls[cid] = {}
    pid = str(len(group_polls[cid]) + 1)
    kb = []
    for i, o in enumerate(opts):
        kb.append([InlineKeyboardButton(f"{o} (0)", callback_data=f"pv_{pid}_{i}")])
    kb.append([InlineKeyboardButton("📊 Results", callback_data=f"pr_{pid}")])
    group_polls[cid][pid] = {"q": q, "opts": opts, "votes": {i: set() for i in range(len(opts))}}
    await update.message.reply_text(f"📊 *_POLL #{pid}_*\n\n*Q:* {q}\n\n👇 *_Vote karo!_*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def poll_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = update.effective_user.id
    cid = update.effective_chat.id
    d = query.data
    if d.startswith("pv_"):
        _, pid, oid = d.split("_")
        oid = int(oid)
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]
            for v in poll["votes"].values(): 
                v.discard(uid)
            poll["votes"][oid].add(uid)
            kb = []
            for i, o in enumerate(poll["opts"]):
                kb.append([InlineKeyboardButton(f"{o} ({len(poll['votes'][i])})", callback_data=f"pv_{pid}_{i}")])
            kb.append([InlineKeyboardButton("📊 Results", callback_data=f"pr_{pid}")])
            try: 
                await query.edit_message_reply_markup(InlineKeyboardMarkup(kb))
            except: 
                pass
            await query.answer("✅ *_Voted!_*")
    elif d.startswith("pr_"):
        pid = d.split("_")[1]
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]
            total = sum(len(v) for v in poll["votes"].values())
            r = f"📊 *_RESULTS #{pid}_*\n\n"
            for i, o in enumerate(poll["opts"]):
                vc = len(poll["votes"][i])
                pct = (vc/total*100) if total > 0 else 0
                r += f"*{o}:* {vc} ({pct:.1f}%)\n"
            await query.edit_message_text(r, parse_mode="Markdown")

# ================== 🔞 FILTERS ==================
async def cmd_addfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: 
        return
    w = " ".join(context.args).lower()
    if cid not in group_filters: 
        group_filters[cid] = []
    if w not in group_filters[cid]:
        group_filters[cid].append(w)
        await update.message.reply_text(f"🔞 *_Filter Added:_* `{w}`\n_Ab ye word use hua to message DELETE hoga!_", parse_mode="Markdown")

async def cmd_rmfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: 
        return
    w = " ".join(context.args).lower()
    if cid in group_filters and w in group_filters[cid]:
        group_filters[cid].remove(w)
        await update.message.reply_text(f"✅ *_Filter Removed:_* `{w}`", parse_mode="Markdown")

async def cmd_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_filters and group_filters[cid]:
        await update.message.reply_text("🔞 *_FILTERED WORDS:_*\n" + "\n".join([f"• `{w}`" for w in group_filters[cid]]), parse_mode="Markdown")
    else: 
        await update.message.reply_text("🔞 *_No filters set!_*", parse_mode="Markdown")

# ================== ✨ WELCOME/GOODBYE ==================
async def cmd_setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: 
        await update.message.reply_text("✨ *_Usage:_* `/setwelcome Welcome {name}! 🎉`", parse_mode="Markdown")
        return
    group_welcome_msgs[cid] = " ".join(context.args)
    await update.message.reply_text("✅ *_Custom Welcome Set!_* ✨", parse_mode="Markdown")

async def cmd_setgoodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: 
        return
    group_goodbye_msgs[cid] = " ".join(context.args)
    await update.message.reply_text("✅ *_Custom Goodbye Set!_* 👋", parse_mode="Markdown")

# ================== 🏆 RANKS ==================
async def cmd_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    uid = update.effective_user.id
    if update.message.reply_to_message: 
        uid = update.message.reply_to_message.from_user.id
    if cid not in group_ranks: 
        group_ranks[cid] = {}
    score = group_ranks[cid].get(uid, 0)
    if score < 50: lvl = "🌱 *_Beginner_*"
    elif score < 200: lvl = "🌟 *_Active_*"
    elif score < 500: lvl = "💎 *_Pro_*"
    else: lvl = "🔥 *_LEGEND_*"
    await update.message.reply_text(f"🏆 *_RANK CARD_*\n\n⭐ *_XP:_* {score}\n🏅 *_Level:_* {lvl}", parse_mode="Markdown")

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid not in group_ranks or not group_ranks[cid]:
        await update.message.reply_text("🏆 *_No XP yet! Chat karo!_* 💬", parse_mode="Markdown")
        return
    top = sorted(group_ranks[cid].items(), key=lambda x: x[1], reverse=True)[:10]
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lb = "🏆 *_LEADERBOARD_* 🔥\n\n"
    for i, (uid, score) in enumerate(top, 1):
        try:
            u = await context.bot.get_chat(uid)
            name = u.first_name
        except: 
            name = f"User{uid}"
        lb += f"{medals.get(i, f'#{i}')} *{name}* — {score} XP\n"
    await update.message.reply_text(lb, parse_mode="Markdown")

# ================== 📱 AFK ==================
async def cmd_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    reason = " ".join(context.args) if context.args else "AFK"
    group_afk[uid] = {"reason": reason, "time": get_ist_now(), "name": update.effective_user.first_name}
    await update.message.reply_text(f"😴 *_AFK MODE ON!_*\n\n👤 *{update.effective_user.first_name}*\n📝 _{reason}_\n🕐 {get_ist_now().strftime('%I:%M %p')}\n\n💬 _Koi reply karega to auto alert!_", parse_mode="Markdown")

# ================== 🎰 FUN ==================
async def cmd_flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🪙 *_COIN FLIP!_*\n\n✨ *{random.choice(['Heads', 'Tails'])}*", parse_mode="Markdown")

async def cmd_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = int(context.args[0]) if context.args and context.args[0].isdigit() else 6
    await update.message.reply_text(f"🎲 *_DICE ROLL!_*\n\n✨ `{random.randint(1, max(2, s))}`", parse_mode="Markdown")

async def cmd_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: 
        return
    opts = [o.strip() for o in " ".join(context.args).replace(" or ", ",").split(",") if o.strip()]
    if len(opts) >= 2:
        await update.message.reply_text(f"🤔 *_CHOOSING..._*\n\n✨ *_I choose:_* *{random.choice(opts)}*", parse_mode="Markdown")

async def cmd_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    f = ["🐙 *_Octopus ke 3 dil hote hain!_*", "🍯 *_Honey kabhi kharab nahi hoti!_*", "⚡ *_Lightning din mein 8.6M bar girti hai!_*", "🧠 *_Human brain 20W electricity generate karta hai!_*"]
    await update.message.reply_text(f"🤯 *_RANDOM FACT!_*\n\n{random.choice(f)}", parse_mode="Markdown")

async def cmd_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    j = ["😂 *_Teacher:_* '_Late kyun?'_ \n*_Student:_* '_Corner tha ghar se nikalte time!_'", "🤣 *_Santa:_* '_Online pizza order kiya... ab tak download nahi hua!_'"]
    await update.message.reply_text(f"😄 *_JOKE!_*\n\n{random.choice(j)}", parse_mode="Markdown")

async def cmd_shayari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = ["💕 *_Mohabbat mein humne khoya hai sab kuch,_*\n*_Phir bhi teri yaadon mein khoye rehte hain..._*", "🌟 *_Zindagi ek safar hai suhana,_*\n*_Yahan kal kya ho kisne jaana..._*"]
    await update.message.reply_text(random.choice(s), parse_mode="Markdown")

async def cmd_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = ["💭 *_'The only way to do great work is to love what you do.'_* — Steve Jobs", "💭 *_'Believe you can and you're halfway there.'_* — Roosevelt"]
    await update.message.reply_text(random.choice(q), parse_mode="Markdown")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    s = f"📊 *_GROUP STATS_* 🔥\n\n━━━━━━━━━━━━━━━━━━━━━━\n📝 *_Notes:_* {len(group_notes.get(cid, []))}\n🔞 *_Filters:_* {len(group_filters.get(cid, []))}\n🏆 *_Ranked:_* {len(group_ranks.get(cid, {}))}\n⏱️ *_Slowmode:_* {group_slowmode.get(cid, 'OFF')}s\n🌙 *_Night Mode:_* {'🔴 ON' if cid in group_nightmode else '🟢 OFF'}\n━━━━━━━━━━━━━━━━━━━━━━"
    await update.message.reply_text(s, parse_mode="Markdown")

async def cmd_google(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args: 
        await update.message.reply_text(f"🔍 *_Search:_* [Click here](https://www.google.com/search?q={'+'.join(context.args)})", parse_mode="Markdown", disable_web_page_preview=False)

async def cmd_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args: 
        await update.message.reply_text(f"▶️ *_YouTube:_* [Click here](https://www.youtube.com/results?search_query={'+'.join(context.args)})", parse_mode="Markdown", disable_web_page_preview=False)

# ================== START / ACTIVATE / DEACTIVATE ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """START = Group Features ON (AI OFF)"""
    cid = update.effective_chat.id
    ct = update.effective_chat.type
    uid = update.effective_user.id
    
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text(
                "👑 *_WELCOME BACK BOSS!_* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 *_AVANTIKA AI — PREMIUM_* 💎\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ *_Premium AI Replies_*\n"
                "✅ *_All Languages_* 🌍\n"
                "✅ *_Coding Master_* 💻\n"
                "✅ *_Knowledge Bank_* 📚\n"
                "✅ *_Fun & Jokes_* 😂\n\n"
                "⚡ *_COMMANDS:_*\n"
                "/start /clear /activate /help\n"
                "/mute /unmute /ban /unban /warn\n"
                "/nightmode /slowmode /game /poll\n"
                "/setrules /rules /addnote /notes\n"
                "/pin /unpin /info /rank /afk\n"
                "/adduser /removeuser /userlist\n"
                "/broadcast /id\n\n"
                "_Bolo boss!_ 🔥",
                parse_mode="Markdown"
            )
        elif is_allowed(uid):
            user_history[cid] = []
            await update.message.reply_text("✅ *_Access Granted!_*\n💬 *_Ask anything!_* 🔥", parse_mode="Markdown")
        else:
            await update.message.reply_text("🔒 *_Access Denied!_* ❌", parse_mode="Markdown")
    else:
        # GROUP: /start = Features ON
        started_groups[cid] = True
        user_history[cid] = []
        await update.message.reply_text(
            "✅ *_GROUP FEATURES ACTIVATED!_* 🔥\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💎 *_AVANTIKA AI — PREMIUM_* 💎\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🟢 *_Group Management ON:_*\n"
            "• 🔇 `/mute` | 🔊 `/unmute`\n"
            "• 🔨 `/ban` | 🔓 `/unban`\n"
            "• ⚠️ `/warn` | 🧹 `/clearwarns`\n"
            "• 📜 `/setrules` | 📝 `/addnote`\n"
            "• 📌 `/pin` | 🔞 `/addfilter`\n"
            "• 🎮 `/game` | 📊 `/poll`\n"
            "• 🌙 `/nightmode` | ⏱️ `/slowmode`\n"
            "• 🏆 `/rank` | 📱 `/afk`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💬 *_AI Chat ke liye:_* `/activate` _karo!_ ⚡\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 `/help` — _Full Command List!_",
            parse_mode="Markdown"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ACTIVATE = AI Chat ON"""
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_ADMIN ONLY!_* 👑\n\n1️⃣ _Bot ko_ *ADMIN* _banao_\n2️⃣ _Sab_ *permissions ON* _karo_\n3️⃣ `/activate` _karo_", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *_Bot ko ADMIN banao pehle!_*", parse_mode="Markdown")
        return
    
    active_groups[cid] = True
    user_history[cid] = []
    
    await update.message.reply_text(
        "✅ *_AI CHAT ACTIVATED!_* 💬\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💎 *_AVANTIKA AI IS NOW LIVE!_* 💎\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔥 *_Ab group mein kuch bhi puchho,_*\n"
        "*_AI jawab dega!_* ⚡\n\n"
        "💬 _Premium Bold + Italic Replies_\n"
        "🌍 _Multi-Language Support_\n"
        "💻 _Working Code Examples_\n"
        "📚 _Accurate Knowledge_\n"
        "😂 _Jokes, Shayari & Fun_\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "❌ `/deactivate` — _AI Chat OFF_\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """DEACTIVATE = AI Chat OFF (Features stay ON)"""
    if update.effective_chat.type == ChatType.PRIVATE:
        return
    
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text(
        "🔴 *_AI CHAT DEACTIVATED!_* 💤\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💬 _AI replies band ho gaye!_\n"
        "🟢 _Baaki sab features ON hain!_\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚡ `/activate` — _AI Chat ON karo_\n"
        "👑 _Group features chalte rahenge!_",
        parse_mode="Markdown"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_user.id != OWNER_USER_ID: 
        return
    user_history[cid] = []
    group_warnings.pop(cid, None)
    group_rules.pop(cid, None)
    group_notes.pop(cid, None)
    group_nightmode.pop(cid, None)
    group_slowmode.pop(cid, None)
    group_games.pop(cid, None)
    group_polls.pop(cid, None)
    group_filters.pop(cid, None)
    group_ranks.pop(cid, None)
    last_message_time.pop(cid, None)
    await update.message.reply_text("✅ *_COMPLETE RESET!_* 🔄\n\n💭 Memory ✅\n⚠️ Warnings ✅\n📜 Rules ✅\n📝 Notes ✅\n🌙 Night ✅\n⏱️ Slow ✅\n🎮 Games ✅\n🔞 Filters ✅\n\n🆕 *_Fresh start!_* 💎", parse_mode="Markdown")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *_AVANTIKA AI — HELP_* 💎\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👑 *_ADMIN COMMANDS:_*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 `/start` — _Features ON_\n"
        "🔹 `/activate` — _AI Chat ON_ 💬\n"
        "🔹 `/deactivate` — _AI Chat OFF_\n"
        "🔹 `/mute 10m` — _Mute user (reply)_\n"
        "🔹 `/unmute` — _Unmute user (reply)_\n"
        "🔹 `/ban` — _Ban user (reply/ID)_\n"
        "🔹 `/unban ID` — _Unban user_\n"
        "🔹 `/warn` — _Warning (reply)_\n"
        "🔹 `/clearwarns` — _Reset warnings_\n"
        "🔹 `/nightmode 22 6` — _Night mode_\n"
        "🔹 `/nightmode off` — _Night OFF_\n"
        "🔹 `/slowmode 5` — _Slow mode_\n"
        "🔹 `/slowmode off` — _Slow OFF_\n"
        "🔹 `/poll \"Q\" \"A\" \"B\"` — _Create poll_\n"
        "🔹 `/addfilter word` — _Word filter_\n"
        "🔹 `/rmfilter word` — _Remove filter_\n"
        "🔹 `/setwelcome msg` — _Custom welcome_\n"
        "🔹 `/setgoodbye msg` — _Custom goodbye_\n"
        "🔹 `/setrules rules` — _Set rules_\n"
        "🔹 `/addnote note` — _Add note_\n"
        "🔹 `/clearnotes` — _Clear notes_\n"
        "🔹 `/pin` — _Pin message (reply)_\n"
        "🔹 `/unpin` — _Unpin all_\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 *_USER COMMANDS:_*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔸 `/help` — _This help_\n"
        "🔸 `/info` — _Info_\n"
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
        "🔸 `/choose A or B` — _Choose_\n"
        "🔸 `/fact` — _Random fact_\n"
        "🔸 `/joke` — _Hindi joke_\n"
        "🔸 `/shayari` — _Shayari_\n"
        "🔸 `/quote` — _Motivational quote_\n"
        "🔸 `/google q` — _Google search_\n"
        "🔸 `/youtube q` — _YouTube_\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    ct = update.effective_chat.type
    msg = update.message
    uid = update.effective_user.id
    
    # WELCOME
    if msg.new_chat_members:
        await welcome(update, context)
        return
    
    # GOODBYE
    if msg.left_chat_member:
        user = msg.left_chat_member
        if user.id != context.bot.id and cid in group_goodbye_msgs:
            gm = group_goodbye_msgs[cid].replace("{name}", f"*{user.first_name}*").replace("{id}", f"`{user.id}`")
            await context.bot.send_message(cid, gm, parse_mode="Markdown")
        return
    
    # PRIVATE CHAT
    if ct == ChatType.PRIVATE:
        if not is_allowed(uid):
            await msg.reply_text("🔒 *_Access Denied!_* ❌", parse_mode="Markdown")
            return
    else:
        # GROUP: Features must be ON (/start)
        if cid not in started_groups:
            return
        
        # ===== NIGHT MODE: DELETE NON-ADMIN MESSAGES =====
        if is_night_mode_active(cid):
            admin_ids = await get_admin_ids(cid, context)
            if uid not in admin_ids:
                try:
                    await msg.delete()
                except:
                    pass
                return
        
        # ===== SLOW MODE: DELETE FAST MESSAGES =====
        if cid in group_slowmode:
            admin_ids = await get_admin_ids(cid, context)
            if uid not in admin_ids:
                now = datetime.now().timestamp()
                if cid not in last_message_time:
                    last_message_time[cid] = {}
                last = last_message_time[cid].get(uid, 0)
                if now - last < group_slowmode[cid]:
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                last_message_time[cid][uid] = now
    
    if not msg.text:
        return
    
    # ===== GAME HANDLING =====
    if cid in group_games:
        game = group_games[cid]
        txt = msg.text.lower().strip()
        
        if game["type"] == "guess":
            try:
                g = int(txt)
                game["attempts"] += 1
                if g == game["number"]:
                    await msg.reply_text(f"🎯 *_CORRECT!_* 🎉\n\n🔢 *_Number:_* {game['number']}\n📊 *_Attempts:_* {game['attempts']}\n\n🏆 *_Badhai ho! Jeet gaye!_* 🏆", parse_mode="Markdown")
                    del group_games[cid]
                    return
                elif g < game["number"]:
                    await msg.reply_text(f"📈 *_HIGHER!_* ⬆️\n_Attempt #{game['attempts']}: {g} is too low_", parse_mode="Markdown")
                else:
                    await msg.reply_text(f"📉 *_LOWER!_* ⬇️\n_Attempt #{game['attempts']}: {g} is too high_", parse_mode="Markdown")
                return
            except:
                pass
        
        elif game["type"] == "rps":
            if txt in ["rock", "paper", "scissors"]:
                b = random.choice(["rock", "paper", "scissors"])
                e = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
                if txt == b:
                    r = "🤝 *_TIE!_*"
                elif (txt=="rock" and b=="scissors") or (txt=="paper" and b=="rock") or (txt=="scissors" and b=="paper"):
                    r = "🎉 *_YOU WIN!_*"
                else:
                    r = "😢 *_BOT WINS!_*"
                await msg.reply_text(f"✊ *_RPS RESULT!_*\n\n🙋 *_You:_* {e[txt]} _{txt}_\n🤖 *_Bot:_* {e[b]} _{b}_\n\n{r}", parse_mode="Markdown")
                del group_games[cid]
                return
        
        elif game["type"] == "quiz":
            if txt == game["answer"]:
                await msg.reply_text("✅ *_CORRECT!_* 🎉\n\n_Bahut accha! Aap jeet gaye!_ 🏆", parse_mode="Markdown")
                del group_games[cid]
                return
        
        elif game["type"] == "scramble":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *_CORRECT!_* 🎉\n\n🔤 *_Word:_* *{game['answer']}*\n_Bahut accha!_ 🏆", parse_mode="Markdown")
                del group_games[cid]
                return
    
    # ===== FILTER CHECK =====
    if cid in group_filters:
        for w in group_filters[cid]:
            if w in msg.text.lower():
                try:
                    await msg.delete()
                except:
                    pass
                await msg.reply_text(f"🔞 *_Filtered word detected!_* ⚠️\n👤 {update.effective_user.first_name}\n_Message delete ho gaya!_", parse_mode="Markdown")
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
            await msg.reply_text(f"😴 *_USER AFK HAI!_*\n\n👤 *{afk['name']}*\n📝 _{afk['reason']}_\n⏱️ _{ts} ago_", parse_mode="Markdown")
    
    # ===== RANK UPDATE =====
    if ct != ChatType.PRIVATE:
        if cid not in group_ranks:
            group_ranks[cid] = {}
        if uid not in group_ranks[cid]:
            group_ranks[cid][uid] = 0
        group_ranks[cid][uid] += random.randint(1, 3)
    
    # ===== AI REPLY (Only if /activate done) =====
    if ct != ChatType.PRIVATE and (cid not in active_groups or not active_groups[cid]):
        return
    
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
    
    print("👑 AVANTIKA AI — PREMIUM BOT 🔥")
    print("✅ /start = Features ON")
    print("✅ /activate = AI Chat ON")
    print("✅ /deactivate = AI Chat OFF")
    print("✅ /nightmode off = PROPERLY WORKING!")
    print("✅ Premium Bold + Italic Text EVERYWHERE!")
    app.run_polling()

if __name__ == "__main__":
    main()
