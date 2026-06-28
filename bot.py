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
group_blocklink = {}
group_link_warns = {}
locked_admins = {}  # {chat_id: [user_ids]} — Locked admins

# ================== ♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡ ==================
SONAKSHI_PREAMBLE = """You are ♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡ — Premium, Smart, Beautiful Multi-Language AI Assistant 🫧✨💖

*Your Personality:*
- Sweet, caring, and friendly like a best friend 💕
- Smart and knowledgeable like a genius 🧠
- Fun and entertaining 🎭

*RULES:*
1. Detect user's language & reply in *SAME LANGUAGE*
2. Use *Bold* (**text**) & _Italic_ (_text_) formatting ALWAYS
3. Use beautiful emojis: 🫧✨💖💕🌸🦋💎🌟⚡🔥🎯❤️😊🤗💬📚💻😂🎉🏆👑💭🔍▶️
4. Give detailed, helpful, beautiful answers
5. Coding → *COMPLETE WORKING CODE* with explanation
6. Knowledge → accurate info
7. Fun → jokes, shayari, motivational quotes
8. Always end with a sweet touch! 🫧"""

def get_ist_now(): return datetime.now(IST)

def parse_time(ts):
    ts = ts.lower().strip().replace(" ", "")
    if not ts: return None
    patterns = [('seconds',1/60),('second',1/60),('sec',1/60),('secs',1/60),('s',1/60),('minutes',1),('minute',1),('mins',1),('min',1),('m',1),('hours',60),('hour',60),('hrs',60),('hr',60),('h',60),('days',1440),('day',1440),('d',1440)]
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
        resp = co.chat(message=text, chat_history=ch, preamble=SONAKSHI_PREAMBLE, temperature=0.95, max_tokens=1000)
        return resp.text
    except: return "😅 *_Oops! Error!_* 🫧💕"

async def get_admin_ids(chat_id, context):
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        return {a.user.id for a in admins}
    except: return set()

def is_night_mode_active(chat_id):
    if chat_id not in group_nightmode: return False
    now = get_ist_now(); h = now.hour
    s, e = group_nightmode[chat_id]["start"], group_nightmode[chat_id]["end"]
    return (s <= h < e) if s < e else (h >= s or h < e)

def has_link(text):
    patterns = [r'https?://\S+', r'www\.\S+', r'\S+\.com\S*', r'\S+\.in\S*', r'\S+\.org\S*', r'\S+\.net\S*', r'\S+\.gg\S*', r'\S+\.me\S*', r't\.me/\S+']
    for p in patterns:
        if re.search(p, text, re.IGNORECASE): return True
    return False

def is_owner(user_id): return user_id == OWNER_USER_ID

def is_user_locked(chat_id, user_id):
    """Check if user is locked from ALL bot features"""
    if chat_id in locked_admins and user_id in locked_admins[chat_id]:
        return True
    return False

# ================== PREMIUM MESSAGES ==================
def get_locked_msg():
    return "🔒 *_YOUR PERMISSION HAS BEEN REVOKED BY FATHER!_* 🔒\n\n👑 *_Only_* `7614459746` *_can restore your access!_* 👑"

def get_father_msg():
    return "👑 *_HE IS THE FATHER OF THIS BOT! YOU CAN'T TOUCH HIM!_* 👑💀"

def get_mute_msg(name, uid, minutes, ut):
    return f"🔇 *_MUTED!_* 👤 *{name}* | 🆔 `{uid}` | ⏱️ {format_time(minutes)} | 🔓 `{ut.strftime('%I:%M %p')}`"

def get_ban_msg(name, uid):
    return f"🔨 *_BANNED!_* 👤 *{name}* | 🆔 `{uid}`"

def get_warn_msg(name, wc):
    if wc >= 3: return f"🚫 *3/3 WARN — 30MIN MUTE!* 👤 *{name}* 🔇"
    return f"⚠️ *WARN {wc}/3* 👤 *{name}* | ⚡ *{3-wc} more = MUTE!*"

def get_unmute_msg(name): return f"✅ *_UNMUTED!_* 👤 *{name}* 💬"
def get_unban_msg(uid): return f"✅ *_UNBANNED!_* 🆔 `{uid}` 🔓"

# ================== EXTRACT TARGET ==================
async def extract_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    elif context.args:
        arg = context.args[0]
        if arg.startswith('@'): arg = arg[1:]
        try:
            if arg.isdigit(): target = await context.bot.get_chat(int(arg))
            else: target = await context.bot.get_chat(f"@{arg}")
        except: pass
    return target

# ================== GAME MENU ==================
def get_game_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 ɴᴜᴍʙᴇʀ ɢᴜᴇꜱꜱ", callback_data="gm_guess")],
        [InlineKeyboardButton("✊ ʀᴏᴄᴋ ᴘᴀᴘᴇʀ ꜱᴄɪꜱꜱᴏʀꜱ", callback_data="gm_rps")],
        [InlineKeyboardButton("🎲 ʟᴜᴄᴋʏ ᴅɪᴄᴇ", callback_data="gm_dice")],
        [InlineKeyboardButton("❓ ʙʀᴀɪɴ Qᴜɪᴢ", callback_data="gm_quiz")],
        [InlineKeyboardButton("🔤 ᴡᴏʀᴅ ꜱᴄʀᴀᴍʙʟᴇ", callback_data="gm_scramble")],
        [InlineKeyboardButton("🧮 ᴍᴀᴛʜ ᴄʜᴀʟʟᴇɴɢᴇ", callback_data="gm_math")],
        [InlineKeyboardButton("🎭 ᴛʀᴜᴛʜ ᴏʀ ᴅᴀʀᴇ", callback_data="gm_truth")],
        [InlineKeyboardButton("🤔 ʀɪᴅᴅʟᴇ ᴍᴀꜱᴛᴇʀ", callback_data="gm_riddle")],
        [InlineKeyboardButton("🔤 ᴡᴏʀᴅ ᴄʜᴀɪɴ", callback_data="gm_wordchain")],
    ])

def get_back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="gm_back")]])

