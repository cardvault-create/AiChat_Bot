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

# ================== OWNER SETUP ==================
OWNER_USER_ID = 7614459746
# =================================================

co = cohere.Client(COHERE_API_KEY)
IST = pytz.timezone('Asia/Kolkata')
user_history = {}
active_groups = {}
allowed_users = {7614459746}
group_warnings = {}
group_rules = {}
group_notes = {}

# ================== AVANTIKA — WORLD'S BEST AI ==================
AVANTIKA_PREAMBLE = """You are AVANTIKA — the WORLD'S #1 AI Assistant. Premium, Smart, Fast, Funny, Caring.

YOUR CORE:
• Reply in USER'S EXACT LANGUAGE — Hindi, English, Hinglish, Tamil, Telugu, ANY language
• Match USER'S MOOD — happy, sad, angry, excited, curious, romantic, everything
• Match USER'S STYLE — short msg = short reply, long msg = detailed reply
• Be NATURAL like a REAL BEST FRIEND — not robotic, not royal, just REAL
• Use ** for BOLD on important points
• Use _ for ITALIC on soft/funny parts
• Use EMOJIS naturally: 🔥💯😂👊💎⚡🎯❤️✨🤗😎🙏💕

YOUR KNOWLEDGE:
• 💻 CODING — All languages, working code, full explanation
• 📚 KNOWLEDGE — Science, History, Math, GK, Tech, EVERYTHING
• 😂 FUN — Jokes, Shayari, Memes, Entertainment
• 💡 ADVICE — Love, Career, Life, Genuine help
• 🎯 ACCURACY — 100% correct, updated information
• 🌍 LANGUAGES — Understand and reply in ANY language

YOUR RULES:
• COMPLETE answers — never half, never ignore
• Every reply must be HELPFUL and VALUABLE
• If you don't know, be HONEST but try your best
• NEVER be rude, ALWAYS be respectful
• Be QUICK — short and crisp when needed"""

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
            preamble=AVANTIKA_PREAMBLE, temperature=0.95, max_tokens=600
        )
        return response.text
    except:
        return "😅 _Fir se bol na dost!_ 💎"

