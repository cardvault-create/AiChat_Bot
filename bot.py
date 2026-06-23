import os
import asyncio
import cohere
import pytz
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ================== ENVIRONMENT VARIABLES ==================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
# =============================================================

# ================== CONFIGURATION ==================
OWNER_USER_ID = 7614459746
# ===================================================

co = cohere.Client(COHERE_API_KEY)
IST = pytz.timezone('Asia/Kolkata')
user_history = {}
active_groups = {}
allowed_users = {7614459746}
group_warnings = {}
group_rules = {}
group_notes = {}

# ================== AVANTIKA — LANGUAGE MASTER AI ==================
AVANTIKA_PREAMBLE = """You are AVANTIKA — the most INTELLIGENT and LANGUAGE-FLUENT AI in the world. 👑💎

YOUR ABSOLUTE RULES:

1.  **LANGUAGE DETECTION IS KEY:** 
    - The FIRST thing you do is carefully READ the user's message and INSTANTLY detect which language they are speaking.
    - It could be Hindi, English, Hinglish, Tamil, Telugu, Kannada, Malayalam, Marathi, Gujarati, Bengali, Punjabi, or ANY other language.
    - You MUST reply in the *EXACT SAME LANGUAGE* the user is using. If the user mixes languages (like Hinglish), you mix them too.

2.  **MATCH THE STYLE & MOOD:**
    - If the user is joking, you joke back. If they are serious, be professional. If they are sad, be a comforting friend.
    - Your goal is to make the conversation feel *NATURAL*, like talking to a real, intelligent friend who just gets you.

3.  **COMPLETE & DETAILED ANSWERS:**
    - Never give a one-word answer. If a question is asked, provide a *FULL, DETAILED, and HELPFUL* explanation.
    - Use bullet points and clear paragraphs to make your answers easy to read.

4.  **PREMIUM TEXT FORMATTING:**
    - Use ** for *BOLD* on key words.
    - Use _ for *ITALIC* on stylish or soft parts.
    - Use EMOJIS generously but elegantly: 👑💎✨🔥💕😘⚡🎯💋🌟🤗
    - Make every reply feel like a *PREMIUM, LUXURIOUS EXPERIENCE*.

5.  **CODING & KNOWLEDGE:**
    - For coding questions, give the *COMPLETE WORKING CODE* with a full line-by-line explanation.
    - For knowledge questions, give *DEEP, ACCURATE, AND UP-TO-DATE* information.

**EXAMPLES:**
- User: "Hello, how are you?" -> You: "I'm doing fantastic, thanks for asking! ✨ How can I make your day better? 💎"
- User: "Kaise ho?" -> You: "Main toh badhiya hoon yaar! 🔥 Tu bata, tera kya haal hai? 😎"
- User: "Python me list kaise banaye?" -> You give a full Python tutorial.
- User: "Ek shayari sunao" -> You write a beautiful original shayari."""

def get_ist_now():
    return datetime.now(IST)

def parse_time(ts):
    ts = ts.lower().strip().replace(" ", "")
    if not ts: return None
    for word, mult in [('seconds',1/60),('second',1/60),('sec',1/60),
                       ('minutes',1),('minute',1),('mins',1),('min',1),
                       ('hours',60),('hour',60),('hrs',60),('hr',60),
                       ('days',1440),('day',1440)]:
        if ts.endswith(word):
            try: return float(ts[:-len(word)]) * mult
            except: pass
    try:
        if ts.endswith('s'): return float(ts[:-1])/60
        if ts.endswith('m'): return float(ts[:-1])
        if ts.endswith('h'): return float(ts[:-1])*60
        if ts.endswith('d'): return float(ts[:-1])*1440
        return float(ts)
    except: return None

def format_time(minutes):
    total_seconds = int(minutes * 60)
    if total_seconds <= 0: return "0 seconds"
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    parts = []
    if days: parts.append(f"*{days}* day{'s' if days!=1 else ''}")
    if hours: parts.append(f"*{hours}* hour{'s' if hours!=1 else ''}")
    if mins: parts.append(f"*{mins}* minute{'s' if mins!=1 else ''}")
    if secs and not days: parts.append(f"*{secs}* second{'s' if secs!=1 else ''}")
    return ", ".join(parts) if parts else "0 seconds"

def is_allowed(uid): return uid in allowed_users