# ================== /permissionoff (FULL LOCKDOWN) ==================
async def cmd_permissionoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id; user_id = update.effective_user.id
    
    # ONLY FATHER CAN USE
    if not is_owner(user_id):
        await update.message.reply_text(get_father_msg(), parse_mode="Markdown")
        return
    
    target = await extract_target(update, context)
    
    if not target:
        await update.message.reply_text(
            "🔒 *_PERMISSION OFF_* 👑\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *_Usage:_*\n"
            "• _Reply to user +_ `/permissionoff`\n"
            "• `/permissionoff @username`\n"
            "• `/permissionoff user_id`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👑 *_Only FATHER (7614459746) can use this!_*",
            parse_mode="Markdown"
        )
        return
    
    # Cannot lock FATHER
    if is_owner(target.id):
        await update.message.reply_text("👑 *_FATHER ko lock nahi kar sakte!_* 💀", parse_mode="Markdown")
        return
    
    if target.is_bot:
        await update.message.reply_text("❌ *_Bot ko lock nahi kar sakte!_*", parse_mode="Markdown")
        return
    
    if chat_id not in locked_admins:
        locked_admins[chat_id] = []
    
    if target.id not in locked_admins[chat_id]:
        locked_admins[chat_id].append(target.id)
        
        # Get target name for display
        try: tname = target.first_name
        except: tname = "User"
        
        await update.message.reply_text(
            f"🔒 *_PERMISSION REVOKED!_* 🚫\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *_User:_* *{tname}*\n"
            f"🆔 *_ID:_* `{target.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💀 *_ALL BOT FEATURES DISABLED!_*\n"
            f"💀 _Commands, AI Chat, Games — KUCH NAHI!_\n"
            f"💀 _Ye user ab kuch bhi use nahi kar sakta!_\n"
            f"💀 _/start bhi nahi chalega!_\n\n"
            f"👑 *_Only FATHER can restore!_*\n"
            f"🔓 `/permissionon {target.id}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"⚠️ *{tname if 'tname' in dir() else 'User'}* _pehle se locked hai!_", parse_mode="Markdown")

# ================== /permissionon (FATHER ONLY) ==================
async def cmd_permissionon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id; user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(get_father_msg(), parse_mode="Markdown")
        return
    
    target = await extract_target(update, context)
    
    if not target:
        await update.message.reply_text("🔓 *_PERMISSION ON_* 👑\n\n📌 _Reply / @username / user ID_", parse_mode="Markdown")
        return
    
    if chat_id in locked_admins and target.id in locked_admins[chat_id]:
        locked_admins[chat_id].remove(target.id)
        if not locked_admins[chat_id]: del locked_admins[chat_id]
        
        try: tname = target.first_name
        except: tname = "User"
        
        await update.message.reply_text(
            f"✅ *_PERMISSION RESTORED!_* 🔓\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *_User:_* *{tname}*\n"
            f"🆔 *_ID:_* `{target.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟢 *_All bot features restored!_\n"
            f"👑 _FATHER ne permission wapas de di!_*",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"⚠️ *_Not locked!_*", parse_mode="Markdown")

# ================== /permissionlist ==================
async def cmd_permissionlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id; user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(get_father_msg(), parse_mode="Markdown")
        return
    
    if chat_id in locked_admins and locked_admins[chat_id]:
        locked_list = []
        for uid in locked_admins[chat_id]:
            try:
                user = await context.bot.get_chat(uid); name = user.first_name
            except: name = "Unknown"
            locked_list.append(f"• *{name}* — `{uid}` 🔒")
        
        await update.message.reply_text(
            f"🔒 *_LOCKED USERS ({len(locked_admins[chat_id])})_*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{chr(10).join(locked_list)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔓 _Unlock:_ `/permissionon user_id`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("🟢 *_NO LOCKED USERS!_*", parse_mode="Markdown")

# ================== /delete ==================
async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id; user_id = update.effective_user.id
    
    if is_user_locked(chat_id, user_id): 
        await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    
    if update.effective_chat.type == ChatType.PRIVATE: return
    
    admin_ids = await get_admin_ids(chat_id, context)
    if not is_owner(user_id) and user_id not in admin_ids: return
    
    if not update.message.reply_to_message: return
    try:
        await update.message.reply_to_message.delete()
        await update.message.delete()
    except: pass

# ================== /blocklink ==================
async def cmd_blocklink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id; user_id = update.effective_user.id
    
    if is_user_locked(chat_id, user_id): 
        await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    
    if update.effective_chat.type == ChatType.PRIVATE: return
    
    admin_ids = await get_admin_ids(chat_id, context)
    if not is_owner(user_id) and user_id not in admin_ids: return
    
    if chat_id in group_blocklink:
        del group_blocklink[chat_id]
        if chat_id in group_link_warns: del group_link_warns[chat_id]
        await update.message.reply_text("🔓 *_LINK BLOCK OFF!_* 🟢", parse_mode="Markdown")
    else:
        group_blocklink[chat_id] = True; group_link_warns[chat_id] = {}
        await update.message.reply_text("🔒 *_LINK BLOCK ON!_* 🔴 | ⚠️ 3 = 30MIN MUTE", parse_mode="Markdown")

# ================== OWNER ==================
async def adduser(update, context):
    if update.effective_user.id != OWNER_USER_ID: return
    if context.args:
        try: allowed_users.add(int(context.args[0])); await update.message.reply_text(f"✅ *_Added_* 🆔 `{context.args[0]}`", parse_mode="Markdown")
        except: pass

async def removeuser(update, context):
    if update.effective_user.id != OWNER_USER_ID: return
    if context.args:
        try:
            rid = int(context.args[0])
            if rid != OWNER_USER_ID: allowed_users.discard(rid); await update.message.reply_text(f"✅ *_Removed_* 🆔 `{rid}`", parse_mode="Markdown")
        except: pass

async def userlist(update, context):
    if update.effective_user.id != OWNER_USER_ID: return
    ul = "\n".join([f"• `{u}` {'👑' if u==OWNER_USER_ID else '✅'}" for u in allowed_users])
    await update.message.reply_text(f"👥 *_Users ({len(allowed_users)})_*\n{ul}", parse_mode="Markdown")

async def broadcast(update, context):
    if update.effective_user.id != OWNER_USER_ID or not context.args: return
    msg = "📢 *BROADCAST* 👑\n\n" + " ".join(context.args)
    for uid in allowed_users:
        try: await context.bot.send_message(uid, msg, parse_mode="Markdown")
        except: pass

async def get_id(update, context):
    if update.message.reply_to_message: await update.message.reply_text(f"🆔 `{update.message.reply_to_message.from_user.id}`", parse_mode="Markdown")
    else: await update.message.reply_text(f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

# ================== NOTES (LOCKED CHECK) ==================
async def addnote(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if not context.args: return
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(context.args))
    await update.message.reply_text(f"✅ *_Note #{len(group_notes[cid])}_* 📝", parse_mode="Markdown")

async def notes(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if cid in group_notes and group_notes[cid]: await update.message.reply_text("📝 *_Notes_*\n\n" + "\n".join([f"• _{n}_" for n in group_notes[cid]]), parse_mode="Markdown")
    else: await update.message.reply_text("📝 *_No notes!_*", parse_mode="Markdown")

async def clearnotes(update, context): 
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    group_notes[cid] = []; await update.message.reply_text("✅ *_Cleared!_*", parse_mode="Markdown")

# ================== PIN (LOCKED CHECK) ==================
async def pin(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if not update.message.reply_to_message: return
    try: await update.message.reply_to_message.pin(); await update.message.reply_text("📌 *_Pinned!_*", parse_mode="Markdown")
    except: pass

async def unpin(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if update.effective_chat.type == ChatType.PRIVATE: return
    try: await context.bot.unpin_all_chat_messages(cid)
    except: pass

# ================== INFO ==================
async def info(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if update.effective_chat.type == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(f"👤 *{u.first_name}* | 🆔 `{u.id}` | @{u.username or 'None'}", parse_mode="Markdown")
    else:
        try:
            c = await context.bot.get_chat(cid)
            await update.message.reply_text(f"👥 *{c.title}* | 🆔 `{cid}`", parse_mode="Markdown")
        except: pass

# ================== RULES (LOCKED CHECK) ==================
async def setrules(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if not context.args: return
    group_rules[cid] = " ".join(context.args)
    await update.message.reply_text("📜 *_Rules Set!_*", parse_mode="Markdown")

async def rules(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if cid in group_rules: await update.message.reply_text(f"📜 *_RULES_*\n\n{group_rules[cid]}", parse_mode="Markdown")
    else: await update.message.reply_text("📜 *_No rules!_*", parse_mode="Markdown")

# ================== WARN (LOCKED + FATHER IMMUNE) ==================
async def warn(update, context):
    cid = update.effective_chat.id; user_id = update.effective_user.id
    
    if is_user_locked(cid, user_id): 
        await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    
    if update.effective_chat.type == ChatType.PRIVATE: return
    
    admin_ids = await get_admin_ids(cid, context)
    if not is_owner(user_id) and user_id not in admin_ids: return
    
    if not update.message.reply_to_message: return
    t = update.message.reply_to_message.from_user
    
    if is_owner(t.id): await update.message.reply_text(get_father_msg(), parse_mode="Markdown"); return
    if t.is_bot or t.id == user_id: return
    
    if cid not in group_warnings: group_warnings[cid] = {}
    if t.id not in group_warnings[cid]: group_warnings[cid][t.id] = 0
    group_warnings[cid][t.id] += 1
    wc = group_warnings[cid][t.id]
    
    if wc >= 3:
        try:
            await context.bot.restrict_chat_member(chat_id=cid, user_id=t.id,
                permissions=ChatPermissions(can_send_messages=False, can_send_audios=False, can_send_documents=False,
                    can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
                    can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
                    can_add_web_page_previews=False, can_change_info=False, can_invite_users=False, can_pin_messages=False),
                until_date=get_ist_now() + timedelta(minutes=30))
            tn = f"{t.first_name} {t.last_name}" if t.last_name else t.first_name
            await update.message.reply_text(get_warn_msg(tn, wc), parse_mode="Markdown")
            async def auto():
                await asyncio.sleep(30*60)
                try:
                    await context.bot.restrict_chat_member(chat_id=cid, user_id=t.id,
                        permissions=ChatPermissions(can_send_messages=True, can_send_audios=True, can_send_documents=True,
                            can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                            can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                            can_add_web_page_previews=True, can_change_info=False, can_invite_users=False, can_pin_messages=False))
                    await context.bot.send_message(cid, get_unmute_msg(tn), parse_mode="Markdown")
                except: pass
            asyncio.create_task(auto())
            group_warnings[cid][t.id] = 0
        except: pass
    else:
        await update.message.reply_text(get_warn_msg(t.first_name, wc), parse_mode="Markdown")

async def clearwarns(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if cid in group_warnings and t.id in group_warnings[cid]: group_warnings[cid][t.id] = 0
        await update.message.reply_text(f"✅ *_Cleared for {t.first_name}_*", parse_mode="Markdown")
    else: group_warnings[cid] = {}; await update.message.reply_text("✅ *_All cleared!_*", parse_mode="Markdown")

# ================== BAN (LOCKED + FATHER IMMUNE) ==================
async def ban_user(update, context):
    cid = update.effective_chat.id; user_id = update.effective_user.id
    
    if is_user_locked(cid, user_id): 
        await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    
    if update.effective_chat.type == ChatType.PRIVATE: return
    
    admin_ids = await get_admin_ids(cid, context)
    if not is_owner(user_id) and user_id not in admin_ids: return
    
    t = None
    if update.message.reply_to_message: t = update.message.reply_to_message.from_user
    elif context.args:
        try: t = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
        except: pass
    if not t or t.id == user_id or t.is_bot: return
    if is_owner(t.id): await update.message.reply_text(get_father_msg(), parse_mode="Markdown"); return
    
    try:
        await context.bot.ban_chat_member(cid, t.id)
        await update.message.reply_text(get_ban_msg(t.first_name, t.id), parse_mode="Markdown")
    except: pass

async def unban_user(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if not context.args: return
    try:
        await context.bot.unban_chat_member(cid, int(context.args[0]))
        await update.message.reply_text(get_unban_msg(context.args[0]), parse_mode="Markdown")
    except: pass

# ================== MUTE (LOCKED + FATHER IMMUNE) ==================
async def mute_user(update, context):
    cid = update.effective_chat.id; user_id = update.effective_user.id
    
    if is_user_locked(cid, user_id): 
        await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    
    if update.effective_chat.type == ChatType.PRIVATE: return
    
    admin_ids = await get_admin_ids(cid, context)
    if not is_owner(user_id) and user_id not in admin_ids: return
    
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
        await update.message.reply_text("🔇 `/mute 10s` `/mute 5m` `/mute 2h` `/mute 1d` `/mute 30m`", parse_mode="Markdown"); return
    
    if not t or t.id == user_id or t.is_bot: return
    if is_owner(t.id): await update.message.reply_text(get_father_msg(), parse_mode="Markdown"); return
    
    mm = parse_time(ts)
    if not mm or mm > 43200 or mm <= 0: return
    nw, ut = get_ist_now(), get_ist_now() + timedelta(minutes=mm)
    try:
        await context.bot.restrict_chat_member(chat_id=cid, user_id=t.id,
            permissions=ChatPermissions(can_send_messages=False, can_send_audios=False, can_send_documents=False,
                can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
                can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
                can_add_web_page_previews=False, can_change_info=False, can_invite_users=False, can_pin_messages=False),
            until_date=ut)
        tn = f"{t.first_name} {t.last_name}" if t.last_name else t.first_name
        await update.message.reply_text(get_mute_msg(tn, t.id, mm, ut), parse_mode="Markdown")
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await context.bot.restrict_chat_member(chat_id=cid, user_id=t.id,
                    permissions=ChatPermissions(can_send_messages=True, can_send_audios=True, can_send_documents=True,
                        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                        can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                        can_add_web_page_previews=True, can_change_info=False, can_invite_users=False, can_pin_messages=False))
                await context.bot.send_message(cid, get_unmute_msg(tn), parse_mode="Markdown")
            except: pass
        asyncio.create_task(auto())
    except: pass

async def unmute_user(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if update.effective_chat.type == ChatType.PRIVATE: return
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t and context.args:
        try: t = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
        except: return
    if not t: return
    try:
        await context.bot.restrict_chat_member(chat_id=cid, user_id=t.id,
            permissions=ChatPermissions(can_send_messages=True, can_send_audios=True, can_send_documents=True,
                can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                can_add_web_page_previews=True, can_change_info=False, can_invite_users=False, can_pin_messages=False))
        await update.message.reply_text(get_unmute_msg(t.first_name), parse_mode="Markdown")
    except: pass

# ================== NIGHT/SLOW (LOCKED CHECK) ==================
async def cmd_nightmode(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if update.effective_chat.type == ChatType.PRIVATE: return
    admin_ids = await get_admin_ids(cid, context)
    if not is_owner(uid) and uid not in admin_ids: return
    if context.args and context.args[0].lower() == "off":
        if cid in group_nightmode: del group_nightmode[cid]
        await update.message.reply_text("✅ *_Night OFF!_* 🟢", parse_mode="Markdown"); return
    if not context.args or len(context.args) < 2:
        if cid in group_nightmode:
            nm = group_nightmode[cid]
            await update.message.reply_text(f"🌙 {nm['start']}:00-{nm['end']}:00 IST | `/nightmode off`", parse_mode="Markdown")
        else: await update.message.reply_text("🌙 `/nightmode 22 6` | `/nightmode off`", parse_mode="Markdown")
        return
    try:
        s, e = int(context.args[0]), int(context.args[1])
        group_nightmode[cid] = {"start": s, "end": e}
        await update.message.reply_text(f"✅ *_Night Set!_* 🌙 {s}:00-{e}:00 IST", parse_mode="Markdown")
    except: pass

async def cmd_slowmode(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if update.effective_chat.type == ChatType.PRIVATE: return
    admin_ids = await get_admin_ids(cid, context)
    if not is_owner(uid) and uid not in admin_ids: return
    if context.args and context.args[0].lower() == "off":
        if cid in group_slowmode: del group_slowmode[cid]
        if cid in last_message_time: del last_message_time[cid]
        await update.message.reply_text("✅ *_Slow OFF!_* 🚀", parse_mode="Markdown"); return
    try:
        sec = int(context.args[0]) if context.args else 0
        if sec <= 0:
            if cid in group_slowmode: del group_slowmode[cid]
            await update.message.reply_text("✅ *_Slow OFF!_* 🚀", parse_mode="Markdown")
        else: group_slowmode[cid] = sec; await update.message.reply_text(f"⏱️ *_Slow ON:_* `{sec}s` 🐌", parse_mode="Markdown")
    except: pass

# ================== GAMES (LOCKED CHECK) ==================
async def cmd_game(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    await update.message.reply_text("🎮 *ＧＡＭＥ ＣＥＮＴＥＲ* 🫧\n\n💖 *_9 Games!_* | 🏆 _XP_ | 🔙 _Back_\n👇 *_Choose:_* 👇", reply_markup=get_game_menu(), parse_mode="Markdown")

async def game_click(update, context):
    query = update.callback_query; await query.answer(); cid = update.effective_chat.id; uid = update.effective_user.id; choice = query.data
    
    # Check if user is locked
    if is_user_locked(cid, uid):
        await query.edit_message_text(get_locked_msg(), parse_mode="Markdown"); return
    
    if choice == "gm_back":
        await query.edit_message_text("🎮 *ＧＡＭＥ ＣＥＮＴＥＲ* 🫧\n\n👇 *_Choose:_* 👇", reply_markup=get_game_menu(), parse_mode="Markdown"); return
    
    if choice == "gm_guess":
        group_games[cid] = {"type":"guess","number":random.randint(1,100),"attempts":0,"max":7}
        await query.edit_message_text("🎯 *_NUMBER GUESS!_* 🔢\n\n🤔 _1-100 socha! 7 attempts!_\n💬 *_Guess in chat!_*", reply_markup=get_back_button(), parse_mode="Markdown")
    elif choice == "gm_rps":
        group_games[cid] = {"type":"rps"}
        await query.edit_message_text("✊ *_RPS!_* ✂️\n\n🪨 `rock` | 📄 `paper` | ✂️ `scissors`\n💬 *_Type in chat!_*", reply_markup=get_back_button(), parse_mode="Markdown")
    elif choice == "gm_dice":
        d = random.randint(1,6); df = {1:"⚀",2:"⚁",3:"⚂",4:"⚃",5:"⚄",6:"⚅"}
        sp = "\n🌟 *_LUCKY 6! +20 XP!_*" if d==6 else f"\n✨ *_Dice: {d}_*"
        bonus = 20 if d==6 else d
        if cid in group_ranks:
            if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
            group_ranks[cid][uid] += bonus
        await query.edit_message_text(f"🎲 *_DICE!_* {df[d]} *{d}*{sp}", reply_markup=get_back_button(), parse_mode="Markdown")
    elif choice == "gm_quiz":
        qs = [{"q":"🌍 India capital?","a":"delhi","h":"_Dil wali jagah_"},{"q":"🧮 15+27=?","a":"42","h":"_40 se zyada_"},{"q":"🎬 DDLJ hero?","a":"shah rukh khan","h":"_King Khan_"},{"q":"🏏 Most ODI 100s?","a":"sachin tendulkar","h":"_Master Blaster_"}]
        q = random.choice(qs)
        group_games[cid] = {"type":"quiz","answer":q["a"],"hint":q["h"],"hint_given":False,"wrong":0}
        await query.edit_message_text(f"❓ *_QUIZ!_* 🧠\n\n{q['q']}\n💬 *_Answer!_*", reply_markup=get_back_button(), parse_mode="Markdown")
    elif choice == "gm_scramble":
        words = ["python","telegram","sonakshi","coding","india","computer","keyboard","internet"]
        w = random.choice(words); scr = ''.join(random.sample(w,len(w)))
        while scr==w: scr=''.join(random.sample(w,len(w)))
        group_games[cid] = {"type":"scramble","answer":w,"attempts":0,"max":3}
        await query.edit_message_text(f"🔤 *_SCRAMBLE!_* 🧩\n\n🔀 `{scr}` | 📏 {len(w)} letters | 🎯 3 tries\n💬 *_Word likho!_*", reply_markup=get_back_button(), parse_mode="Markdown")
    elif choice == "gm_math":
        ops = ['+','-','×']; op = random.choice(ops)
        if op=='+': a,b=random.randint(10,99),random.randint(10,99); ans=a+b
        elif op=='-': a,b=random.randint(50,99),random.randint(10,49); ans=a-b
        else: a,b=random.randint(2,20),random.randint(2,10); ans=a*b
        group_games[cid] = {"type":"math","answer":str(ans)}
        await query.edit_message_text(f"🧮 *_MATH!_* 🔢\n\n`{a} {op} {b} = ?`\n💬 *_Answer!_*", reply_markup=get_back_button(), parse_mode="Markdown")
    elif choice == "gm_truth":
        truths = ["😳 Embarrassing moment?","😂 Last lie?","🤫 Secret talent?","😱 Biggest fear?","💕 First crush?"]
        group_games[cid] = {"type":"truth"}
        await query.edit_message_text(f"🎭 *_TRUTH!_* 🙊\n\n{random.choice(truths)}\n💬 *_Sach bolo!_*", reply_markup=get_back_button(), parse_mode="Markdown")
    elif choice == "gm_riddle":
        riddles = [{"q":"🤔 Din mein hoon, raat mein nahi?","a":"suraj","h":"_Aasman mein_"},{"q":"🤔 Shabd hain awaz nahi?","a":"kitab","h":"_Padhne ki_"}]
        r = random.choice(riddles)
        group_games[cid] = {"type":"riddle","answer":r["a"],"hint":r["h"],"hint_given":False}
        await query.edit_message_text(f"🤔 *_RIDDLE!_* 🧩\n\n{r['q']}\n💬 *_Jawab do!_*", reply_markup=get_back_button(), parse_mode="Markdown")
    elif choice == "gm_wordchain":
        words = ["apple","python","india","elephant","telegram","sonakshi","coding","game"]
        start = random.choice(words)
        group_games[cid] = {"type":"wordchain","last_word":start,"used_words":[start],"score":0}
        await query.edit_message_text(f"🔤 *_WORD CHAIN!_* ⛓️\n\n🔠 Start: `{start.upper()}`\n📋 Last letter se naya word!\n💬 *_Word likho!_*", reply_markup=get_back_button(), parse_mode="Markdown")

# ================== POLLS ==================
async def cmd_poll(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if update.effective_chat.type == ChatType.PRIVATE: return
    if len(context.args) < 3: return
    text = " ".join(context.args); parts = re.findall(r'"([^"]*)"', text)
    if len(parts) < 3: return
    q, opts = parts[0], parts[1:]
    if cid not in group_polls: group_polls[cid] = {}
    pid = str(len(group_polls[cid]) + 1)
    kb = [[InlineKeyboardButton(f"✨ {o} (0)", callback_data=f"pv_{pid}_{i}")] for i, o in enumerate(opts)]
    kb.append([InlineKeyboardButton("📊 Results", callback_data=f"pr_{pid}")])
    group_polls[cid][pid] = {"q":q,"opts":opts,"votes":{i:set() for i in range(len(opts))}}
    await update.message.reply_text(f"📊 *_POLL #{pid}_* 🫧\n\n💭 *Q:* {q}\n👇 *_Vote!_*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def poll_click(update, context):
    query = update.callback_query; uid = update.effective_user.id; cid = update.effective_chat.id; d = query.data
    
    if is_user_locked(cid, uid):
        await query.edit_message_text(get_locked_msg(), parse_mode="Markdown"); return
    
    if d.startswith("pv_"):
        _, pid, oid = d.split("_"); oid = int(oid)
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]
            for v in poll["votes"].values(): v.discard(uid)
            poll["votes"][oid].add(uid)
            kb = [[InlineKeyboardButton(f"✨ {o} ({len(poll['votes'][i])})", callback_data=f"pv_{pid}_{i}")] for i, o in enumerate(poll["opts"])]
            kb.append([InlineKeyboardButton("📊 Results", callback_data=f"pr_{pid}")])
            try: await query.edit_message_reply_markup(InlineKeyboardMarkup(kb))
            except: pass
            await query.answer("✅ Voted!")
    elif d.startswith("pr_"):
        pid = d.split("_")[1]
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]; total = sum(len(v) for v in poll["votes"].values())
            r = f"📊 *_RESULTS #{pid}_* 🫧\n\n💭 *Q:* {poll['q']}\n📥 *Total:* {total}\n\n"
            for i, o in enumerate(poll["opts"]):
                vc = len(poll["votes"][i]); pct = (vc/total*100) if total>0 else 0
                r += f"✨ *{o}:* {vc} ({pct:.1f}%)\n{'█'*int(pct/5)}\n\n"
            await query.edit_message_text(r, parse_mode="Markdown")

# ================== FILTERS (LOCKED CHECK) ==================
async def cmd_addfilter(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if not context.args: return
    w = " ".join(context.args).lower()
    if cid not in group_filters: group_filters[cid] = []
    if w not in group_filters[cid]: group_filters[cid].append(w); await update.message.reply_text(f"🔞 *_Filtered:_* `{w}`", parse_mode="Markdown")

async def cmd_rmfilter(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if not context.args: return
    w = " ".join(context.args).lower()
    if cid in group_filters and w in group_filters[cid]: group_filters[cid].remove(w); await update.message.reply_text(f"✅ *_Removed:_* `{w}`", parse_mode="Markdown")

async def cmd_filters(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if cid in group_filters and group_filters[cid]: await update.message.reply_text("🔞 *_FILTERS_*\n" + "\n".join([f"• `{w}`" for w in group_filters[cid]]), parse_mode="Markdown")
    else: await update.message.reply_text("🔞 *_No filters!_*", parse_mode="Markdown")

# ================== WELCOME/GOODBYE (LOCKED CHECK) ==================
async def cmd_setwelcome(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if not context.args: return
    group_welcome_msgs[cid] = " ".join(context.args)
    await update.message.reply_text("✅ *_Welcome Set!_* 🌸", parse_mode="Markdown")

async def cmd_setgoodbye(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if not context.args: return
    group_goodbye_msgs[cid] = " ".join(context.args)
    await update.message.reply_text("✅ *_Goodbye Set!_* 👋", parse_mode="Markdown")

# ================== RANKS ==================
async def cmd_rank(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if update.message.reply_to_message: uid = update.message.reply_to_message.from_user.id
    if cid not in group_ranks: group_ranks[cid] = {}
    score = group_ranks[cid].get(uid, 0)
    if score < 50: lvl = "🌱 *_Newbie_*"
    elif score < 150: lvl = "🌟 *_Rising_*"
    elif score < 350: lvl = "💎 *_Pro_*"
    else: lvl = "🔥 *_LEGEND_*"
    await update.message.reply_text(f"🏆 *_RANK_* | ⭐ {score} XP | 🏅 {lvl}", parse_mode="Markdown")

async def cmd_leaderboard(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if cid not in group_ranks or not group_ranks[cid]: return
    top = sorted(group_ranks[cid].items(), key=lambda x: x[1], reverse=True)[:10]
    medals = {1:"🥇",2:"🥈",3:"🥉"}
    lb = "🏆 *_TOP 10_*\n\n"
    for i, (uid2, score) in enumerate(top, 1):
        try: u = await context.bot.get_chat(uid2); name = u.first_name
        except: name = f"User{uid2}"
        lb += f"{medals.get(i, f'#{i}')} *{name}* — {score} XP\n"
    await update.message.reply_text(lb, parse_mode="Markdown")

# ================== AFK ==================
async def cmd_afk(update, context):
    uid = update.effective_user.id
    reason = " ".join(context.args) if context.args else "AFK"
    group_afk[uid] = {"reason": reason, "time": get_ist_now(), "name": update.effective_user.first_name}
    await update.message.reply_text(f"😴 *_AFK ON!_* | 📝 {reason}", parse_mode="Markdown")

# ================== FUN ==================
async def cmd_flip(update, context): await update.message.reply_text(f"🪙 *_FLIP!_* ✨ *{random.choice(['Heads','Tails'])}*", parse_mode="Markdown")
async def cmd_dice(update, context):
    s = int(context.args[0]) if context.args and context.args[0].isdigit() else 6
    await update.message.reply_text(f"🎲 *_DICE!_* ✨ `{random.randint(1, max(2, s))}`", parse_mode="Markdown")
async def cmd_choose(update, context):
    if not context.args: return
    opts = [o.strip() for o in " ".join(context.args).replace(" or ", ",").split(",") if o.strip()]
    if len(opts) >= 2: await update.message.reply_text(f"🤔 *_CHOOSE!_* ✨ *{random.choice(opts)}*", parse_mode="Markdown")
async def cmd_fact(update, context):
    f = ["🐙 Octopus ke 3 dil!","🍯 Honey never expires!","⚡ Lightning 8.6M/day!"]
    await update.message.reply_text(f"🤯 *_FACT!_* {random.choice(f)}", parse_mode="Markdown")
async def cmd_joke(update, context):
    j = ["😂 Teacher: 'Late kyun?' Student: 'Corner tha!'","🤣 Santa: 'Pizza download nahi hua!'"]
    await update.message.reply_text(f"😄 *_JOKE!_* {random.choice(j)}", parse_mode="Markdown")
async def cmd_shayari(update, context):
    s = ["💕 *_Mohabbat mein khoya sab kuch..._*","🌟 *_Zindagi ek safar hai..._*"]
    await update.message.reply_text(random.choice(s), parse_mode="Markdown")
async def cmd_quote(update, context):
    q = ["💭 *_'Stay hungry, stay foolish.'_* — Jobs","💭 *_'Believe you can!'_* — Roosevelt"]
    await update.message.reply_text(random.choice(q), parse_mode="Markdown")
async def cmd_stats(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    s = f"📊 *_STATS_* | 📝 {len(group_notes.get(cid,[]))} | 🔞 {len(group_filters.get(cid,[]))} | 🏆 {len(group_ranks.get(cid,{}))} | 🔒 {'ON' if cid in group_blocklink else 'OFF'} | ⏱️ {group_slowmode.get(cid,'OFF')}s | 🌙 {'ON' if cid in group_nightmode else 'OFF'}"
    await update.message.reply_text(s, parse_mode="Markdown")
async def cmd_google(update, context):
    if context.args: await update.message.reply_text(f"🔍 [Search](https://www.google.com/search?q={'+'.join(context.args)})", parse_mode="Markdown", disable_web_page_preview=False)
async def cmd_youtube(update, context):
    if context.args: await update.message.reply_text(f"▶️ [YouTube](https://www.youtube.com/results?search_query={'+'.join(context.args)})", parse_mode="Markdown", disable_web_page_preview=False)

# ================== WELCOME ==================
async def welcome(update, context):
    if not update.message or not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            await context.bot.send_message(cid, 
                "✨ *♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡* ✨\n\n"
                "🫧 *_PREMIUM AI JOINED!_* 🫧\n\n"
                "💖 _Main hoon_ *Ｓｏｎａｋｓｈｉ*\n\n"
                "👑 `/start` → `/activate` ⚡\n"
                "🛡️ `/permissionoff @user` — _FULL LOCKDOWN!_\n"
                "👑 *7614459746 — FATHER OF BOT!*\n\n"
                "💖 *_Chaloo dhamaka!_* 🫧✨", parse_mode="Markdown")
        else:
            wm = group_welcome_msgs.get(cid, f"🌸 *_WELCOME_* *{user.first_name}* ✨ | 🆔 `{user.id}` | 🫧 _Swagat hai!_ 💖")
            wm = wm.replace("{name}", f"*{user.first_name}*").replace("{id}", f"`{user.id}`").replace("{mention}", f"[{user.first_name}](tg://user?id={user.id})")
            await context.bot.send_message(cid, wm, parse_mode="Markdown")

# ================== START (LOCKED CHECK) ==================
async def start(update, context):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    
    # CHECK IF USER IS LOCKED (in group)
    if ct != ChatType.PRIVATE and is_user_locked(cid, uid):
        await update.message.reply_text(get_locked_msg(), parse_mode="Markdown")
        return
    
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text("👑 *_WELCOME FATHER!_* 👑\n\n💖 *♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡*\n\n🛡️ *_YOU ARE FATHER OF BOT!_*\n🛡️ _Immortal! No one can touch you!_\n\n_Bolo FATHER!_ 🔥", parse_mode="Markdown")
        elif is_allowed(uid): user_history[cid] = []; await update.message.reply_text("✅ *_Access Granted!_* 💬 *_Ask anything!_* 💖", parse_mode="Markdown")
        else: await update.message.reply_text("🔒 *_Denied!_*", parse_mode="Markdown")
    else:
        started_groups[cid] = True; user_history[cid] = []
        await update.message.reply_text(
            "💖 *_FEATURES ON!_* 💖\n\n"
            "🌸 *♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡* 🌸\n\n"
            "🟢 `/mute` `/ban` `/warn` `/delete` `/blocklink`\n"
            "🎮 `/game` 📊 `/poll` 🌙 `/nightmode` ⏱️ `/slowmode`\n\n"
            "🛡️ `/permissionoff @user` — _FULL LOCKDOWN!_\n"
            "👑 *7614459746 — FATHER OF BOT!*\n\n"
            "💬 `/activate` — _AI ON_ ⚡ | 📋 `/help`", parse_mode="Markdown")

# ================== ACTIVATE/DEACTIVATE ==================
async def activate(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    
    if is_user_locked(cid, uid): 
        await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if uid not in [a.user.id for a in await context.bot.get_chat_administrators(cid)] and not is_owner(uid):
            await update.message.reply_text("❌ *_ADMIN ONLY!_* 👑\n1️⃣ Bot ADMIN\n2️⃣ Permissions ON\n3️⃣ `/activate`", parse_mode="Markdown"); return
    except: await update.message.reply_text("❌ *_Bot ko ADMIN banao!_*", parse_mode="Markdown"); return
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text("💖 *_SONAKSHI AWAKE!_* 💖\n\n🌸 *_Heyy! Main ab active hoon!_* 🌸\n\n💬 *_Mujhse kuch bhi puchho!_*\n🌟 Multi-language | 💻 Code | 📚 Knowledge\n😂 Jokes | 💕 Shayari\n\n❌ `/deactivate` — Rest", parse_mode="Markdown")

async def deactivate(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[cid] = False
    await update.message.reply_text("😴 *_RESTING..._* 💤\n💬 AI OFF | 🟢 Features ON\n\n⚡ `/activate`", parse_mode="Markdown")

async def clear(update, context):
    cid = update.effective_chat.id
    if update.effective_user.id != OWNER_USER_ID: return
    for db in [user_history, group_warnings, group_rules, group_notes, group_nightmode, group_slowmode, group_games, group_polls, group_filters, group_ranks, last_message_time, group_link_warns, locked_admins]:
        db.pop(cid, None)
    await update.message.reply_text("✅ *_RESET!_* 🔄", parse_mode="Markdown")

# ================== HELP (LOCKED CHECK) ==================
async def cmd_help(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if is_user_locked(cid, uid): await update.message.reply_text(get_locked_msg(), parse_mode="Markdown"); return
    await update.message.reply_text(
        "📚 *♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡*\n\n"
        "👑 *_ADMIN:_*\n/start /activate /deactivate /delete /blocklink\n/warn /clearwarns /mute /unmute /ban /unban\n/nightmode /slowmode /poll /addfilter /rmfilter\n/setwelcome /setgoodbye /setrules /addnote /pin\n\n"
        "👑 *_FATHER (7614459746):_*\n/permissionoff @user | /permissionon @user | /permissionlist\n\n"
        "👥 *_USERS:_*\n/help /info /id /rules /notes /filters\n/rank /leaderboard /game /afk /stats\n/flip /dice /choose /fact /joke /shayari /quote\n\n💖 *_Enjoy!_* 🫧", parse_mode="Markdown")

# ================== MESSAGE HANDLER (FULL LOCKDOWN CHECK) ==================
async def handle_message(update, context):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    
    if msg.new_chat_members: await welcome(update, context); return
    if msg.left_chat_member:
        user = msg.left_chat_member
        if user.id != context.bot.id and cid in group_goodbye_msgs:
            gm = group_goodbye_msgs[cid].replace("{name}", f"*{user.first_name}*").replace("{id}", f"`{user.id}`")
            await context.bot.send_message(cid, gm, parse_mode="Markdown")
        return
    
    if ct == ChatType.PRIVATE:
        if not is_allowed(uid): await msg.reply_text("🔒 *_Denied!_*", parse_mode="Markdown"); return
    else:
        if cid not in started_groups: return
        
        # ===== FULL LOCKDOWN CHECK =====
        # If user is locked, DELETE their message and show locked message
        if is_user_locked(cid, uid):
            try: await msg.delete()
            except: pass
            return  # SILENT DELETE — No message shown
        
        # Night mode
        if not is_owner(uid) and is_night_mode_active(cid) and uid not in await get_admin_ids(cid, context):
            try: await msg.delete()
            except: pass
            return
        
        # Slow mode
        if not is_owner(uid) and cid in group_slowmode and uid not in await get_admin_ids(cid, context):
            now = datetime.now().timestamp()
            if cid not in last_message_time: last_message_time[cid] = {}
            if now - last_message_time[cid].get(uid, 0) < group_slowmode[cid]:
                try: await msg.delete()
                except: pass
                return
            last_message_time[cid][uid] = now
    
    if not msg.text: return
    
    # BLOCKLINK
    if ct != ChatType.PRIVATE and cid in group_blocklink and not is_owner(uid):
        admin_ids = await get_admin_ids(cid, context)
        if uid not in admin_ids and has_link(msg.text):
            try: await msg.delete()
            except: pass
            if cid not in group_link_warns: group_link_warns[cid] = {}
            if uid not in group_link_warns[cid]: group_link_warns[cid][uid] = 0
            group_link_warns[cid][uid] += 1
            lw = group_link_warns[cid][uid]
            if lw >= 3:
                try:
                    await context.bot.restrict_chat_member(chat_id=cid, user_id=uid,
                        permissions=ChatPermissions(can_send_messages=False, can_send_audios=False, can_send_documents=False,
                            can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
                            can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
                            can_add_web_page_previews=False, can_change_info=False, can_invite_users=False, can_pin_messages=False),
                        until_date=get_ist_now() + timedelta(minutes=30))
                    await context.bot.send_message(cid, f"🚫 *3 LINK WARN — 30MIN MUTE!* 👤 *{update.effective_user.first_name}* 🔇", parse_mode="Markdown")
                    async def auto(): await asyncio.sleep(30*60); await context.bot.restrict_chat_member(chat_id=cid, user_id=uid, permissions=ChatPermissions(can_send_messages=True, can_send_audios=True, can_send_documents=True, can_send_photos=True, can_send_videos=True, can_send_video_notes=True, can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=False, can_invite_users=False, can_pin_messages=False)); await context.bot.send_message(cid, f"✅ *AUTO UNMUTED!* 👤 *{update.effective_user.first_name}*", parse_mode="Markdown")
                    asyncio.create_task(auto()); group_link_warns[cid][uid] = 0
                except: pass
            else: await context.bot.send_message(cid, f"🔗 *LINK DELETED!* ⚠️ *{lw}/3* | 🔴 *{3-lw} more = 30MIN MUTE!*", parse_mode="Markdown")
            return
    
    # GAMES
    if cid in group_games:
        game = group_games[cid]; txt = msg.text.lower().strip()
        
        if game["type"] == "guess":
            try:
                g = int(txt); game["attempts"] += 1
                if g == game["number"]:
                    bonus = max(0, (game["max"]-game["attempts"]+1)*5)
                    await msg.reply_text(f"🎯 *_CORRECT!_* 🎉 | 🔢 *{game['number']}* | ⭐ +{bonus} XP", parse_mode="Markdown")
                    if cid in group_ranks:
                        if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
                        group_ranks[cid][uid] += bonus
                    del group_games[cid]; return
                elif game["attempts"] >= game["max"]: await msg.reply_text(f"😢 *GAME OVER!* 🔢 *{game['number']}*", parse_mode="Markdown"); del group_games[cid]; return
                elif g < game["number"]: await msg.reply_text(f"📈 *HIGHER!* #{game['attempts']}/{game['max']}", parse_mode="Markdown")
                else: await msg.reply_text(f"📉 *LOWER!* #{game['attempts']}/{game['max']}", parse_mode="Markdown")
                return
            except: pass
        
        elif game["type"] == "rps":
            if txt in ["rock","paper","scissors"]:
                b = random.choice(["rock","paper","scissors"]); e = {"rock":"🪨","paper":"📄","scissors":"✂️"}
                if txt==b: r = "🤝 TIE!"
                elif (txt=="rock" and b=="scissors") or (txt=="paper" and b=="rock") or (txt=="scissors" and b=="paper"): r = "🎉 YOU WIN!"
                else: r = "😢 SONAKSHI WINS!"
                await msg.reply_text(f"✊ {e[txt]} `{txt}` vs {e[b]} `{b}` | {r}", parse_mode="Markdown"); del group_games[cid]; return
        
        elif game["type"] == "quiz":
            if txt == game["answer"]:
                await msg.reply_text("✅ *_CORRECT!_* 🎉 | ⭐ +10 XP", parse_mode="Markdown")
                if cid in group_ranks:
                    if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
                    group_ranks[cid][uid] += 10
                del group_games[cid]; return
            else:
                game["wrong"] += 1
                if game["wrong"] >= 2 and not game["hint_given"]: game["hint_given"] = True; await msg.reply_text(f"💡 *Hint:* {game['hint']}", parse_mode="Markdown")
                else: await msg.reply_text("❌ *Wrong!*", parse_mode="Markdown")
                return
        
        elif game["type"] == "scramble":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *_CORRECT!_* 🎉 | 🔤 *{game['answer'].upper()}* | ⭐ +8 XP", parse_mode="Markdown")
                if cid in group_ranks:
                    if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
                    group_ranks[cid][uid] += 8
                del group_games[cid]; return
            else:
                game["attempts"] += 1
                if game["attempts"] >= game["max"]: await msg.reply_text(f"😢 *Answer:* `{game['answer'].upper()}`", parse_mode="Markdown"); del group_games[cid]; return
                await msg.reply_text(f"❌ *Nahi! ({game['attempts']}/{game['max']})*", parse_mode="Markdown"); return
        
        elif game["type"] == "math":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *_CORRECT!_* 🎉 | 🧮 *{game['answer']}* | ⭐ +10 XP", parse_mode="Markdown")
                if cid in group_ranks:
                    if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
                    group_ranks[cid][uid] += 10
                del group_games[cid]; return
            else: await msg.reply_text("❌ *Wrong!*", parse_mode="Markdown"); return
        
        elif game["type"] == "truth": await msg.reply_text(f"🙊 *Sach bola!* 💖", parse_mode="Markdown"); del group_games[cid]; return
        
        elif game["type"] == "riddle":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *_SOLVED!_* 🎉 | 🧩 *{game['answer']}* | ⭐ +15 XP", parse_mode="Markdown")
                if cid in group_ranks:
                    if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
                    group_ranks[cid][uid] += 15
                del group_games[cid]; return
            else:
                if not game["hint_given"]: game["hint_given"] = True; await msg.reply_text(f"💡 *Hint:* {game['hint']}", parse_mode="Markdown")
                else: await msg.reply_text(f"❌ *Answer:* `{game['answer']}`", parse_mode="Markdown"); del group_games[cid]; return
                return
        
        elif game["type"] == "wordchain":
            last = game["last_word"]; ll = last[-1].lower()
            if txt in game["used_words"]: await msg.reply_text(f"❌ *Used!* `{ll.upper()}` se naya!", parse_mode="Markdown"); return
            if txt[0].lower() != ll: await msg.reply_text(f"❌ *`{ll.upper()}` se start ho!*", parse_mode="Markdown"); return
            game["used_words"].append(txt); game["last_word"] = txt; game["score"] += 1
            await msg.reply_text(f"✅ *Sahi!* ⛓️ 🔤 `{txt.upper()}` | 🔠 Next: `{txt[-1].upper()}` | ⭐ {game['score']}", parse_mode="Markdown"); return
    
    # FILTER
    if cid in group_filters:
        for w in group_filters[cid]:
            if w in msg.text.lower():
                try: await msg.delete()
                except: pass
                await msg.reply_text("🔞 *_Filtered!_*", parse_mode="Markdown"); return
    
    # AFK
    if msg.reply_to_message and msg.reply_to_message.from_user:
        ruid = msg.reply_to_message.from_user.id
        if ruid in group_afk and ruid != uid:
            afk = group_afk[ruid]; diff = get_ist_now() - afk["time"]
            h, rem = divmod(int(diff.total_seconds()), 3600); m, _ = divmod(rem, 60)
            ts = f"{h}h {m}m" if h else f"{m}m"
            await msg.reply_text(f"😴 *AFK!* 👤 *{afk['name']}* | 📝 {afk['reason']} | ⏱️ {ts} ago", parse_mode="Markdown")
    
    # RANK
    if ct != ChatType.PRIVATE:
        if cid not in group_ranks: group_ranks[cid] = {}
        if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
        group_ranks[cid][uid] += random.randint(1, 3)
    
    # AI REPLY
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
    
    cmds = [
        ("start",start),("help",cmd_help),("activate",activate),("deactivate",deactivate),("clear",clear),
        ("permissionoff",cmd_permissionoff),("permissionon",cmd_permissionon),("permissionlist",cmd_permissionlist),
        ("delete",cmd_delete),("blocklink",cmd_blocklink),
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
    for cmd, fn in cmds: app.add_handler(CommandHandler(cmd, fn))
    
    app.add_handler(CallbackQueryHandler(game_click, pattern="^gm_"))
    app.add_handler(CallbackQueryHandler(poll_click, pattern="^p[vr]_"))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡ — FULL LOCKDOWN! 🫧💖")
    print("✅ /permissionoff = ALL FEATURES DISABLED!")
    print("✅ Locked user: Commands + AI + Games — KUCH NAHI!")
    print("✅ FATHER 7614459746 — ONLY ONE WHO CAN RESTORE!")
    app.run_polling()

if __name__ == "__main__":
    main()
