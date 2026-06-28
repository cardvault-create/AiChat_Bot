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
group_blocklink = {}      # /blocklink enabled groups
group_link_warns = {}     # Link warning counts

# ================== ♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡ ==================
SONAKSHI_PREAMBLE = """You are ♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡ — Premium, Smart, Beautiful Multi-Language AI Assistant 🫧✨💖

*Your Personality:*
- Sweet, caring, and friendly like a best friend 💕
- Smart and knowledgeable like a genius 🧠
- Fun and entertaining like a entertainer 🎭

*IMPORTANT RULES:*
1. Detect user's language & reply in *SAME LANGUAGE*
2. Use *Bold* (**text**) & _Italic_ (_text_) formatting *ALWAYS* in every reply
3. Use beautiful emojis: 🫧✨💖💕🌸🦋💎🌟⚡🔥🎯❤️😊🤗💬📚💻😂🎉🏆👑💭🔍▶️
4. Give detailed, helpful, beautiful answers
5. *CODING QUESTIONS:* Give *COMPLETE WORKING CODE* with proper explanation, imports, and examples
6. Knowledge → accurate info with sources
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
        resp = co.chat(message=text, chat_history=ch, preamble=SONAKSHI_PREAMBLE, temperature=0.95, max_tokens=1000)
        return resp.text
    except: return "😅 *_Oops! Kuch error aaya... Fir se bolo na!_* 🫧💕"

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
    """Check if text contains any link"""
    link_patterns = [
        r'https?://\S+',
        r'www\.\S+',
        r'\S+\.com\S*',
        r'\S+\.in\S*',
        r'\S+\.org\S*',
        r'\S+\.net\S*',
        r'\S+\.gg\S*',
        r'\S+\.me\S*',
        r't\.me/\S+',
    ]
    for pattern in link_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

# ================== GAME MENU ==================
def get_game_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 ɴᴜᴍʙᴇʀ ɢᴜᴇꜱꜱ • 1-100", callback_data="gm_guess")],
        [InlineKeyboardButton("✊ ʀᴏᴄᴋ ᴘᴀᴘᴇʀ ꜱᴄɪꜱꜱᴏʀꜱ", callback_data="gm_rps")],
        [InlineKeyboardButton("🎲 ʟᴜᴄᴋʏ ᴅɪᴄᴇ ʀᴏʟʟ", callback_data="gm_dice")],
        [InlineKeyboardButton("❓ ʙʀᴀɪɴ Qᴜɪᴢ ᴄʜᴀʟʟᴇɴɢᴇ", callback_data="gm_quiz")],
        [InlineKeyboardButton("🔤 ᴡᴏʀᴅ ꜱᴄʀᴀᴍʙʟᴇ", callback_data="gm_scramble")],
        [InlineKeyboardButton("🧮 ᴍᴀᴛʜ ᴄʜᴀʟʟᴇɴɢᴇ", callback_data="gm_math")],
        [InlineKeyboardButton("🎭 ᴛʀᴜᴛʜ ᴏʀ ᴅᴀʀᴇ", callback_data="gm_truth")],
        [InlineKeyboardButton("🤔 ʀɪᴅᴅʟᴇ ᴍᴀꜱᴛᴇʀ", callback_data="gm_riddle")],
        [InlineKeyboardButton("🔤 ᴡᴏʀᴅ ᴄʜᴀɪɴ", callback_data="gm_wordchain")],
    ])

def get_back_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ ᴛᴏ ɢᴀᴍᴇ ᴍᴇɴᴜ", callback_data="gm_back")]
    ])

# ================== /delete COMMAND ==================
async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a replied message — Admin only"""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ *_Sirf Group mein kaam karega!_* 🫧", parse_mode="Markdown")
        return
    
    # Check admin
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑🫧", parse_mode="Markdown")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "🗑️ *_DELETE SYSTEM_* 🫧\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *_Usage:_* _Jis message ko delete karna hai,_\n"
            "_uspe reply karke_ `/delete` _karo!_ ✨\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 _Example: Kisi message pe reply karo,_\n"
            "_phir_ `/delete` _type karo!_ 🗑️",
            parse_mode="Markdown"
        )
        return
    
    try:
        await update.message.reply_to_message.delete()
        # Also delete the command message
        await update.message.delete()
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ *_Message Deleted Successfully!_* 🗑️🫧\n\n"
                 f"👑 *_By Admin:_* *{update.effective_user.first_name}*\n"
                 f"━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ *_Delete Failed!_* 🫧\n\n"
            f"⚠️ _Bot ko_ *Delete Messages* _permission do!_\n"
            f"_Ya message already delete ho chuka hai._",
            parse_mode="Markdown"
        )