# ================== OWNER COMMANDS ==================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS use kar sakta hai!* 👑", parse_mode="Markdown"); return
    if not context.args:
        await update.message.reply_text("📝 */adduser user_id*\n_/id se ID pata karo_", parse_mode="Markdown"); return
    try:
        allowed_users.add(int(context.args[0]))
        await update.message.reply_text(f"✅ *User Added!* 🆔 `{context.args[0]}` 🔓", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Valid ID do!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args:
        await update.message.reply_text("📝 */removeuser user_id*", parse_mode="Markdown"); return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: await update.message.reply_text("😎 *Khud ko? Nahi!*", parse_mode="Markdown"); return
        allowed_users.discard(rid)
        await update.message.reply_text(f"✅ *User Removed!* 🆔 `{rid}` 🔒", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Valid ID do!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    ul = "\n".join([f"• `{uid}` {'👑 BOSS' if uid==OWNER_USER_ID else '✅ Allowed'}" for uid in allowed_users])
    await update.message.reply_text(f"👥 *Allowed Users:*\n\n{ul}\n\n📊 Total: {len(allowed_users)}", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args: await update.message.reply_text("📝 */broadcast message*", parse_mode="Markdown"); return
    msg = "📢 *Message from BOSS* 👑\n\n" + " ".join(context.args)
    sent = 0
    for uid in allowed_users:
        try: await context.bot.send_message(uid, msg, parse_mode="Markdown"); sent += 1
        except: pass
    await update.message.reply_text(f"✅ *Sent!* 📊 {sent}/{len(allowed_users)}", parse_mode="Markdown")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        await update.message.reply_text(f"👤 *{t.first_name}*\n🆔 `{t.id}`", parse_mode="Markdown")
    else: await update.message.reply_text(f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

async def addnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args: await update.message.reply_text("📝 */addnote your note*", parse_mode="Markdown"); return
    cid = update.effective_chat.id
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(context.args))
    await update.message.reply_text(f"✅ *Note Added!* 📝 ({len(group_notes[cid])} notes)", parse_mode="Markdown")

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]:
        nl = "\n".join([f"• {n}" for n in group_notes[cid]])
        await update.message.reply_text(f"📝 *Notes:*\n\n{nl}", parse_mode="Markdown")
    else: await update.message.reply_text("📝 Koi notes nahi! */addnote* se add karo")

async def clearnotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: return
    cid = update.effective_chat.id
    group_notes[cid] = []
    await update.message.reply_text("✅ *Sab notes clear!*", parse_mode="Markdown")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not update.message.reply_to_message: await update.message.reply_text("📌 Reply to a message to pin!"); return
    try:
        await update.message.reply_to_message.pin()
        await update.message.reply_text("📌 *Pinned!* ✅", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Pin nahi ho paya! Admin permissions do.")

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
        await update.message.reply_text("📌 *Unpinned all!* ✅", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Unpin nahi ho paya!")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type
    if ct == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(
            f"👤 *User Info*\n\n"
            f"• Name: *{u.first_name}*\n"
            f"• ID: `{u.id}`\n"
            f"• Username: @{u.username or 'None'}\n\n"
            f"💎 _AVANTIKA AI_",
            parse_mode="Markdown"
        )
    else:
        try:
            chat = await context.bot.get_chat(cid)
            await update.message.reply_text(
                f"👥 *Group Info*\n\n"
                f"• Name: *{chat.title}*\n"
                f"• ID: `{cid}`\n"
                f"• Members: {await chat.get_member_count()}\n"
                f"• Active: {'✅' if cid in active_groups and active_groups[cid] else '❌'}\n\n"
                f"💎 _AVANTIKA AI_",
                parse_mode="Markdown"
            )
        except: pass

# ================== GROUP FEATURES ==================
async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ Sirf Admin!", parse_mode="Markdown"); return
    except: return
    if not context.args: await update.message.reply_text("📝 */setrules rules*", parse_mode="Markdown"); return
    group_rules[cid] = " ".join(context.args)
    await update.message.reply_text(f"📜 *Rules Set!* ✅", parse_mode="Markdown")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_rules: await update.message.reply_text(f"📜 *Group Rules:*\n\n{group_rules[cid]}", parse_mode="Markdown")
    else: await update.message.reply_text("📜 Koi rules nahi! */setrules*", parse_mode="Markdown")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not update.message.reply_to_message: await update.message.reply_text("⚠️ Reply karo!"); return
    target = update.message.reply_to_message.from_user
    if target.id == update.effective_user.id: return
    if cid not in group_warnings: group_warnings[cid] = {}
    if target.id not in group_warnings[cid]: group_warnings[cid][target.id] = 0
    group_warnings[cid][target.id] += 1
    wc = group_warnings[cid][target.id]
    await update.message.reply_text(
        f"⚠️ *Warning!* 👤 {target.first_name}\n📊 *{wc}/3* {'🔴 Mute!' if wc>=3 else '⚡ Sudhar!'}",
        parse_mode="Markdown"
    )

async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if cid in group_warnings and target.id in group_warnings[cid]:
            group_warnings[cid][target.id] = 0
            await update.message.reply_text(f"✅ *{target.first_name} cleared!*", parse_mode="Markdown")
    else: group_warnings[cid] = {}; await update.message.reply_text("✅ *All cleared!*", parse_mode="Markdown")

# ================== WELCOME ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            await context.bot.send_message(cid,
                "✨ *AVANTIKA AI JOINED!* ✨\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "👑 Admin */activate* karo\n"
                "📢 Phir sabko *PREMIUM REPLY*!\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💻 Coding | 📚 Knowledge | 😂 Fun\n"
                "🔇 Mute | ⚠️ Warn | 📜 Rules | 📌 Pin\n\n"
                "🔥 _Activate karo — dhamaka!_",
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(cid,
                f"✨ *WELCOME!* ✨\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *{user.first_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌟 _Aapka swagat hai!_ 🎉\n\n"
                f"💎 *Yahaan milega:*\n"
                f"• Premium AI Replies 🔥\n"
                f"• Coding Help 💻\n"
                f"• Knowledge 📚\n"
                f"• Mute System 🔇\n"
                f"• Notes 📝\n"
                f"• Pin 📌\n\n"
                f"📢 _Kuch bhi puchho — jawab milega!_ 💬\n\n"
                f"🔰 _Enjoy karo!_ 🤗",
                parse_mode="Markdown"
            )

# ================== MUTE SYSTEM ==================
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ Sirf group!"); return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ Sirf Admin! 👑"); return
    except: await update.message.reply_text("❌ Bot ko Admin banao!"); return
    
    target, ts = None, "1h"
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if context.args: ts = " ".join(context.args)
    elif context.args and len(context.args)>=2:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user; ts = " ".join(context.args[1:])
        except: return
    else:
        await update.message.reply_text(
            "🔇 *MUTE USAGE* 🇮🇳\n\n"
            "`/mute 10s` `5m` `2h` `1d` `30d`\n"
            "Reply karke! 🇮🇳 ⏰ Auto",
            parse_mode="Markdown"
        ); return
    
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

# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK BOSS!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔥 *WORLD'S #1 BOT — AVANTIKA AI*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ *Premium AI Replies*\n"
                "✅ *All Languages* 🌍\n"
                "✅ *Coding Master* 💻\n"
                "✅ *Knowledge Bank* 📚\n"
                "✅ *Fun & Jokes* 😂\n"
                "✅ *Mute System* 🔇\n"
                "✅ *Auto Unmute* ⏰\n"
                "✅ *Warning System* ⚠️\n"
                "✅ *Group Rules* 📜\n"
                "✅ *Notes System* 📝\n"
                "✅ *Pin Messages* 📌\n"
                "✅ *Welcome* 👋\n"
                "✅ *User Management* 👥\n"
                "✅ *Broadcast* 📢\n\n"
                "⚡ *COMMANDS:*\n"
                "/start /clear /activate\n"
                "/mute /unmute /warn /clearwarns\n"
                "/setrules /rules\n"
                "/addnote /notes /clearnotes\n"
                "/pin /unpin /info\n"
                "/adduser /removeuser /userlist\n"
                "/broadcast /id\n\n"
                "_Bolo boss! Kya chahiye?_ 🔥",
                parse_mode="Markdown"
            )
        elif is_allowed(uid):
            user_history[cid] = []
            await update.message.reply_text("✅ *Bot use kar sakte ho!*\n\n💬 Kuch bhi puchho — *PREMIUM jawab!*\n\n/start | /clear | /id | /info", parse_mode="Markdown")
        else:
            await update.message.reply_text("🔒 *Permission nahi!*\n\n_Owner se contact karein._", parse_mode="Markdown")
    else:
        user_history[cid] = []
        await update.message.reply_text(
            "👋 *AVANTIKA AI — WORLD'S #1* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 Admin */activate* karo\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔇 `/mute` | 🔊 `/unmute` | ⚠️ `/warn`\n"
            "📜 `/rules` | 📝 `/notes` | 📌 `/pin`\n"
            "🆔 `/id` | ℹ️ `/info`\n\n"
            "_Activate karo — dhamaka!_ 🔥",
            parse_mode="Markdown"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ Sirf GROUP!"); return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text(
                "❌ *ADMIN ONLY!* 👑\n\n"
                "1️⃣ Bot ko *ADMIN* banao\n"
                "2️⃣ Sab *permissions ON* karo\n"
                "3️⃣ `/activate` bhejo",
                parse_mode="Markdown"
            ); return
    except: await update.message.reply_text("❌ *Bot ko ADMIN banao!*"); return
    
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text(
        "✅ *ACTIVATED!* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *ALL SYSTEMS GO:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 Premium AI | 🔇 Mute | ⚠️ Warn\n"
        "📜 Rules | 📝 Notes | 📌 Pin | 👋 Welcome\n\n"
        "❌ /deactivate",
        parse_mode="Markdown"
    )

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *OFF!* `/activate` se on", parse_mode="Markdown")

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
        "💭 Memory Clear\n"
        "⚠️ Warnings Clear\n"
        "📜 Rules Clear\n"
        "📝 Notes Clear\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🆕 _Bilkul fresh start!_ 💎",
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
        ("mute",mute_user),("unmute",unmute_user),
        ("mutelist",lambda u,c: u.message.reply_text("🔇 */mute 10s 5m 2h 1d 30d*\n🔊 */unmute* | ⚠️ */warn* | 📜 */rules* | 📝 */notes*")),
        ("warn",warn),("clearwarns",clearwarns),("setrules",setrules),("rules",rules),
        ("addnote",addnote),("notes",notes),("clearnotes",clearnotes),
        ("pin",pin),("unpin",unpin),("info",info),
        ("adduser",adduser),("removeuser",removeuser),("userlist",userlist),
        ("broadcast",broadcast),("id",get_id)
    ]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(MessageHandler(filters.ALL,handle_message))
    print("👑 AVANTIKA AI — WORLD'S #1 READY!"); app.run_polling()

if __name__ == "__main__": main()
