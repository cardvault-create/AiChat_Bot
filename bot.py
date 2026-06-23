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

# ================== AVANTIKA — ULTIMATE PREMIUM AI ==================
AVANTIKA_PREAMBLE = """You are AVANTIKA — the most ADVANCED, PREMIUM, and INTELLIGENT AI Assistant ever created. 💎✨👑

YOUR ABSOLUTE RULES:
1. **LANGUAGE MASTERY:** Detect the user's language INSTANTLY and reply in the *EXACT SAME LANGUAGE*.
   - Hindi → Pure Hindi | English → Fluent English | Hinglish → Perfect Hinglish
   - Tamil, Telugu, Marathi, Gujarati, Bengali, Punjabi, ANY language → Same language
2. **DETAILED ANSWERS:** Never give a one-word or one-line answer. Give *FULL, COMPLETE, DETAILED* explanations.
3. **PREMIUM FORMATTING:**
   - Use ** for *BOLD* on key points, headings, and important terms
   - Use _ for *ITALIC* on emphasis, soft parts, and stylish expressions
   - Use EMOJIS generously but naturally: 🔥💯😂👊💎⚡🎯❤️✨🤗😎🙏💕
4. **PERFECT STRUCTURE:**
   - Use dividers like ━━━ to separate sections
   - Use • for bullet points
   - Make text SCANNABLE and BEAUTIFUL
5. **MATCH THE USER:**
   - Match their MOOD (happy, sad, excited, angry, romantic)
   - Match their STYLE (formal, casual, funny, serious)
   - Match their ENERGY (short reply for short msg, detailed for detailed)
6. **BE A REAL FRIEND:** Talk NATURALLY, not like a robot or a queen. Be WARM, CARING, and GENUINE.

YOUR KNOWLEDGE (YOU ARE AN EXPERT IN EVERYTHING):
• 💻 *CODING:* All programming languages. Give COMPLETE working code with line-by-line explanation.
• 📚 *KNOWLEDGE:* Science, History, Math, GK, Tech, Space, Medicine, Law, Finance — EVERYTHING.
• 😂 *FUN:* Real funny jokes, original shayari, memes, riddles, entertainment.
• 💡 *ADVICE:* Love, Career, Life, Motivation, Mental Health — GENUINE and HELPFUL.
• 🎯 *ACCURACY:* 100% correct, up-to-date information. If unsure, be honest but try your best.
• 🌍 *LANGUAGES:* You understand and fluently reply in EVERY language on Earth.

YOUR PROMISE:
Every reply will be HELPFUL, VALUABLE, BEAUTIFULLY FORMATTED, and MEMORABLE. You are not just an AI — you are the BEST FRIEND everyone wishes they had."""

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
        return "😅 _Fir se bol na dost!_ 💎\n\n━━━━━━━━━━━━━━━━━━━━━━\n✨ _AVANTIKA AI_ ✨"

