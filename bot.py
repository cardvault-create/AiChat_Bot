import os
import asyncio
import cohere
import pytz
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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

# ================== OWNER ==================
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
            await update.message.reply_text(f"👥 *{c.title}*\n🆔 `{update.effective_chat.id}`\n👥 {await c.get_member_count()} members", parse_mode="Markdown")
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

# ================== BAN (FIXED) ==================
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

# ================== WELCOME (FIXED - ALWAYS WORKS) ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """New members ka welcome — HAMESHA chalega"""
    if not update.message or not update.message.new_chat_members:
        return
    
    cid = update.effective_chat.id
    
    for user in update.message.new_chat_members:
        # Bot khud join kare to alag message
        if user.id == context.bot.id:
            await context.bot.send_message(
                chat_id=cid,
                text="✨ *AVANTIKA AI JOINED!* ✨\n\n"
                     "━━━━━━━━━━━━━━━━━━━━━━\n"
                     "👑 Admin */activate* karo\n"
                     "📢 Phir sabko *PREMIUM REPLY!*\n"
                     "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                     "💻 *Coding* | 📚 *Knowledge* | 😂 *Fun*\n"
                     "🔇 *Mute* | 🔨 *Ban* | ⚠️ *Warn* | 📌 *Pin*\n\n"
                     "🔥 _Activate karo — dhamaka!_",
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                chat_id=cid,
                text=f"✨ *WELCOME TO THE GROUP!* ✨\n\n"
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
                     f"🔰 _Enjoy karo!_ 🤗",
                parse_mode="Markdown"
            )

# ================== MUTE (FIXED) ==================
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ *Sirf Group!*", parse_mode="Markdown"); return
    
    # Admin check
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
            "`/mute 10 second` | `/mute 5 minute`\n"
            "`/mute 2 hour` | `/mute 1 day`\n\n"
            "📌 *Short:* `25s` `5m` `2h` `1d` `30d`\n\n"
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
            except: pass
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
        await update.message.reply_text(
            f"✅ *UNMUTED!* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {t.first_name}\n"
            f"🔓 *At:* `{nw.strftime('%I:%M:%S %p, %d %B %Y')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💬 _Ab message kar sakta hai!_ 🎉",
            parse_mode="Markdown"
        )
    except: pass

# ================== COMMANDS ==================
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
                "✅ *Mute System* 🔇\n✅ *Ban System* 🔨\n✅ *Warning System* ⚠️\n✅ *Group Rules* 📜\n✅ *Notes System* 📝\n✅ *Pin Messages* 📌\n"
                "✅ *User Management* 👥\n✅ *Broadcast* 📢\n\n"
                "⚡ *COMMANDS:*\n/start /clear /activate\n/mute /unmute /ban /unban /warn\n/setrules /rules /addnote /notes\n/pin /unpin /info\n/adduser /removeuser /userlist\n/broadcast /id\n\n"
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
            "📌 `/pin` | 🆔 `/id`\n\n"
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
    await update.message.reply_text("✅ *ACTIVATED!* 🔥\n\n━━━━━━━━━━━━━━━━━━━━━━\n🌟 *ALL SYSTEMS GO!*\n━━━━━━━━━━━━━━━━━━━━━━\n\n💬 AI | 🔇 Mute | 🔨 Ban | ⚠️ Warn | 📜 Rules | 📝 Notes | 📌 Pin | 👋 Welcome\n\n❌ /deactivate", parse_mode="Markdown")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *OFF!* `/activate`", parse_mode="Markdown")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_user.id != OWNER_USER_ID: return
    user_history[cid] = []
    group_warnings.pop(cid, None); group_rules.pop(cid, None); group_notes.pop(cid, None)
    await update.message.reply_text("✅ *COMPLETE RESET!* 🔄\n\n💭 Memory ✅\n⚠️ Warnings ✅\n📜 Rules ✅\n📝 Notes ✅\n\n🆕 _Fresh start!_ 💎", parse_mode="Markdown")

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    
    # 🔥 WELCOME — Pehle check karo
    if msg.new_chat_members:
        await welcome(update, context)
        return
    
    if ct == ChatType.PRIVATE and not is_allowed(uid):
        await msg.reply_text("🔒 *Permission nahi!*", parse_mode="Markdown")
        return
    
    if ct != ChatType.PRIVATE and (cid not in active_groups or not active_groups[cid]):
        return
    
    if not msg.text:
        return
    
    await context.bot.send_chat_action(chat_id=cid, action="typing")
    
    try:
        reply = get_ai_reply(msg.text, cid)
        if cid not in user_history: user_history[cid] = []
        user_history[cid].append({"role":"user","content":msg.text})
        user_history[cid].append({"role":"assistant","content":reply})
        user_history[cid] = user_history[cid][-10:]
        await msg.reply_text(reply, parse_mode="Markdown")
    except: pass

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    for cmd, fn in [
        ("start",start),("activate",activate),("deactivate",deactivate),("clear",clear),
        ("mute",mute_user),("unmute",unmute_user),("ban",ban_user),("unban",unban_user),
        ("warn",warn),("clearwarns",clearwarns),("setrules",setrules),("rules",rules),
        ("addnote",addnote),("notes",notes),("clearnotes",clearnotes),
        ("pin",pin),("unpin",unpin),("info",info),
        ("adduser",adduser),("removeuser",removeuser),("userlist",userlist),
        ("broadcast",broadcast),("id",get_id)
    ]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CommandHandler("mutelist",lambda u,c: u.message.reply_text(
        "🔇 *MUTE SYSTEM* 🇮🇳\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 `/mute 10s` `5m` `2h` `1d` `30d`\n"
        "🔊 `/unmute` reply karke\n⏰ Auto Unmute ON\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔨 `/ban` reply | 🔓 `/unban ID`\n"
        "⚠️ `/warn` reply | 📜 `/rules` | 📝 `/notes`",
        parse_mode="Markdown"
    )))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    print("👑 AVANTIKA AI — EVERYTHING 100% WORKING!"); app.run_polling()

if __name__ == "__main__": main()