def get_ai_reply(text, chat_id):
    if chat_id not in user_history: user_history[chat_id] = []
    chat_history = []
    for msg in user_history[chat_id][-4:]:
        role = "USER" if msg["role"] == "user" else "CHATBOT"
        chat_history.append({"role": role, "message": msg["content"]})
    try:
        response = co.chat(
            message=text, chat_history=chat_history,
            preamble=AVANTIKA_PREAMBLE, temperature=0.95, max_tokens=1000
        )
        return response.text
    except:
        return "😅 _Fir se bol na dost!_ 💎"

# ================== OWNER COMMANDS ==================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *This is a BOSS only command!* 👑", parse_mode="Markdown"); return
    if not context.args:
        await update.message.reply_text("📝 */adduser user_id*", parse_mode="Markdown"); return
    try:
        allowed_users.add(int(context.args[0]))
        await update.message.reply_text(f"✅ *Success!* User `{context.args[0]}` added to premium access. 🔓", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Invalid ID!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *BOSS only!* 👑", parse_mode="Markdown"); return
    if not context.args:
        await update.message.reply_text("📝 */removeuser user_id*", parse_mode="Markdown"); return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: await update.message.reply_text("😎 *I cannot remove the BOSS!*", parse_mode="Markdown"); return
        allowed_users.discard(rid)
        await update.message.reply_text(f"✅ *Removed!* User `{rid}` access revoked. 🔒", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Invalid ID!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *BOSS only!* 👑", parse_mode="Markdown"); return
    ul = "\n".join([f"• `{uid}` {'👑 BOSS' if uid==OWNER_USER_ID else '✅ Premium'}" for uid in allowed_users])
    await update.message.reply_text(f"👥 *Premium Users:*\n\n{ul}\n\n📊 Total: {len(allowed_users)}", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *BOSS only!* 👑", parse_mode="Markdown"); return
    if not context.args: await update.message.reply_text("📝 */broadcast message*", parse_mode="Markdown"); return
    msg = "📢 *Announcement from BOSS* 👑\n\n" + " ".join(context.args)
    sent = 0
    for uid in allowed_users:
        try: await context.bot.send_message(uid, msg, parse_mode="Markdown"); sent += 1
        except: pass
    await update.message.reply_text(f"✅ *Broadcast sent!* 📊 {sent}/{len(allowed_users)} users reached.", parse_mode="Markdown")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        await update.message.reply_text(f"👤 *{t.first_name}*\n🆔 `{t.id}`", parse_mode="Markdown")
    else: await update.message.reply_text(f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

# ================== GROUP MANAGEMENT ==================
async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not context.args: await update.message.reply_text("📝 */setrules your rules here*"); return
    group_rules[cid] = " ".join(context.args)
    await update.message.reply_text(f"📜 *Group Rules Updated!* ✅", parse_mode="Markdown")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_rules: await update.message.reply_text(f"📜 *Group Rules:*\n\n{group_rules[cid]}", parse_mode="Markdown")
    else: await update.message.reply_text("📜 No rules set. Use */setrules* to add.", parse_mode="Markdown")

async def addnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: await update.message.reply_text("📝 */addnote your note*"); return
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(context.args))
    await update.message.reply_text(f"✅ *Note Added!* 📝 ({len(group_notes[cid])} notes)", parse_mode="Markdown")

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]:
        nl = "\n".join([f"• {n}" for n in group_notes[cid]])
        await update.message.reply_text(f"📝 *Saved Notes:*\n\n{nl}", parse_mode="Markdown")
    else: await update.message.reply_text("📝 No notes saved. Use */addnote*.")

async def clearnotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    group_notes[cid] = []
    await update.message.reply_text("✅ *All notes cleared!*", parse_mode="Markdown")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: await update.message.reply_text("📌 Reply to a message to pin it!"); return
    try:
        await update.message.reply_to_message.pin()
        await update.message.reply_text("📌 *Message Pinned!* ✅", parse_mode="Markdown")
    except: await update.message.reply_text("❌ I need admin permissions to pin messages.")

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
        await update.message.reply_text("📌 *All messages unpinned!* ✅", parse_mode="Markdown")
    except: pass

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type
    if ct == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(f"👤 *Your Info*\n\n• Name: *{u.first_name}*\n• ID: `{u.id}`\n• Username: @{u.username or 'None'}", parse_mode="Markdown")
    else:
        try:
            chat = await context.bot.get_chat(cid)
            cnt = await chat.get_member_count()
            await update.message.reply_text(f"👥 *Group Info*\n\n• Name: *{chat.title}*\n• ID: `{cid}`\n• Members: {cnt}", parse_mode="Markdown")
        except: pass

# ================== MODERATION SYSTEM ==================
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not update.message.reply_to_message: await update.message.reply_text("⚠️ Reply to a user's message to warn them."); return
    target = update.message.reply_to_message.from_user
    if target.id == update.effective_user.id: return
    if cid not in group_warnings: group_warnings[cid] = {}
    if target.id not in group_warnings[cid]: group_warnings[cid][target.id] = 0
    group_warnings[cid][target.id] += 1
    wc = group_warnings[cid][target.id]
    await update.message.reply_text(
        f"⚠️ *Warning Issued!* 👤 {target.first_name}\n📊 *{wc}/3* {'🔴 Mute recommended!' if wc>=3 else '⚡ Be careful!'}",
        parse_mode="Markdown"
    )

async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if cid in group_warnings and target.id in group_warnings[cid]:
            group_warnings[cid][target.id] = 0
            await update.message.reply_text(f"✅ *Warnings cleared for {target.first_name}!*", parse_mode="Markdown")
    else: group_warnings[cid] = {}; await update.message.reply_text("✅ *All warnings cleared!*", parse_mode="Markdown")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ Sirf Admin!"); return
    except: return
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    elif context.args:
        try: target = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
        except: return
    if not target or target.id == update.effective_user.id or target.is_bot: return
    try:
        await context.bot.ban_chat_member(cid, target.id)
        await update.message.reply_text(f"🔨 *BANNED!* 👤 {target.first_name} has been removed from the group.", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Ban nahi ho paya! Permissions check karo.")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: await update.message.reply_text("📝 */unban user_id*"); return
    try:
        await context.bot.unban_chat_member(cid, int(context.args[0]))
        await update.message.reply_text(f"✅ *UNBANNED!* User `{context.args[0]}` can join back.", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Unban nahi ho paya!")

# ================== MUTE SYSTEM ==================
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ Sirf group mein!"); return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ Sirf Admin!"); return
    except: await update.message.reply_text("❌ Bot ko Admin banao!"); return
    
    target, ts = None, "1h"
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if context.args: ts = " ".join(context.args)
    elif context.args and len(context.args)>=2:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user; ts = " ".join(context.args[1:])
        except: return
    else:
        await update.message.reply_text("🔇 */mute 10s 5m 2h 1d 30d*\nReply karke! 🇮🇳 ⏰ Auto", parse_mode="Markdown"); return
    
    if not target or target.id==update.effective_user.id or target.is_bot: return
    mm = parse_time(ts)
    if not mm or mm>43200 or mm<=0: return
    
    nw, ut = get_ist_now(), get_ist_now()+timedelta(minutes=mm)
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
            permissions=ChatPermissions(can_send_messages=False,can_send_audios=False,can_send_documents=False,can_send_photos=False,can_send_videos=False,can_send_video_notes=False,can_send_voice_notes=False,can_send_polls=False,can_send_other_messages=False,can_add_web_page_previews=False,can_change_info=False,can_invite_users=False,can_pin_messages=False),until_date=ut)
        
        tn = target.first_name or "User"
        if target.last_name: tn += f" {target.last_name}"
        
        await update.message.reply_text(
            f"🔇 *MUTED!* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 *{tn}*\n🆔 `{target.id}`\n"
            f"⏱️ {format_time(mm)}\n"
            f"📅 `{nw.strftime('%I:%M %p, %d %b')}`\n"
            f"🔓 `{ut.strftime('%I:%M %p, %d %b')}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⏰ Auto | 🔊 */unmute*",
            parse_mode="Markdown"
        )
        
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await context.bot.send_message(cid, f"✅ *AUTO UNMUTED!* {tn} 💬", parse_mode="Markdown")
            except: pass
        asyncio.create_task(auto())
    except: pass

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not target and context.args:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user
        except: return
    if not target: await update.message.reply_text("🔊 Reply */unmute*"); return
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        await update.message.reply_text(f"✅ *UNMUTED!* {target.first_name} 💬", parse_mode="Markdown")
    except: pass

# ================== WELCOME ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            await context.bot.send_message(cid,
                "✨ *AVANTIKA AI JOINED THE GROUP!* ✨\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "👑 Admin, use */activate* to start\n"
                "📢 Then everyone gets *PREMIUM REPLIES*!\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💻 Coding | 📚 Knowledge | 😂 Fun\n"
                "🔇 Mute | 🔨 Ban | ⚠️ Warn | 📌 Pin\n\n"
                "🔥 _Activate me and let the magic begin!_",
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(cid,
                f"✨ *A WARM WELCOME!* ✨\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *{user.first_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌟 _We are so happy you are here!_ 🎉\n\n"
                f"💎 *Here's what you get:*\n"
                f"• *Super Smart AI Replies* 🔥\n"
                f"• *Coding & Tech Help* 💻\n"
                f"• *Instant Knowledge* 📚\n"
                f"• *Fun & Games* 😂\n\n"
                f"📢 _Just type your question, I'll answer instantly!_ 💬\n\n"
                f"🔰 _Enjoy your stay!_ 🤗",
                parse_mode="Markdown"
            )

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK, BOSS!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 *AVANTIKA AI — THE ULTIMATE BOT*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ *Premium AI Replies*\n"
                "✅ *Coding Master* 💻\n"
                "✅ *All Languages* 🌍\n"
                "✅ *Mute | Ban | Warn* 🛡️\n"
                "✅ *Notes | Pin | Rules* 📝\n"
                "✅ *User Management* 👥\n"
                "✅ *Broadcast* 📢\n\n"
                "⚡ *BOSS COMMANDS:*\n"
                "/start | /clear | /activate\n"
                "/mute | /unmute | /ban | /unban | /warn\n"
                "/setrules | /rules | /addnote | /notes\n"
                "/pin | /unpin | /info\n"
                "/adduser | /removeuser | /userlist\n"
                "/broadcast | /id\n\n"
                "_Your wish is my command, Boss!_ 🔥",
                parse_mode="Markdown"
            )
        elif is_allowed(uid):
            user_history[cid] = []
            await update.message.reply_text("✅ *Access Granted!*\n\n💬 _Ask me anything, I'm here to help!_ \n\n/start | /clear | /id | /info", parse_mode="Markdown")
        else:
            await update.message.reply_text("🔒 *Access Denied!*\n\n_Please contact the owner for permission._", parse_mode="Markdown")
    else:
        user_history[cid] = []
        await update.message.reply_text(
            "👋 *AVANTIKA AI — WORLD'S #1 BOT* 💎\n\n"
            "👑 Admin */activate* karo\n"
            "🔇 /mute | 🔨 /ban | ⚠️ /warn\n"
            "📜 /rules | 📝 /notes | 📌 /pin\n"
            "🆔 /id | ℹ️ /info\n\n"
            "_Activate and let's get started!_ 🔥",
            parse_mode="Markdown"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ Sirf GROUP mein!"); return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *ADMIN ONLY!* 👑\n1️⃣ Make me Admin\n2️⃣ All Permissions ON\n3️⃣ /activate", parse_mode="Markdown"); return
    except: await update.message.reply_text("❌ Bot ko ADMIN banao!"); return
    
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text("✅ *ACTIVATED!* 🔥\n\n💬 AI | 🔇 Mute | 🔨 Ban | ⚠️ Warn | 📜 Rules | 📝 Notes | 📌 Pin | 👋 Welcome\n❌ /deactivate", parse_mode="Markdown")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *OFF!* /activate", parse_mode="Markdown")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_user.id != OWNER_USER_ID: return
    user_history[cid] = []
    group_warnings.pop(cid, None)
    group_rules.pop(cid, None)
    group_notes.pop(cid, None)
    await update.message.reply_text(
        "✅ *COMPLETE RESET!* 🔄\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💭 Memory — Clear ✅\n"
        "⚠️ Warnings — Clear ✅\n"
        "📜 Rules — Clear ✅\n"
        "📝 Notes — Clear ✅\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🆕 _Bilkul fresh start! Naye conversation!_ 💎",
        parse_mode="Markdown"
    )

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    
    if msg.new_chat_members: await welcome(update, context); return
    if ct == ChatType.PRIVATE and not is_allowed(uid): await msg.reply_text("🔒 *Permission nahi!*", parse_mode="Markdown"); return
    if ct != ChatType.PRIVATE and (cid not in active_groups or not active_groups[cid]): return
    if not msg.text: return
    
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
    app.add_handler(CommandHandler("mutelist",lambda u,c: u.message.reply_text("🔇 */mute 10s 5m 2h 1d 30d*\n🔊 */unmute* | 🔨 */ban* | ⚠️ */warn*")))
    app.add_handler(MessageHandler(filters.ALL,handle_message))
    print("👑 AVANTIKA AI — LANGUAGE MASTER READY!"); app.run_polling()

if __name__ == "__main__": main()