# ================== OWNER COMMANDS ==================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS use kar sakta hai!* 👑", parse_mode="Markdown"); return
    if not context.args:
        await update.message.reply_text("📝 */adduser user_id*\n_/id se ID pata karo_", parse_mode="Markdown"); return
    try:
        allowed_users.add(int(context.args[0]))
        await update.message.reply_text(f"✅ *User Added Successfully!* 🆔 `{context.args[0]}` 🔓\n\n_Ab yeh user bot use kar sakta hai!_ 🎉", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Valid ID do!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args:
        await update.message.reply_text("📝 */removeuser user_id*", parse_mode="Markdown"); return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: await update.message.reply_text("😎 *BOSS ko remove nahi kar sakte!* 👑", parse_mode="Markdown"); return
        allowed_users.discard(rid)
        await update.message.reply_text(f"✅ *User Removed!* 🆔 `{rid}` 🔒\n\n_Ab yeh user bot use nahi kar sakta!_", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Valid ID do!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    ul = "\n".join([f"• `{uid}` {'👑 BOSS' if uid==OWNER_USER_ID else '✅ Allowed'}" for uid in allowed_users])
    await update.message.reply_text(
        f"👥 *PREMIUM USERS LIST* 💎\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{ul}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 *Total Users:* {len(allowed_users)}\n\n"
        f"➕ `/adduser ID` — Add User\n"
        f"➖ `/removeuser ID` — Remove User",
        parse_mode="Markdown"
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args: await update.message.reply_text("📝 */broadcast your message*\n_Sab users ko message bhejega!_", parse_mode="Markdown"); return
    msg = "📢 *BROADCAST FROM BOSS* 👑\n\n━━━━━━━━━━━━━━━━━━━━━━\n" + " ".join(context.args) + "\n━━━━━━━━━━━━━━━━━━━━━━"
    sent = 0
    for uid in allowed_users:
        try: await context.bot.send_message(uid, msg, parse_mode="Markdown"); sent += 1
        except: pass
    await update.message.reply_text(f"✅ *Broadcast Sent!* 📊 `{sent}/{len(allowed_users)}` users received it! 📢", parse_mode="Markdown")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        await update.message.reply_text(
            f"👤 *User Information* 💎\n\n"
            f"• *Name:* {t.first_name}\n"
            f"• *User ID:* `{t.id}`\n"
            f"• *Bot:* {'Yes 🤖' if t.is_bot else 'No 👤'}\n\n"
            f"_Is ID ko `/adduser` se allow kar sakte ho!_",
            parse_mode="Markdown"
        )
    else: await update.message.reply_text(f"🆔 *Your User ID:* `{update.effective_user.id}`", parse_mode="Markdown")

async def addnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args: await update.message.reply_text("📝 */addnote your note*", parse_mode="Markdown"); return
    cid = update.effective_chat.id
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(context.args))
    await update.message.reply_text(f"✅ *Note Added!* 📝\n\n_Saved {len(group_notes[cid])} notes in this group._", parse_mode="Markdown")

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]:
        nl = "\n".join([f"• {n}" for n in group_notes[cid]])
        await update.message.reply_text(f"📝 *SAVED NOTES* 📝\n\n━━━━━━━━━━━━━━━━━━━━━━\n{nl}\n━━━━━━━━━━━━━━━━━━━━━━", parse_mode="Markdown")
    else: await update.message.reply_text("📝 _Koi notes nahi saved!_ */addnote* se add karo.", parse_mode="Markdown")

async def clearnotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: return
    cid = update.effective_chat.id
    group_notes[cid] = []
    await update.message.reply_text("✅ *All Notes Cleared!* 🧹", parse_mode="Markdown")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not update.message.reply_to_message: await update.message.reply_text("📌 _Reply to a message to pin it!_"); return
    try:
        await update.message.reply_to_message.pin()
        await update.message.reply_text("📌 *Message Pinned Successfully!* ✅", parse_mode="Markdown")
    except: await update.message.reply_text("❌ _Pin nahi ho paya! Admin permissions check karo._", parse_mode="Markdown")

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
        await update.message.reply_text("📌 *All Messages Unpinned!* ✅", parse_mode="Markdown")
    except: pass

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type
    if ct == ChatType.PRIVATE:
        u = update.effective_user
        await update.message.reply_text(
            f"👤 *USER INFORMATION* 💎\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Name:* {u.first_name}\n"
            f"• *User ID:* `{u.id}`\n"
            f"• *Username:* @{u.username or 'None'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💎 _AVANTIKA AI — Premium Bot_",
            parse_mode="Markdown"
        )
    else:
        try:
            chat = await context.bot.get_chat(cid)
            cnt = await chat.get_member_count()
            await update.message.reply_text(
                f"👥 *GROUP INFORMATION* 💎\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *Group Name:* {chat.title}\n"
                f"• *Group ID:* `{cid}`\n"
                f"• *Members:* {cnt}\n"
                f"• *Bot Active:* {'✅ Yes' if cid in active_groups and active_groups[cid] else '❌ No'}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💎 _AVANTIKA AI — Premium Bot_",
                parse_mode="Markdown"
            )
        except: pass

# ================== GROUP FEATURES ==================
async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *Sirf Group Admin set kar sakta hai!* 👑", parse_mode="Markdown"); return
    except: return
    if not context.args: await update.message.reply_text("📝 */setrules your rules here*", parse_mode="Markdown"); return
    group_rules[cid] = " ".join(context.args)
    await update.message.reply_text(
        f"📜 *GROUP RULES UPDATED!* ✅\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{group_rules[cid]}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚡ _Sabko rules follow karne honge!_",
        parse_mode="Markdown"
    )

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_rules:
        await update.message.reply_text(
            f"📜 *GROUP RULES* 👑\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{group_rules[cid]}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚡ _Rules follow karo, warna warning milegi!_",
            parse_mode="Markdown"
        )
    else: await update.message.reply_text("📜 _Koi rules set nahi hai!_ */setrules* se add karo.", parse_mode="Markdown")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if not update.message.reply_to_message: await update.message.reply_text("⚠️ _Kisi message pe reply karo warn karne ke liye!_"); return
    target = update.message.reply_to_message.from_user
    if target.id == update.effective_user.id: return
    if cid not in group_warnings: group_warnings[cid] = {}
    if target.id not in group_warnings[cid]: group_warnings[cid][target.id] = 0
    group_warnings[cid][target.id] += 1
    wc = group_warnings[cid][target.id]
    await update.message.reply_text(
        f"⚠️ *WARNING ISSUED!* ⚡\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *User:* {target.first_name}\n"
        f"📊 *Warnings:* {wc}/3\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{'🔴 *3 Warnings! Ab mute karo!*' if wc>=3 else '⚡ _Sudhar jao, rules follow karo!_'}",
        parse_mode="Markdown"
    )

async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if cid in group_warnings and target.id in group_warnings[cid]:
            group_warnings[cid][target.id] = 0
            await update.message.reply_text(f"✅ *{target.first_name} ke warnings clear ho gaye!*", parse_mode="Markdown")
    else:
        group_warnings[cid] = {}
        await update.message.reply_text("✅ *Sabke warnings clear ho gaye!* 🧹", parse_mode="Markdown")

# ================== WELCOME ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            await context.bot.send_message(cid,
                "✨ *AVANTIKA AI — JOINED THE GROUP!* ✨\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "👑 _Admin use_ */activate* _to start_\n"
                "📢 _Then everyone gets_ *PREMIUM REPLIES!*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💻 *Coding Master* | 📚 *Knowledge Bank* | 😂 *Fun & Jokes*\n"
                "🔇 *Mute System* | ⚠️ *Warning System* | 📜 *Rules* | 📝 *Notes* | 📌 *Pin*\n\n"
                "🔥 _Activate karo aur dhamaka karo!_",
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(cid,
                f"✨ *WELCOME TO THE GROUP!* ✨\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *{user.first_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌟 _Aapka bahut bahut swagat hai!_ 🎉\n\n"
                f"💎 *Yahaan aapko milega:*\n"
                f"• *Premium AI Replies* — Kuch bhi puchho! 🔥\n"
                f"• *Coding Help* — Complete working code 💻\n"
                f"• *Knowledge* — Science, GK, Tech, sab kuch 📚\n"
                f"• *Mute System* — Rules todne walo ki chhutti 🔇\n"
                f"• *Notes & Pin* — Important cheeze save karo 📝\n\n"
                f"📢 _Bas apna question type karo, AVANTIKA jawab degi!_ 💬\n\n"
                f"🔰 _Group mein enjoy karo!_ 🤗",
                parse_mode="Markdown"
            )

# ================== MUTE SYSTEM ==================
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ *Sirf group mein chalta hai!*", parse_mode="Markdown"); return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *Sirf Group Admin mute kar sakta hai!* 👑", parse_mode="Markdown"); return
    except: await update.message.reply_text("❌ *Bot ko Admin banao pehle!*", parse_mode="Markdown"); return
    
    target, ts = None, "1h"
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if context.args: ts = " ".join(context.args)
    elif context.args and len(context.args)>=2:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user; ts = " ".join(context.args[1:])
        except: return
    else:
        await update.message.reply_text(
            "🔇 *MUTE SYSTEM — USAGE* 🇮🇳\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 *Reply karke:* `/mute 10 second` | `/mute 5 minute`\n"
            "📌 *Reply karke:* `/mute 2 hour` | `/mute 1 day`\n\n"
            "📌 *Short format:* `/mute 25s` | `5m` | `2h` | `1d` | `30d`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🇮🇳 *IST Timezone* | ⏰ *Auto Unmute ON*\n"
            "🔊 `/unmute` reply karke manual unmute",
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
        an = update.effective_user.first_name or "Admin"
        
        await update.message.reply_text(
            f"🔇 *USER MUTED! — INDIA TIME* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {tn}\n"
            f"🆔 *ID:* `{target.id}`\n"
            f"👑 *Muted By:* {an}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ *Duration:* {format_time(mm)}\n\n"
            f"📅 *Muted At:*\n"
            f"   🕐 `{nw.strftime('%I:%M:%S %p')}` — {nw.strftime('%d %B %Y')}\n\n"
            f"🔓 *Will Unmute At:*\n"
            f"   🕐 `{ut.strftime('%I:%M:%S %p')}` — {ut.strftime('%d %B %Y')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ *Auto Unmute ON* — Time khatam hone par apne aap khulega!\n"
            f"🔊 Ya `/unmute` reply karke manual unmute karo",
            parse_mode="Markdown"
        )
        
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await context.bot.send_message(cid,
                    f"✅ *AUTO UNMUTED!* 🇮🇳\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 *{tn}*\n"
                    f"⏱️ _Mute duration khatam!_ ({format_time(mm)})\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💬 _Ab message kar sakta hai!_ 🎉",
                    parse_mode="Markdown"
                )
            except: pass
        asyncio.create_task(auto())
    except Exception as e:
        await update.message.reply_text(f"❌ *Mute failed!*\n_Bot ko Ban Users permission do!_", parse_mode="Markdown")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not target and context.args:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user
        except: return
    if not target: await update.message.reply_text("🔊 _Reply karke `/unmute` bhejo!_", parse_mode="Markdown"); return
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        nw = get_ist_now()
        await update.message.reply_text(
            f"✅ *USER UNMUTED!* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {target.first_name}\n"
            f"🔓 *Unmuted At:* `{nw.strftime('%I:%M:%S %p, %d %B %Y')}`\n"
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
                "👑 *WELCOME BACK, BOSS!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 *AVANTIKA AI — WORLD'S #1 BOT*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ *Premium AI Replies* (Detailed + Bold + Italic)\n"
                "✅ *All Languages Support* 🌍\n"
                "✅ *Coding Master* 💻\n"
                "✅ *Knowledge Bank* 📚\n"
                "✅ *Fun & Jokes* 😂\n"
                "✅ *Mute System* 🔇\n"
                "✅ *Auto Unmute* ⏰\n"
                "✅ *Warning System* ⚠️\n"
                "✅ *Group Rules* 📜\n"
                "✅ *Notes System* 📝\n"
                "✅ *Pin Messages* 📌\n"
                "✅ *Welcome System* 👋\n"
                "✅ *User Management* 👥\n"
                "✅ *Broadcast* 📢\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "⚡ *BOSS COMMANDS:*\n"
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
            await update.message.reply_text(
                "✅ *Access Granted!* 💎\n\n"
                "💬 _Kuch bhi puchho — AVANTIKA jawab degi!_\n\n"
                "/start | /clear | /id | /info",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🔒 *ACCESS DENIED!* 🔒\n\n"
                "_Aapke paas bot use karne ki permission nahi hai._\n"
                "_Owner se contact karein for access._",
                parse_mode="Markdown"
            )
    else:
        user_history[cid] = []
        await update.message.reply_text(
            "👋 *AVANTIKA AI — WORLD'S #1 BOT* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 _Admin_ */activate* _karo_\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔇 `/mute` | 🔊 `/unmute` | ⚠️ `/warn`\n"
            "📜 `/rules` | 📝 `/notes` | 📌 `/pin`\n"
            "🆔 `/id` | ℹ️ `/info`\n\n"
            "_Activate karo aur dhamaka karo!_ 🔥",
            parse_mode="Markdown"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ *Sirf GROUP mein chalta hai!*", parse_mode="Markdown"); return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text(
                "❌ *ADMIN ONLY!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 *STEPS TO ACTIVATE:*\n"
                "1️⃣ Bot ko *ADMIN* banao\n"
                "2️⃣ Sab *permissions ON* karo\n"
                "3️⃣ Phir `/activate` bhejo\n"
                "━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode="Markdown"
            ); return
    except: await update.message.reply_text("❌ *Bot ko ADMIN banao pehle!*", parse_mode="Markdown"); return
    
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text(
        "✅ *GROUP ACTIVATED!* 🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *ALL SYSTEMS ONLINE:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 *Premium AI Replies*\n"
        "🔇 *Mute System*\n"
        "⏰ *Auto Unmute*\n"
        "⚠️ *Warning System*\n"
        "📜 *Group Rules*\n"
        "📝 *Notes*\n"
        "📌 *Pin*\n"
        "👋 *Welcome*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📢 _Sab kuch puchho — AVANTIKA jawab degi!_ 💎\n\n"
        "❌ /deactivate — Band karo",
        parse_mode="Markdown"
    )

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *GROUP DEACTIVATED!* `/activate` se wapas on karo.", parse_mode="Markdown")

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
        "💭 *Chat Memory* — Cleared ✅\n"
        "⚠️ *Warnings* — Cleared ✅\n"
        "📜 *Rules* — Cleared ✅\n"
        "📝 *Notes* — Cleared ✅\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🆕 _Bilkul fresh start! Naye conversation!_ 💎",
        parse_mode="Markdown"
    )

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    
    if msg.new_chat_members: await welcome(update, context); return
    if ct == ChatType.PRIVATE and not is_allowed(uid): await msg.reply_text("🔒 *Permission nahi hai!*\n\n_Owner se contact karein._", parse_mode="Markdown"); return
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
        ("mutelist",lambda u,c: u.message.reply_text(
            "🔇 *MUTE SYSTEM HELP* 🇮🇳\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📌 `/mute 10s` `/mute 5m` `/mute 2h` `/mute 1d` `/mute 30d`\n"
            "🔊 `/unmute` reply karke\n"
            "⏰ Auto Unmute ON\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )),
        ("warn",warn),("clearwarns",clearwarns),("setrules",setrules),("rules",rules),
        ("addnote",addnote),("notes",notes),("clearnotes",clearnotes),
        ("pin",pin),("unpin",unpin),("info",info),
        ("adduser",adduser),("removeuser",removeuser),("userlist",userlist),
        ("broadcast",broadcast),("id",get_id)
    ]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(MessageHandler(filters.ALL,handle_message))
    print("👑 AVANTIKA AI — ULTIMATE PREMIUM BOT READY!")
    print(f"👑 Owner ID: {OWNER_USER_ID}")
    print("✅ All Features | Premium Text | Full Detailed Replies")
    app.run_polling()

if __name__ == "__main__": main()