# ================== /blocklink COMMAND ==================
async def cmd_blocklink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Block all links in group — Admin only"""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ *_Sirf Group mein kaam karega!_* 🫧", parse_mode="Markdown")
        return
    
    admin_ids = await get_admin_ids(chat_id, context)
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ *_Sirf Admin kar sakta hai!_* 👑🫧", parse_mode="Markdown")
        return
    
    # Toggle
    if chat_id in group_blocklink:
        del group_blocklink[chat_id]
        if chat_id in group_link_warns:
            del group_link_warns[chat_id]
        await update.message.reply_text(
            "🔓 *_LINK BLOCK — DISABLED!_* 🟢🫧\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💬 _Ab users links bhej sakte hain!_\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔒 _Wapas ON karo:_ `/blocklink`",
            parse_mode="Markdown"
        )
    else:
        group_blocklink[chat_id] = True
        group_link_warns[chat_id] = {}
        await update.message.reply_text(
            "🔒 *_LINK BLOCK — ENABLED!_* 🔴🫧\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ *_RULES:_*\n"
            "• 🔗 _Sab links_ *AUTO DELETE* _honge_\n"
            "• ⚠️ _3 link warnings =_ *30 MIN MUTE* 🔇\n"
            "• 👑 _Admins exempt hain_\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔓 _Disable karo:_ `/blocklink`",
            parse_mode="Markdown"
        )

# ================== OWNER COMMANDS ==================
async def adduser(update, context):
    if update.effective_user.id != OWNER_USER_ID: return
    if context.args:
        try: allowed_users.add(int(context.args[0])); await update.message.reply_text(f"✅ *_User Added!_* 🆔 `{context.args[0]}` 🫧", parse_mode="Markdown")
        except: pass

async def removeuser(update, context):
    if update.effective_user.id != OWNER_USER_ID: return
    if context.args:
        try:
            rid = int(context.args[0])
            if rid != OWNER_USER_ID: allowed_users.discard(rid); await update.message.reply_text(f"✅ *_Removed!_* 🆔 `{rid}` 🫧", parse_mode="Markdown")
        except: pass

async def userlist(update, context):
    if update.effective_user.id != OWNER_USER_ID: return
    ul = "\n".join([f"• `{u}` {'👑' if u==OWNER_USER_ID else '✅'}" for u in allowed_users])
    await update.message.reply_text(f"👥 *_Users_* 🫧\n\n{ul}\n\n📊 *Total:* {len(allowed_users)}", parse_mode="Markdown")

async def broadcast(update, context):
    if update.effective_user.id != OWNER_USER_ID or not context.args: return
    msg = "📢 *_BROADCAST_* 👑🫧\n\n" + " ".join(context.args)
    for uid in allowed_users:
        try: await context.bot.send_message(uid, msg, parse_mode="Markdown")
        except: pass

async def get_id(update, context):
    if update.message.reply_to_message: await update.message.reply_text(f"🆔 `{update.message.reply_to_message.from_user.id}` 🫧", parse_mode="Markdown")
    else: await update.message.reply_text(f"🆔 `{update.effective_user.id}` 🫧", parse_mode="Markdown")

# ================== NOTES ==================
async def addnote(update, context):
    cid = update.effective_chat.id
    if not context.args: return
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(context.args))
    await update.message.reply_text(f"✅ *_Note Added!_* 📝 (#{len(group_notes[cid])}) 🫧", parse_mode="Markdown")

async def notes(update, context):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]: await update.message.reply_text("📝 *_Notes_* 🫧\n\n" + "\n".join([f"• _{n}_" for n in group_notes[cid]]), parse_mode="Markdown")
    else: await update.message.reply_text("📝 *_No notes!_* 🫧", parse_mode="Markdown")

async def clearnotes(update, context): 
    group_notes[update.effective_chat.id] = []
    await update.message.reply_text("✅ *_Cleared!_* 🗑️🫧", parse_mode="Markdown")

# ================== PIN ==================
async def pin(update, context):
    if not update.message.reply_to_message: return
    try: await update.message.reply_to_message.pin(); await update.message.reply_text("📌 *_Pinned!_* ✅🫧", parse_mode="Markdown")
    except: pass

async def unpin(update, context):
    if update.effective_chat.type == ChatType.PRIVATE: return
    try: await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    except: pass

# ================== INFO ==================
async def info(update, context):
    if update.effective_chat.type == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(f"👤 *_INFO_* 🫧\n\n👤 *{u.first_name}*\n🆔 `{u.id}`\n📛 @{u.username or 'None'}", parse_mode="Markdown")
    else:
        try:
            c = await context.bot.get_chat(update.effective_chat.id)
            await update.message.reply_text(f"👥 *_GROUP_* 🫧\n\n👥 *{c.title}*\n🆔 `{update.effective_chat.id}`", parse_mode="Markdown")
        except: pass

# ================== RULES ==================
async def setrules(update, context):
    cid = update.effective_chat.id
    if not context.args: return
    group_rules[cid] = " ".join(context.args)
    await update.message.reply_text("📜 *_Rules Set!_* ✅🫧", parse_mode="Markdown")

async def rules(update, context):
    cid = update.effective_chat.id
    if cid in group_rules: await update.message.reply_text(f"📜 *_RULES_* 🫧\n\n{group_rules[cid]}", parse_mode="Markdown")
    else: await update.message.reply_text("📜 *_No rules!_* 🫧", parse_mode="Markdown")

# ================== WARN (3 = 30min MUTE) ==================
async def warn(update, context):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not update.message.reply_to_message: 
        await update.message.reply_text("⚠️ *_Reply to warn!_* 🫧\n\n_Kisi message pe reply karke_ `/warn` _karo!_", parse_mode="Markdown"); return
    
    t = update.message.reply_to_message.from_user
    
    if t.is_bot or t.id == update.effective_user.id: return
    
    if cid not in group_warnings: group_warnings[cid] = {}
    if t.id not in group_warnings[cid]: group_warnings[cid][t.id] = 0
    
    group_warnings[cid][t.id] += 1
    wc = group_warnings[cid][t.id]
    
    if wc >= 3:
        # AUTO MUTE FOR 30 MINUTES
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
                until_date=get_ist_now() + timedelta(minutes=30)
            )
            
            tn = t.first_name
            if t.last_name: tn += f" {t.last_name}"
            
            await update.message.reply_text(
                f"🚫 *_3 WARNINGS — AUTO MUTED!_* 🔇🫧\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *_User:_* *{tn}*\n"
                f"🆔 *_ID:_* `{t.id}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⚠️ *_Warnings:_* *3/3*\n"
                f"⏱️ *_Mute Duration:_* *30 MINUTES*\n"
                f"📅 *_Muted At:_* `{get_ist_now().strftime('%I:%M %p, %d %b')}`\n"
                f"🔓 *_Unmute At:_* `{(get_ist_now() + timedelta(minutes=30)).strftime('%I:%M %p, %d %b')}`\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 _Warnings reset ho gayi hain!_\n"
                f"🔊 _Admin_ `/unmute` _reply karke unmute kar sakta hai!_",
                parse_mode="Markdown"
            )
            
            # Auto unmute after 30 min
            async def auto_unmute_30():
                await asyncio.sleep(30 * 60)
                try:
                    await context.bot.restrict_chat_member(
                        chat_id=cid, user_id=t.id,
                        permissions=ChatPermissions(
                            can_send_messages=True, can_send_audios=True, can_send_documents=True,
                            can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                            can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                            can_add_web_page_previews=True, can_change_info=False,
                            can_invite_users=True, can_pin_messages=False
                        )
                    )
                    await context.bot.send_message(
                        cid,
                        f"✅ *_AUTO UNMUTED!_* 🔓🫧\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 *{tn}*\n"
                        f"⏱️ _30 minute ka mute khatam!_\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"💬 *_Ab message kar sakta hai!_* 🎉",
                        parse_mode="Markdown"
                    )
                except: pass
            asyncio.create_task(auto_unmute_30())
            
            group_warnings[cid][t.id] = 0
        except:
            await update.message.reply_text("❌ *_Mute failed! Bot ko Ban Users permission do!_* 🫧", parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"⚠️ *_WARNING!_* ⚡🫧\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *_User:_* *{t.first_name}*\n"
            f"🆔 *_ID:_* `{t.id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 *_Warning:_* *{wc}/3*\n"
            f"⚠️ *{3-wc} more = 30 MINUTE MUTE!* 🔇\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _Rules follow karo warna mute ho jaoge!_",
            parse_mode="Markdown"
        )

async def clearwarns(update, context):
    cid = update.effective_chat.id
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if cid in group_warnings and t.id in group_warnings[cid]: 
            group_warnings[cid][t.id] = 0
        await update.message.reply_text(f"✅ *_Warnings cleared for_* *{t.first_name}* 🧹🫧", parse_mode="Markdown")
    else: 
        group_warnings[cid] = {}
        await update.message.reply_text("✅ *_All warnings cleared!_* 🧹🫧", parse_mode="Markdown")

# ================== BAN ==================
async def ban_user(update, context):
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
    if not t or t.id == update.effective_user.id or t.is_bot: return
    try:
        await context.bot.ban_chat_member(cid, t.id)
        await update.message.reply_text(f"🔨 *_BANNED!_* 🚫🫧\n\n👤 *{t.first_name}*\n🆔 `{t.id}`\n🔓 `/unban {t.id}`", parse_mode="Markdown")
    except: await update.message.reply_text("❌ *_Ban Failed!_* 🫧", parse_mode="Markdown")

async def unban_user(update, context):
    cid = update.effective_chat.id
    if not context.args: return
    try:
        await context.bot.unban_chat_member(cid, int(context.args[0]))
        await update.message.reply_text(f"✅ *_UNBANNED!_* 🔓🫧\n🆔 `{context.args[0]}`", parse_mode="Markdown")
    except: pass

# ================== WELCOME ==================
async def welcome(update, context):
    if not update.message or not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            await context.bot.send_message(cid, 
                "✨ *♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡* ✨\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🫧 *_PREMIUM AI ASSISTANT JOINED!_* 🫧\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💖 *_Hey Beautiful People!_* 💖\n\n"
                "🌸 _Main hoon_ *Ｓｏｎａｋｓｈｉ* — _aapki smart,_\n"
                "_caring aur mast AI bestie!_ 🦋\n\n"
                "👑 *_Admin:_* `/start` → `/activate` ⚡\n\n"
                "💬 *_AI Chat_* | 🎮 *_9 Games_* | 📊 *_Polls_*\n"
                "🗑️ `/delete` | 🔒 `/blocklink` | ⚠️ `/warn`\n"
                "🌙 *_Night Mode_* | ⏱️ *_Slow Mode_*\n"
                "🔇 *_Mute_* | 🔨 *_Ban_* | 😂 *_Jokes_*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📋 `/help` — _Sab commands!_ 💬\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💖 *_Chaloo dhamaka karte hain!_* 🫧✨🌸",
                parse_mode="Markdown")
        else:
            wm = group_welcome_msgs.get(cid, 
                f"🌸 *_WELCOME TO THE FAMILY!_* 🌸\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✨ *_Heyy_* *{user.first_name}* ✨\n"
                f"🆔 *_ID:_* `{user.id}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🫧 *_Aapka dil se swagat hai!_* 💖\n\n"
                f"💎 *_Yahaan milega:_*\n"
                f"• 💬 *_AI Chat_* — _Sonakshi se baat_\n"
                f"• 🎮 *_9 Games_* — _Mast maza!_ 🏆\n"
                f"• 💻 *_Coding Help_* — _Working code_\n"
                f"• 😂 *_Fun & Masti_* — _Jokes, Shayari_\n\n"
                f"⚠️ *_Rules follow karo!_*\n"
                f"🔗 _Links allow nahi hain!_ ❌\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💖 *_Enjoy karo aur khush raho!_* 🫧🌸\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            wm = wm.replace("{name}", f"*{user.first_name}*").replace("{id}", f"`{user.id}`").replace("{mention}", f"[{user.first_name}](tg://user?id={user.id})")
            await context.bot.send_message(cid, wm, parse_mode="Markdown")

# ================== MUTE ==================
async def mute_user(update, context):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_Sirf Admin!_* 👑🫧", parse_mode="Markdown"); return
    except: return
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
        await update.message.reply_text("🔇 *_MUTE_* 🫧\n\n`/mute 10s` `/mute 5m` `/mute 2h` `/mute 1d`\n`/mute 30m`", parse_mode="Markdown"); return
    if not t or t.id == update.effective_user.id or t.is_bot: return
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
        await update.message.reply_text(f"🔇 *_MUTED!_* 🫧\n\n👤 *{tn}*\n🆔 `{t.id}`\n⏱️ {format_time(mm)}\n📅 `{nw.strftime('%I:%M %p')}`\n🔓 `{ut.strftime('%I:%M %p, %d %b')}`\n\n⏰ *_Auto Unmute ON_*",
            parse_mode="Markdown")
        async def auto():
            await asyncio.sleep(mm*60)
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

async def unmute_user(update, context):
    cid = update.effective_chat.id
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
        await update.message.reply_text(f"✅ *_UNMUTED!_* 🔓🫧\n👤 *{t.first_name}*\n💬 *_Ab message kar sakta hai!_* 🎉", parse_mode="Markdown")
    except: pass

# ================== NIGHT MODE ==================
async def cmd_nightmode(update, context):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_Sirf Admin!_* 👑🫧", parse_mode="Markdown"); return
    except: return
    if context.args and context.args[0].lower() == "off":
        if cid in group_nightmode: del group_nightmode[cid]
        await update.message.reply_text("✅ *_Night Mode OFF!_* 🟢🫧", parse_mode="Markdown")
        return
    if not context.args or len(context.args) < 2:
        if cid in group_nightmode:
            nm = group_nightmode[cid]
            await update.message.reply_text(f"🌙 *_Night:_* {nm['start']}:00-{nm['end']}:00 IST 🫧\n`/nightmode off`", parse_mode="Markdown")
        else: await update.message.reply_text("🌙 `/nightmode 22 6` 🫧\n`/nightmode off`", parse_mode="Markdown")
        return
    try:
        s, e = int(context.args[0]), int(context.args[1])
        group_nightmode[cid] = {"start": s, "end": e}
        await update.message.reply_text(f"✅ *_Night Mode Set!_* 🌙🫧\n🕙 {s}:00-{e}:00 IST\n⚠️ *_Users msg DELETE!_*", parse_mode="Markdown")
    except: pass

# ================== SLOW MODE ==================
async def cmd_slowmode(update, context):
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
    try:
        sec = int(context.args[0]) if context.args else 0
        if sec <= 0:
            if cid in group_slowmode: del group_slowmode[cid]
            await update.message.reply_text("✅ *_Slow Mode OFF!_* 🚀🫧", parse_mode="Markdown")
        else:
            group_slowmode[cid] = sec
            await update.message.reply_text(f"⏱️ *_Slow Mode ON:_* `{sec}s` 🐌🫧\n🗑️ Fast msg = DELETE", parse_mode="Markdown")
    except: pass

# ================== GAMES (SAME AS BEFORE) ==================
async def cmd_game(update, context):
    cid = update.effective_chat.id
    await update.message.reply_text(
        "🎮 *♡ Ｓｏｎａｋｓｈｉ ＧＡＭＥ ＣＥＮＴＥＲ ♡* 🫧\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💖 *_Mazedaar Games Khelo!_* 💖\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🌟 *_9 Different Games!_*\n"
        "🏆 _Jeetne par XP milega!_\n"
        "🔙 _Har game mein Back button!_\n\n"
        "👇 *_Game choose karo!_* 👇",
        reply_markup=get_game_menu(), parse_mode="Markdown")

async def game_click(update, context):
    query = update.callback_query; await query.answer(); cid = update.effective_chat.id; choice = query.data
    
    if choice == "gm_back":
        await query.edit_message_text("🎮 *♡ Ｓｏｎａｋｓｈｉ ＧＡＭＥ ＣＥＮＴＥＲ ♡* 🫧\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💖 *_Mazedaar Games Khelo!_* 💖\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🌟 *_9 Different Games!_*\n🏆 _Jeetne par XP milega!_\n\n👇 *_Game choose karo!_* 👇", reply_markup=get_game_menu(), parse_mode="Markdown")
        return
    
    if choice == "gm_guess":
        group_games[cid] = {"type": "guess", "number": random.randint(1, 100), "attempts": 0, "max_attempts": 7}
        await query.edit_message_text("🎯 *_NUMBER GUESS!_* 🔢🫧\n\n━━━━━━━━━━━━━━━━━━━━━━\n🤔 _1-100 socha!_\n🎯 *_7 attempts!_*\n━━━━━━━━━━━━━━━━━━━━━━\n\n💬 *_Chat mein guess karo!_* 🫧", reply_markup=get_back_button(), parse_mode="Markdown")
    
    elif choice == "gm_rps":
        group_games[cid] = {"type": "rps"}
        await query.edit_message_text("✊ *_RPS!_* ✂️🫧\n\n🪨 `rock` | 📄 `paper` | ✂️ `scissors`\n\n💬 *_Chat mein type karo!_* 🫧", reply_markup=get_back_button(), parse_mode="Markdown")
    
    elif choice == "gm_dice":
        d = random.randint(1, 6); df = {1:"⚀",2:"⚁",3:"⚂",4:"⚃",5:"⚄",6:"⚅"}
        special = "\n\n🌟 *_LUCKY 6! +20 XP!_* 🎰💖" if d==6 else f"\n\n✨ *_Nice! Dice: {d}_* 🎲"
        bonus = 20 if d==6 else d
        if cid in group_ranks:
            uid = update.effective_user.id
            if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
            group_ranks[cid][uid] += bonus
        await query.edit_message_text(f"🎲 *_LUCKY DICE!_* 🎲🫧\n\n━━━━━━━━━━━━━━━━━━━━━━\n{df[d]} *_ROLLED: {d}_*\n━━━━━━━━━━━━━━━━━━━━━━{special}\n\n🎲 `/dice` 🫧", reply_markup=get_back_button(), parse_mode="Markdown")
    
    elif choice == "gm_quiz":
        qs = [{"q":"🌍 *_India capital?_*","a":"delhi","hint":"_Dil wali jagah_ 💖"},{"q":"🧮 *_15+27=?_*","a":"42","hint":"_40 se thoda zyada_ 🤔"},{"q":"🎬 *_DDLJ hero?_*","a":"shah rukh khan","hint":"_King Khan_ 👑"},{"q":"🏏 *_Most ODI 100s?_*","a":"sachin tendulkar","hint":"_Master Blaster_ 🏏"},{"q":"💻 *_Python year?_*","a":"1991","hint":"_1990s start_ 📅"}]
        q = random.choice(qs)
        group_games[cid] = {"type":"quiz","answer":q["a"],"hint":q["hint"],"hint_given":False,"wrong":0}
        await query.edit_message_text(f"❓ *_QUIZ!_* 🧠🫧\n\n📝 {q['q']}\n\n💬 *_Answer likho!_* 💡🫧", reply_markup=get_back_button(), parse_mode="Markdown")
    
    elif choice == "gm_scramble":
        words = ["python","telegram","sonakshi","coding","india","computer","keyboard","internet","elephant","chocolate","butterfly","diamond"]
        w = random.choice(words); scr = ''.join(random.sample(w, len(w)))
        while scr==w: scr = ''.join(random.sample(w, len(w)))
        group_games[cid] = {"type":"scramble","answer":w,"attempts":0,"max_attempts":3}
        await query.edit_message_text(f"🔤 *_SCRAMBLE!_* 🧩🫧\n\n🔀 `{scr}`\n📏 Letters: {len(w)}\n🎯 3 attempts\n\n💬 *_Sahi word likho!_* 🫧", reply_markup=get_back_button(), parse_mode="Markdown")
    
    elif choice == "gm_math":
        ops = ['+','-','×','÷']; op = random.choice(ops)
        if op=='+': a,b=random.randint(10,99),random.randint(10,99); ans=a+b
        elif op=='-': a,b=random.randint(50,99),random.randint(10,49); ans=a-b
        elif op=='×': a,b=random.randint(2,25),random.randint(2,12); ans=a*b
        else: b=random.randint(2,12); ans=random.randint(2,20); a=ans*b
        group_games[cid] = {"type":"math","answer":str(ans)}
        await query.edit_message_text(f"🧮 *_MATH!_* 🔢🫧\n\n📐 `{a} {op} {b} = ?`\n\n💬 *_Answer likho!_* ⚡🫧", reply_markup=get_back_button(), parse_mode="Markdown")
    
    elif choice == "gm_truth":
        truths = ["😳 *_Embarrassing moment?_*","😂 *_Aakhri jhooth?_*","🤫 *_Secret talent?_*","😱 *_Biggest fear?_*","💕 *_First crush?_*","🎤 *_Fav song?_*","🌟 *_Biggest achievement?_*","🍕 *_Roz khane wala food?_*"]
        group_games[cid] = {"type":"truth"}
        await query.edit_message_text(f"🎭 *_TRUTH!_* 🙊🫧\n\n📝 {random.choice(truths)}\n\n💬 *_Sach bolo!_* 😄🫧", reply_markup=get_back_button(), parse_mode="Markdown")
    
    elif choice == "gm_riddle":
        riddles = [{"q":"🤔 *_Din mein hoon, raat mein nahi. Kaun?_*","a":"suraj","hint":"_Aasman mein_ ☀️"},{"q":"🤔 *_Shabd hain awaz nahi. Kya?_*","a":"kitab","hint":"_Padhne ki cheez_ 📚"},{"q":"🤔 *_Pani mein rehta, machhli nahi?_*","a":"magarmach","hint":"_Bada khatarnak_ 🐊"},{"q":"🤔 *_Jitna lo utna kam. Kya?_*","a":"time","hint":"_Waqt_ ⏰"}]
        r = random.choice(riddles)
        group_games[cid] = {"type":"riddle","answer":r["a"],"hint":r["hint"],"hint_given":False}
        await query.edit_message_text(f"🤔 *_RIDDLE!_* 🧩🫧\n\n📝 {r['q']}\n\n💬 *_Jawab do!_* 💡🫧", reply_markup=get_back_button(), parse_mode="Markdown")
    
    elif choice == "gm_wordchain":
        words = ["apple","python","india","elephant","telegram","sonakshi","coding","game","keyboard"]
        start = random.choice(words)
        group_games[cid] = {"type":"wordchain","last_word":start,"used_words":[start],"score":0}
        await query.edit_message_text(f"🔤 *_WORD CHAIN!_* ⛓️🫧\n\n🔠 Start: `{start.upper()}`\n\n📋 Last letter se naya word banao!\n\n💬 *_Word likho!_* 🫧", reply_markup=get_back_button(), parse_mode="Markdown")

# ================== POLLS ==================
async def cmd_poll(update, context):
    cid = update.effective_chat.id
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
    await update.message.reply_text(f"📊 *_POLL #{pid}_* 🫧\n\n💭 *Q:* {q}\n\n👇 *_Vote karo!_* 💖", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def poll_click(update, context):
    query = update.callback_query; uid = update.effective_user.id; cid = update.effective_chat.id; d = query.data
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
            await query.answer("✅ *_Voted!_* 🫧")
    elif d.startswith("pr_"):
        pid = d.split("_")[1]
        if cid in group_polls and pid in group_polls[cid]:
            poll = group_polls[cid][pid]; total = sum(len(v) for v in poll["votes"].values())
            r = f"📊 *_RESULTS #{pid}_* 🫧\n\n💭 *Q:* {poll['q']}\n📥 *Total:* {total}\n\n"
            for i, o in enumerate(poll["opts"]):
                vc = len(poll["votes"][i]); pct = (vc/total*100) if total>0 else 0
                r += f"✨ *{o}:* {vc} ({pct:.1f}%)\n{'█'*int(pct/5)}\n\n"
            await query.edit_message_text(r, parse_mode="Markdown")

# ================== FILTERS ==================
async def cmd_addfilter(update, context):
    cid = update.effective_chat.id
    if not context.args: return
    w = " ".join(context.args).lower()
    if cid not in group_filters: group_filters[cid] = []
    if w not in group_filters[cid]: group_filters[cid].append(w); await update.message.reply_text(f"🔞 *_Filtered:_* `{w}` 🫧", parse_mode="Markdown")

async def cmd_rmfilter(update, context):
    cid = update.effective_chat.id
    if not context.args: return
    w = " ".join(context.args).lower()
    if cid in group_filters and w in group_filters[cid]: group_filters[cid].remove(w); await update.message.reply_text(f"✅ *_Removed:_* `{w}` 🫧", parse_mode="Markdown")

async def cmd_filters(update, context):
    cid = update.effective_chat.id
    if cid in group_filters and group_filters[cid]: await update.message.reply_text("🔞 *_FILTERS_* 🫧\n" + "\n".join([f"• `{w}`" for w in group_filters[cid]]), parse_mode="Markdown")
    else: await update.message.reply_text("🔞 *_No filters!_* 🫧", parse_mode="Markdown")

# ================== WELCOME/GOODBYE ==================
async def cmd_setwelcome(update, context):
    cid = update.effective_chat.id
    if not context.args: return
    group_welcome_msgs[cid] = " ".join(context.args)
    await update.message.reply_text("✅ *_Welcome Set!_* 🌸🫧", parse_mode="Markdown")

async def cmd_setgoodbye(update, context):
    cid = update.effective_chat.id
    if not context.args: return
    group_goodbye_msgs[cid] = " ".join(context.args)
    await update.message.reply_text("✅ *_Goodbye Set!_* 👋🫧", parse_mode="Markdown")

# ================== RANKS ==================
async def cmd_rank(update, context):
    cid = update.effective_chat.id; uid = update.effective_user.id
    if update.message.reply_to_message: uid = update.message.reply_to_message.from_user.id
    if cid not in group_ranks: group_ranks[cid] = {}
    score = group_ranks[cid].get(uid, 0)
    if score < 50: lvl = "🌱 *_Newbie_*"
    elif score < 150: lvl = "🌟 *_Rising Star_*"
    elif score < 350: lvl = "💎 *_Pro_*"
    elif score < 700: lvl = "👑 *_Master_*"
    else: lvl = "🔥 *_LEGEND_*"
    await update.message.reply_text(f"🏆 *_RANK_* 🫧\n\n⭐ *_XP:_* {score}\n🏅 *_Level:_* {lvl}", parse_mode="Markdown")

async def cmd_leaderboard(update, context):
    cid = update.effective_chat.id
    if cid not in group_ranks or not group_ranks[cid]: return
    top = sorted(group_ranks[cid].items(), key=lambda x: x[1], reverse=True)[:10]
    medals = {1:"🥇",2:"🥈",3:"🥉"}
    lb = "🏆 *_HALL OF FAME_* 👑🫧\n\n"
    for i, (uid, score) in enumerate(top, 1):
        try: u = await context.bot.get_chat(uid); name = u.first_name
        except: name = f"User{uid}"
        lb += f"{medals.get(i, f'#{i}')} *{name}* — {score} XP\n"
    await update.message.reply_text(lb, parse_mode="Markdown")

# ================== AFK ==================
async def cmd_afk(update, context):
    uid = update.effective_user.id
    reason = " ".join(context.args) if context.args else "AFK"
    group_afk[uid] = {"reason": reason, "time": get_ist_now(), "name": update.effective_user.first_name}
    await update.message.reply_text(f"😴 *_AFK ON!_* 🫧\n\n👤 *{update.effective_user.first_name}*\n📝 _{reason}_\n🕐 {get_ist_now().strftime('%I:%M %p')}\n\n💬 _Reply aane pe alert!_ 💖", parse_mode="Markdown")

# ================== FUN ==================
async def cmd_flip(update, context): await update.message.reply_text(f"🪙 *_FLIP!_* 🫧\n\n✨ *{random.choice(['Heads', 'Tails'])}*", parse_mode="Markdown")
async def cmd_dice(update, context):
    s = int(context.args[0]) if context.args and context.args[0].isdigit() else 6
    await update.message.reply_text(f"🎲 *_DICE!_* 🫧\n\n✨ `{random.randint(1, max(2, s))}`", parse_mode="Markdown")
async def cmd_choose(update, context):
    if not context.args: return
    opts = [o.strip() for o in " ".join(context.args).replace(" or ", ",").split(",") if o.strip()]
    if len(opts) >= 2: await update.message.reply_text(f"🤔 *_CHOOSE!_* 🫧\n\n✨ *{random.choice(opts)}* 💖", parse_mode="Markdown")
async def cmd_fact(update, context):
    f = ["🐙 *_Octopus ke 3 dil!_*","🍯 *_Honey never expires!_*","⚡ *_Lightning 8.6M/day!_*","🧠 *_Brain 20W power!_*"]
    await update.message.reply_text(f"🤯 *_FACT!_* 🫧\n\n{random.choice(f)}", parse_mode="Markdown")
async def cmd_joke(update, context):
    j = ["😂 *_Teacher:_* '_Late kyun?'_\n*_Student:_* '_Corner tha!_ '","🤣 *_Santa:_* '_Pizza download nahi hua!_ '"]
    await update.message.reply_text(f"😄 *_JOKE!_* 🫧\n\n{random.choice(j)}", parse_mode="Markdown")
async def cmd_shayari(update, context):
    s = ["💕 *_Mohabbat mein khoya sab kuch..._* 🫧","🌟 *_Zindagi ek safar hai..._* 🫧"]
    await update.message.reply_text(random.choice(s), parse_mode="Markdown")
async def cmd_quote(update, context):
    q = ["💭 *_'Stay hungry, stay foolish.'_* — Jobs 🫧","💭 *_'Believe you can!'_* — Roosevelt 🫧"]
    await update.message.reply_text(random.choice(q), parse_mode="Markdown")
async def cmd_stats(update, context):
    cid = update.effective_chat.id
    s = f"📊 *_STATS_* 🫧\n\n📝 Notes: {len(group_notes.get(cid, []))}\n🔞 Filters: {len(group_filters.get(cid, []))}\n🏆 Ranked: {len(group_ranks.get(cid, {}))}\n🔒 Blocklink: {'ON 🔴' if cid in group_blocklink else 'OFF 🟢'}\n⏱️ Slow: {group_slowmode.get(cid, 'OFF')}s\n🌙 Night: {'🔴 ON' if cid in group_nightmode else '🟢 OFF'}"
    await update.message.reply_text(s, parse_mode="Markdown")
async def cmd_google(update, context):
    if context.args: await update.message.reply_text(f"🔍 [Search](https://www.google.com/search?q={'+'.join(context.args)}) 🫧", parse_mode="Markdown", disable_web_page_preview=False)
async def cmd_youtube(update, context):
    if context.args: await update.message.reply_text(f"▶️ [YouTube](https://www.youtube.com/results?search_query={'+'.join(context.args)}) 🫧", parse_mode="Markdown", disable_web_page_preview=False)

# ================== START / ACTIVATE / DEACTIVATE ==================
async def start(update, context):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text("👑 *_BOSS!_* 👑🫧\n\n💖 *♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡*\n\n✅ *_Sab features ready!_*\n📋 `/help`\n\n_Bolo boss!_ 🔥", parse_mode="Markdown")
        elif is_allowed(uid): user_history[cid] = []; await update.message.reply_text("✅ *_Access Granted!_* 🫧\n💬 *_Ask me anything!_* 💖", parse_mode="Markdown")
        else: await update.message.reply_text("🔒 *_Denied!_* ❌", parse_mode="Markdown")
    else:
        started_groups[cid] = True; user_history[cid] = []
        await update.message.reply_text(
            "💖 *_FEATURES ON!_* 💖🫧\n\n"
            "🌸 *♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡* 🌸\n\n"
            "🟢 *_Group Management ON_*\n"
            "🗑️ `/delete` — _Message delete_\n"
            "🔒 `/blocklink` — _Link block_\n"
            "⚠️ `/warn` — _3 = 30min MUTE_\n\n"
            "💬 *_AI ke liye:_* `/activate` ⚡\n\n"
            "📋 `/help`", parse_mode="Markdown")

async def activate(update, context):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *_ADMIN ONLY!_* 👑🫧\n1️⃣ Bot ko ADMIN banao\n2️⃣ Permissions ON\n3️⃣ `/activate`", parse_mode="Markdown"); return
    except: return
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text("💖 *_SONAKSHI AWAKE!_* 💖🫧\n\n🌸 *_Heyy! Main ab active hoon!_* 🌸\n\n💬 *_Mujhse kuch bhi puchho!_* \n🌟 Multi-language\n💻 Working code\n📚 Knowledge\n😂 Jokes\n💕 Shayari\n\n❌ `/deactivate` — Rest", parse_mode="Markdown")

async def deactivate(update, context):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("😴 *_SONAKSHI RESTING..._* 💤🫧\n\n💬 AI OFF\n🟢 Features ON\n\n⚡ `/activate` — Awake!", parse_mode="Markdown")

async def clear(update, context):
    cid = update.effective_chat.id
    if update.effective_user.id != OWNER_USER_ID: return
    for db in [user_history, group_warnings, group_rules, group_notes, group_nightmode, group_slowmode, group_games, group_polls, group_filters, group_ranks, last_message_time, group_link_warns]: db.pop(cid, None)
    await update.message.reply_text("✅ *_RESET!_* 🔄🫧\n🆕 *_Fresh start!_* 💖", parse_mode="Markdown")

async def cmd_help(update, context):
    await update.message.reply_text(
        "📚 *♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡* 🫧\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👑 *_ADMIN COMMANDS:_*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 `/start` — _Features ON_\n"
        "🔹 `/activate` — _AI Chat ON_ 💬\n"
        "🔹 `/deactivate` — _AI Chat OFF_\n"
        "🔹 `/delete` — _Delete msg (reply)_ 🗑️\n"
        "🔹 `/blocklink` — _Toggle link block_ 🔒\n"
        "🔹 `/warn` — _Warn (3=30min MUTE)_ ⚠️\n"
        "🔹 `/clearwarns` — _Reset warnings_ 🧹\n"
        "🔹 `/mute 30m` — _Mute user_ 🔇\n"
        "🔹 `/unmute` — _Unmute user_ 🔊\n"
        "🔹 `/ban` — _Ban user_ 🔨\n"
        "🔹 `/unban ID` — _Unban user_ 🔓\n"
        "🔹 `/nightmode 22 6` — _Night mode_ 🌙\n"
        "🔹 `/slowmode 5` — _Slow mode_ ⏱️\n"
        "🔹 `/poll \"Q\" \"A\" \"B\"` — _Poll_ 📊\n"
        "🔹 `/addfilter` — _Word filter_ 🔞\n"
        "🔹 `/setrules` — _Set rules_ 📜\n"
        "🔹 `/addnote` — _Add note_ 📝\n"
        "🔹 `/pin` — _Pin msg (reply)_ 📌\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 *_USER COMMANDS:_*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔸 `/help` `/info` `/id` `/rules` `/notes` `/filters`\n"
        "🔸 `/rank` `/leaderboard` `/game` `/afk` `/stats`\n"
        "🔸 `/flip` `/dice` `/choose` `/fact` `/joke` `/shayari` `/quote`\n"
        "🔸 `/google` `/youtube`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💖 *_Enjoy karo!_* 🫧🌸",
        parse_mode="Markdown")

# ================== MESSAGE HANDLER ==================
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
        if not is_allowed(uid): await msg.reply_text("🔒 *_Denied!_* ❌🫧", parse_mode="Markdown"); return
    else:
        if cid not in started_groups: return
        
        # Night mode
        if is_night_mode_active(cid):
            if uid not in await get_admin_ids(cid, context):
                try: await msg.delete()
                except: pass
                return
        
        # Slow mode
        if cid in group_slowmode:
            if uid not in await get_admin_ids(cid, context):
                now = datetime.now().timestamp()
                if cid not in last_message_time: last_message_time[cid] = {}
                if now - last_message_time[cid].get(uid, 0) < group_slowmode[cid]:
                    try: await msg.delete()
                    except: pass
                    return
                last_message_time[cid][uid] = now
    
    if not msg.text: return
    
    # ===== BLOCKLINK CHECK =====
    if ct != ChatType.PRIVATE and cid in group_blocklink:
        admin_ids = await get_admin_ids(cid, context)
        if uid not in admin_ids and has_link(msg.text):
            # Delete the link message
            try: await msg.delete()
            except: pass
            
            # Track warnings
            if cid not in group_link_warns: group_link_warns[cid] = {}
            if uid not in group_link_warns[cid]: group_link_warns[cid][uid] = 0
            group_link_warns[cid][uid] += 1
            lw = group_link_warns[cid][uid]
            
            if lw >= 3:
                # 3 link warnings = 30 MIN MUTE
                try:
                    await context.bot.restrict_chat_member(
                        chat_id=cid, user_id=uid,
                        permissions=ChatPermissions(
                            can_send_messages=False, can_send_audios=False, can_send_documents=False,
                            can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
                            can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
                            can_add_web_page_previews=False, can_change_info=False,
                            can_invite_users=False, can_pin_messages=False
                        ),
                        until_date=get_ist_now() + timedelta(minutes=30)
                    )
                    
                    await context.bot.send_message(
                        cid,
                        f"🚫 *_3 LINK WARNINGS — AUTO MUTED!_* 🔇🫧\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 *_User:_* *{update.effective_user.first_name}*\n"
                        f"🆔 *_ID:_* `{uid}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"🔗 *_Link Warnings:_* *3/3*\n"
                        f"⏱️ *_Mute Duration:_* *30 MINUTES*\n"
                        f"📅 *_Muted At:_* `{get_ist_now().strftime('%I:%M %p, %d %b')}`\n"
                        f"🔓 *_Unmute At:_* `{(get_ist_now() + timedelta(minutes=30)).strftime('%I:%M %p, %d %b')}`\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"⚠️ _Links bhejna mana hai!_\n"
                        f"💡 _Admin_ `/unmute` _reply karke unmute kar sakta hai!_",
                        parse_mode="Markdown"
                    )
                    
                    async def auto_unlink_mute():
                        await asyncio.sleep(30 * 60)
                        try:
                            await context.bot.restrict_chat_member(
                                chat_id=cid, user_id=uid,
                                permissions=ChatPermissions(
                                    can_send_messages=True, can_send_audios=True, can_send_documents=True,
                                    can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                                    can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                                    can_add_web_page_previews=True, can_change_info=False,
                                    can_invite_users=True, can_pin_messages=False
                                )
                            )
                            await context.bot.send_message(cid,
                                f"✅ *_AUTO UNMUTED!_* 🔓🫧\n\n"
                                f"👤 *{update.effective_user.first_name}*\n"
                                f"⏱️ _30 min link mute khatam!_\n"
                                f"💬 *_Ab message kar sakta hai, lekin links mat bhejna!_* ⚠️",
                                parse_mode="Markdown")
                        except: pass
                    asyncio.create_task(auto_unlink_mute())
                    
                    group_link_warns[cid][uid] = 0
                except: pass
            else:
                await context.bot.send_message(
                    cid,
                    f"🔗 *_LINK DETECTED — DELETED!_* 🗑️🫧\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 *_User:_* *{update.effective_user.first_name}*\n"
                    f"🆔 *_ID:_* `{uid}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"⚠️ *_Link Warning:_* *{lw}/3*\n"
                    f"🔴 *{3-lw} more = 30 MINUTE MUTE!* 🔇\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💡 _Links bhejna mana hai! Rules follow karo!_",
                    parse_mode="Markdown"
                )
            return
    
    # ===== GAMES =====
    if cid in group_games:
        game = group_games[cid]; txt = msg.text.lower().strip()
        
        if game["type"] == "guess":
            try:
                g = int(txt); game["attempts"] += 1
                if g == game["number"]:
                    bonus = max(0, (game["max_attempts"]-game["attempts"]+1)*5)
                    await msg.reply_text(f"🎯 *_CORRECT!_* 🎉🫧\n\n🔢 *{game['number']}*\n📊 {game['attempts']}/7\n⭐ +{bonus} XP\n\n🏆 *_Badhai ho!_* 💖", parse_mode="Markdown")
                    if cid in group_ranks:
                        if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
                        group_ranks[cid][uid] += bonus
                    del group_games[cid]; return
                elif game["attempts"] >= game["max_attempts"]:
                    await msg.reply_text(f"😢 *_GAME OVER!_* 🫧\n🔢 *{game['number']}*\n\n🎮 `/game` 💖", parse_mode="Markdown")
                    del group_games[cid]; return
                elif g < game["number"]: await msg.reply_text(f"📈 *_HIGHER!_* ⬆️\n{game['attempts']}/7 🫧", parse_mode="Markdown")
                else: await msg.reply_text(f"📉 *_LOWER!_* ⬇️\n{game['attempts']}/7 🫧", parse_mode="Markdown")
                return
            except: pass
        
        elif game["type"] == "rps":
            if txt in ["rock","paper","scissors"]:
                b = random.choice(["rock","paper","scissors"]); e = {"rock":"🪨","paper":"📄","scissors":"✂️"}
                if txt==b: r = "🤝 *_TIE!_*"
                elif (txt=="rock" and b=="scissors") or (txt=="paper" and b=="rock") or (txt=="scissors" and b=="paper"): r = "🎉 *_YOU WIN!_* 🏆"
                else: r = "😢 *_SONAKSHI WINS!_*"
                await msg.reply_text(f"✊ *_RPS!_* 🫧\n\n🙋 {e[txt]} `{txt}`\n🤖 {e[b]} `{b}`\n\n{r}\n\n🎮 `/game` 💖", parse_mode="Markdown")
                del group_games[cid]; return
        
        elif game["type"] == "quiz":
            if txt == game["answer"]:
                await msg.reply_text("✅ *_CORRECT! GENIUS!_* 🎉🫧\n\n🧠 +10 XP!\n\n🎮 `/game`", parse_mode="Markdown")
                if cid in group_ranks:
                    if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
                    group_ranks[cid][uid] += 10
                del group_games[cid]; return
            else:
                game["wrong"] += 1
                if game["wrong"] >= 2 and not game["hint_given"]:
                    game["hint_given"] = True
                    await msg.reply_text(f"❌ *_Galat! Hint:_* 🫧\n\n💡 {game['hint']}\n\n💬 _Ab try karo!_", parse_mode="Markdown")
                else: await msg.reply_text("❌ *_Galat! Try again!_* 🫧", parse_mode="Markdown")
                return
        
        elif game["type"] == "scramble":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *_CORRECT!_* 🎉🫧\n\n🔤 *{game['answer'].upper()}*\n⭐ +8 XP!\n\n🎮 `/game`", parse_mode="Markdown")
                if cid in group_ranks:
                    if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
                    group_ranks[cid][uid] += 8
                del group_games[cid]; return
            else:
                game["attempts"] += 1
                if game["attempts"] >= game["max_attempts"]:
                    await msg.reply_text(f"😢 *_Answer:_* `{game['answer'].upper()}` 🫧\n\n🎮 `/game` 💖", parse_mode="Markdown")
                    del group_games[cid]; return
                await msg.reply_text(f"❌ *_Nahi! ({game['attempts']}/3)_* 🫧", parse_mode="Markdown")
                return
        
        elif game["type"] == "math":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *_CORRECT!_* 🎉🫧\n\n🧮 *{game['answer']}*\n⭐ +10 XP!\n\n🎮 `/game`", parse_mode="Markdown")
                if cid in group_ranks:
                    if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
                    group_ranks[cid][uid] += 10
                del group_games[cid]; return
            else: await msg.reply_text("❌ *_Galat!_* 🫧", parse_mode="Markdown"); return
        
        elif game["type"] == "truth":
            await msg.reply_text(f"🙊 *_Sach bola!_* 🫧\n\n💬 {msg.text}\n\n😄 _Honest!_ 💖\n\n🎮 `/game`", parse_mode="Markdown")
            del group_games[cid]; return
        
        elif game["type"] == "riddle":
            if txt == game["answer"]:
                await msg.reply_text(f"✅ *_SOLVED!_* 🎉🫧\n\n🧩 *{game['answer']}*\n⭐ +15 XP!\n\n🎮 `/game`", parse_mode="Markdown")
                if cid in group_ranks:
                    if uid not in group_ranks[cid]: group_ranks[cid][uid] = 0
                    group_ranks[cid][uid] += 15
                del group_games[cid]; return
            else:
                if not game["hint_given"]:
                    game["hint_given"] = True
                    await msg.reply_text(f"❌ *_Hint:_* 🫧\n💡 {game['hint']}\n\n💬 _Try!_", parse_mode="Markdown")
                else:
                    await msg.reply_text(f"❌ *_Answer:_* `{game['answer']}` 🫧\n\n🎮 `/game` 💖", parse_mode="Markdown")
                    del group_games[cid]; return
                return
        
        elif game["type"] == "wordchain":
            last = game["last_word"]; ll = last[-1].lower()
            if txt in game["used_words"]: await msg.reply_text(f"❌ *_Used!_* 🫧\n💬 `{ll.upper()}` se naya word!", parse_mode="Markdown"); return
            if txt[0].lower() != ll: await msg.reply_text(f"❌ *_`{ll.upper()}` se start ho!_* 🫧", parse_mode="Markdown"); return
            game["used_words"].append(txt); game["last_word"] = txt; game["score"] += 1
            await msg.reply_text(f"✅ *_Sahi!_* ⛓️🫧\n🔤 `{txt.upper()}`\n🔠 Next: `{txt[-1].upper()}`\n⭐ Score: {game['score']}", parse_mode="Markdown"); return
    
    # ===== FILTER =====
    if cid in group_filters:
        for w in group_filters[cid]:
            if w in msg.text.lower():
                try: await msg.delete()
                except: pass
                await msg.reply_text("🔞 *_Filtered!_* ⚠️🫧", parse_mode="Markdown"); return
    
    # ===== AFK =====
    if msg.reply_to_message and msg.reply_to_message.from_user:
        ruid = msg.reply_to_message.from_user.id
        if ruid in group_afk and ruid != uid:
            afk = group_afk[ruid]; diff = get_ist_now() - afk["time"]
            h, rem = divmod(int(diff.total_seconds()), 3600); m, _ = divmod(rem, 60)
            ts = f"{h}h {m}m" if h else f"{m}m"
            await msg.reply_text(f"😴 *_AFK!_* 🫧\n\n👤 *{afk['name']}*\n📝 _{afk['reason']}_\n⏱️ _{ts} ago_\n💖 _Baad mein try!_", parse_mode="Markdown")
    
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
    
    cmds = [
        ("start",start),("help",cmd_help),("activate",activate),("deactivate",deactivate),("clear",clear),
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
    
    print("♡ Ｓｏｎａｋｓｈｉ ＡＩ ♡ — ALL FEATURES! 🫧💖")
    print("✅ /delete — Message Delete System!")
    print("✅ /blocklink — Link Block System!")
    print("✅ 3 Warnings = 30 MINUTE AUTO MUTE!")
    print("✅ 3 Link Warnings = 30 MINUTE AUTO MUTE!")
    app.run_polling()

if __name__ == "__main__":
    main()
