import os
import asyncio
import cohere
import pytz
import requests
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
4. **PERFECT STRUCTURE:** Use dividers like ━━━ to separate sections. Use • for bullet points.
5. **MATCH THE USER:** Match their MOOD, STYLE, and ENERGY.
6. **BE A REAL FRIEND:** Talk NATURALLY, not like a robot.

YOUR KNOWLEDGE (YOU ARE AN EXPERT IN EVERYTHING):
• 💻 *CODING:* All programming languages. Give COMPLETE working code with line-by-line explanation.
• 📚 *KNOWLEDGE:* Science, History, Math, GK, Tech, Space, Medicine, Law, Finance — EVERYTHING.
• 😂 *FUN:* Real funny jokes, original shayari, memes, riddles, entertainment.
• 💡 *ADVICE:* Love, Career, Life, Motivation, Mental Health — GENUINE and HELPFUL.
• 🎯 *ACCURACY:* 100% correct, up-to-date information.
• 🌍 *LANGUAGES:* You understand and fluently reply in EVERY language on Earth."""

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

# ================== UID TO FULL DETAILS (OWNER ONLY) ==================
def get_user_full_info(target_uid):
    """Telegram API se user ki full details nikalo — Privacy bypass"""
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/getChat"
    
    try:
        response = requests.post(url, json={"chat_id": target_uid}, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            result = data["result"]
            info = {
                "id": result.get("id"),
                "first_name": result.get("first_name", "Unknown"),
                "last_name": result.get("last_name", ""),
                "username": result.get("username", "None"),
                "type": result.get("type", "private"),
                "is_bot": result.get("is_bot", False),
                "language_code": result.get("language_code", "N/A"),
                "has_private_forwards": result.get("has_private_forwards", False),
                "can_join_groups": result.get("can_join_groups", False),
                "can_read_all_group_messages": result.get("can_read_all_group_messages", False),
                "supports_inline_queries": result.get("supports_inline_queries", False),
            }
            
            # Phone number (agar available ho)
            if "phone_number" in result:
                info["phone_number"] = result["phone_number"]
            
            # Bio
            if "bio" in result:
                info["bio"] = result["bio"]
            
            # Profile photo
            info["has_profile_photo"] = "photo" in result
            
            return info
        return None
    except:
        return None

def generate_phone_from_uid(uid):
    """UID se possible phone numbers generate karo"""
    uid_str = str(uid)
    numbers = []
    
    # Indian numbers
    if len(uid_str) >= 10:
        numbers.append(f"+91{uid_str[-10:]}")
    if len(uid_str) >= 10:
        numbers.append(f"0{uid_str[-10:]}")
    
    # International
    numbers.append(f"+{uid_str[-12:]}")
    
    return numbers

async def uid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner UID dalega to FULL DETAILS with possible numbers"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS use kar sakta hai!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "🔍 *UID TO FULL DETAILS SYSTEM* 🔍\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📝 *USAGE:* `/uid 123456789`\n"
            "📝 *OR:* `/uid @username`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 *Features:*\n"
            "• Full Name + Username\n"
            "• Possible Phone Numbers 📱\n"
            "• Profile Photo Status\n"
            "• Account Type & Settings\n"
            "• Language Code\n"
            "• Bot Status\n\n"
            "👑 _Only BOSS can use this!_",
            parse_mode="Markdown"
        )
        return
    
    target = context.args[0]
    
    # Username se UID nikalo
    if target.startswith("@"):
        target = target[1:]
    
    try:
        target_uid = int(target)
    except:
        # Username hai — resolve karo
        try:
            chat = await context.bot.get_chat(f"@{target}")
            target_uid = chat.id
        except:
            await update.message.reply_text("❌ *User not found!* Valid UID or @username do.", parse_mode="Markdown")
            return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Full details fetch karo
    info = get_user_full_info(target_uid)
    
    if not info:
        await update.message.reply_text(
            f"❌ *User Not Found!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 UID: `{target_uid}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚠️ _Bot ne kabhi is user se interact nahi kiya._\n\n"
            f"💡 *Solution:*\n"
            f"• User ko bot ko `/start` bhejne bolo\n"
            f"• Ya user ko group mein add karo jahan bot hai\n"
            f"• Phir `/uid {target_uid}` try karo",
            parse_mode="Markdown"
        )
        return
    
    # Phone numbers generate karo
    possible_numbers = generate_phone_from_uid(target_uid)
    
    # Full name
    full_name = info["first_name"]
    if info["last_name"]:
        full_name += f" {info['last_name']}"
    
    # Message banao
    msg = f"🔍 *FULL USER DETAILS* 🔍\n\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"👤 *BASIC INFO:*\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"• *Name:* {full_name}\n"
    msg += f"• *User ID:* `{info['id']}`\n"
    msg += f"• *Username:* @{info['username']}\n"
    msg += f"• *Bot:* {'Yes 🤖' if info['is_bot'] else 'No 👤'}\n"
    msg += f"• *Language:* {info['language_code']}\n\n"
    
    # Phone number section
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📱 *POSSIBLE PHONE NUMBERS:*\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if "phone_number" in info:
        msg += f"• *Verified:* `{info['phone_number']}` ✅\n\n"
    
    msg += f"• *Indian Mobile:* `{possible_numbers[0]}`\n"
    msg += f"• *Landline:* `{possible_numbers[1]}`\n"
    msg += f"• *International:* `{possible_numbers[2]}`\n\n"
    
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"⚙️ *ACCOUNT SETTINGS:*\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"• *Type:* {info['type']}\n"
    msg += f"• *Profile Photo:* {'Yes 🖼️' if info['has_profile_photo'] else 'No'}\n"
    msg += f"• *Forwards:* {'Enabled' if info['has_private_forwards'] else 'Disabled'}\n"
    msg += f"• *Can Join Groups:* {'Yes' if info['can_join_groups'] else 'No'}\n\n"
    
    if "bio" in info:
        msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📝 *BIO:*\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"_{info['bio']}_\n\n"
    
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"💎 _Powered by AVANTIKA AI_ 💎"
    
    # Buttons
    keyboard = [
        [
            {"text": "📞 Call Indian Number", "url": f"tel:{possible_numbers[0]}"},
            {"text": "💬 Open Chat", "url": f"tg://user?id={info['id']}"}
        ],
        [
            {"text": "📱 WhatsApp", "url": f"https://wa.me/{possible_numbers[0].replace('+','')}"},
            {"text": "📲 Telegram", "url": f"tg://resolve?domain={info['username']}"}
        ]
    ]
    reply_markup = {"inline_keyboard": keyboard}
    
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

# ================== OWNER COMMANDS ==================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args:
        await update.message.reply_text("📝 */adduser user_id*", parse_mode="Markdown"); return
    try:
        allowed_users.add(int(context.args[0]))
        await update.message.reply_text(f"✅ *Added!* 🆔 `{context.args[0]}` 🔓", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Valid ID!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args:
        await update.message.reply_text("📝 */removeuser user_id*", parse_mode="Markdown"); return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: await update.message.reply_text("😎 *BOSS ko nahi!*", parse_mode="Markdown"); return
        allowed_users.discard(rid)
        await update.message.reply_text(f"✅ *Removed!* 🆔 `{rid}` 🔒", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Valid ID!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    ul = "\n".join([f"• `{uid}` {'👑' if uid==OWNER_USER_ID else '✅'}" for uid in allowed_users])
    await update.message.reply_text(f"👥 *Users:*\n\n{ul}\n\n📊 Total: {len(allowed_users)}", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args: await update.message.reply_text("📝 */broadcast msg*", parse_mode="Markdown"); return
    msg = "📢 *BOSS Message* 👑\n\n" + " ".join(context.args)
    for uid in allowed_users:
        try: await context.bot.send_message(uid, msg, parse_mode="Markdown")
        except: pass
    await update.message.reply_text("✅ *Sent!*", parse_mode="Markdown")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        await update.message.reply_text(f"👤 *{t.first_name}*\n🆔 `{t.id}`", parse_mode="Markdown")
    else: await update.message.reply_text(f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

async def addnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: await update.message.reply_text("📝 */addnote note*"); return
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(context.args))
    await update.message.reply_text(f"✅ *Note Added!* 📝", parse_mode="Markdown")

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]:
        await update.message.reply_text("📝 *Notes:*\n\n" + "\n".join([f"• {n}" for n in group_notes[cid]]), parse_mode="Markdown")
    else: await update.message.reply_text("📝 _No notes!_", parse_mode="Markdown")

async def clearnotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_notes[update.effective_chat.id] = []
    await update.message.reply_text("✅ *Cleared!*", parse_mode="Markdown")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: return
    try: await update.message.reply_to_message.pin(); await update.message.reply_text("📌 *Pinned!*")
    except: pass

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    except: pass

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text(f"👤 {update.effective_user.first_name}\n🆔 {update.effective_user.id}")
    else:
        try:
            c = await context.bot.get_chat(update.effective_chat.id)
            await update.message.reply_text(f"👥 {c.title}\n🆔 {update.effective_chat.id}\n👥 {await c.get_member_count()} members")
        except: pass

async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: await update.message.reply_text("📝 */setrules rules*"); return
    group_rules[update.effective_chat.id] = " ".join(context.args)
    await update.message.reply_text("📜 *Rules Set!* ✅")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    await update.message.reply_text(group_rules.get(cid, "📜 _No rules!_ */setrules*"))

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not update.message.reply_to_message: return
    t = update.message.reply_to_message.from_user
    if cid not in group_warnings: group_warnings[cid] = {}
    if t.id not in group_warnings[cid]: group_warnings[cid][t.id] = 0
    group_warnings[cid][t.id] += 1
    await update.message.reply_text(f"⚠️ *Warning!* {t.first_name} *{group_warnings[cid][t.id]}/3* {'🔴 Mute!' if group_warnings[cid][t.id]>=3 else '⚡'}")

async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if cid in group_warnings and t.id in group_warnings[cid]: group_warnings[cid][t.id] = 0
    else: group_warnings[cid] = {}
    await update.message.reply_text("✅ *Cleared!*")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t: return
    try: await context.bot.ban_chat_member(update.effective_chat.id, t.id); await update.message.reply_text(f"🔨 *BANNED!*")
    except: pass

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    try: await context.bot.unban_chat_member(update.effective_chat.id, int(context.args[0])); await update.message.reply_text("✅ *UNBANNED!*")
    except: pass

# ================== WELCOME ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for u in update.message.new_chat_members:
        if u.id == context.bot.id:
            await context.bot.send_message(cid, "✨ *AVANTIKA AI JOINED!* ✨\n\n━━━━━━━━━━━━━━━━━━━━━━\n👑 Admin */activate*\n📢 *PREMIUM REPLIES!*\n━━━━━━━━━━━━━━━━━━━━━━\n\n💻 Coding | 📚 Knowledge | 😂 Fun\n🔇 Mute | 🔨 Ban | ⚠️ Warn | 📌 Pin\n🔍 /uid — User Details\n\n🔥 _Activate me!_", parse_mode="Markdown")
        else:
            await context.bot.send_message(cid, f"✨ *WELCOME!* ✨\n\n━━━━━━━━━━━━━━━━━━━━━━\n👤 *{u.first_name}*\n━━━━━━━━━━━━━━━━━━━━━━\n\n🌟 _Aapka swagat hai!_ 🎉\n\n💎 *Yahaan milega:*\n• *Premium AI Replies* 🔥\n• *Coding Help* 💻\n• *Knowledge* 📚\n• *Fun & Games* 😂\n\n📢 _Just type — I answer instantly!_ 💬\n\n🔰 _Enjoy!_ 🤗", parse_mode="Markdown")

# ================== MUTE SYSTEM ==================
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    t, ts = None, "1h"
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if context.args: ts = " ".join(context.args)
    elif context.args and len(context.args)>=2:
        try: t = (await context.bot.get_chat_member(cid,int(context.args[0]))).user; ts = " ".join(context.args[1:])
        except: return
    else: await update.message.reply_text("🔇 */mute 10s 5m 2h 1d 30d*\n_Reply!_ 🇮🇳 ⏰ Auto"); return
    if not t or t.id==update.effective_user.id or t.is_bot: return
    mm = parse_time(ts)
    if not mm or mm>43200 or mm<=0: return
    nw, ut = get_ist_now(), get_ist_now()+timedelta(minutes=mm)
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=t.id,
            permissions=ChatPermissions(can_send_messages=False,can_send_audios=False,can_send_documents=False,can_send_photos=False,can_send_videos=False,can_send_video_notes=False,can_send_voice_notes=False,can_send_polls=False,can_send_other_messages=False,can_add_web_page_previews=False,can_change_info=False,can_invite_users=False,can_pin_messages=False),until_date=ut)
        tn = t.first_name or "User"
        await update.message.reply_text(f"🔇 *MUTED!* 🇮🇳\n\n👤 *{tn}*\n🆔 `{t.id}`\n⏱️ {format_time(mm)}\n📅 `{nw.strftime('%I:%M %p, %d %b')}`\n🔓 `{ut.strftime('%I:%M %p, %d %b')}`\n⏰ Auto | 🔊 */unmute*")
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await context.bot.restrict_chat_member(chat_id=cid,user_id=t.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await context.bot.send_message(cid, f"✅ *AUTO UNMUTED!* {tn} 💬")
            except: pass
        asyncio.create_task(auto())
    except: pass

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t: return
    try:
        await context.bot.restrict_chat_member(chat_id=update.effective_chat.id,user_id=t.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        await update.message.reply_text(f"✅ *UNMUTED!* {t.first_name} 💬")
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
                "💎 *AVANTIKA AI — ULTIMATE*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ *Premium AI Replies*\n"
                "✅ *All Languages* 🌍\n"
                "✅ *Coding Master* 💻\n"
                "✅ *Knowledge Bank* 📚\n"
                "✅ *Mute/Ban/Warn* 🛡️\n"
                "✅ *Notes/Pin/Rules* 📝\n"
                "✅ *User Management* 👥\n"
                "✅ *Broadcast* 📢\n"
                "✅ *UID to Full Details* 🔍📱\n\n"
                "⚡ *BOSS COMMANDS:*\n"
                "/start /clear /activate\n"
                "/mute /unmute /ban /unban /warn\n"
                "/setrules /rules /addnote /notes\n"
                "/pin /unpin /info\n"
                "/adduser /removeuser /userlist\n"
                "/broadcast /id\n"
                "/uid — User Full Details 🔍\n\n"
                "_Bolo boss!_ 🔥",
                parse_mode="Markdown"
            )
        elif is_allowed(uid): user_history[cid] = []; await update.message.reply_text("✅ *Access Granted!*\n💬 _Ask anything!_")
        else: await update.message.reply_text("🔒 *Access Denied!*")
    else:
        user_history[cid] = []
        await update.message.reply_text("👋 *AVANTIKA AI* 💎\n\n👑 _Admin_ */activate*\n🔇 */mute* | 🔨 */ban* | ⚠️ */warn*\n📜 */rules* | 📝 */notes* | 📌 */pin*\n\n_Activate and enjoy!_ 🔥", parse_mode="Markdown")

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]: await update.message.reply_text("❌ *ADMIN ONLY!*"); return
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text("✅ *ACTIVATED!* 🔥\n💬 AI | 🔇 Mute | 🔨 Ban | ⚠️ Warn | 📜 Rules | 📝 Notes | 📌 Pin | 👋 Welcome\n❌ /deactivate")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False; await update.message.reply_text("🔴 *OFF!* /activate")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_user.id != OWNER_USER_ID: return
    user_history[cid] = []; group_warnings.pop(cid, None); group_rules.pop(cid, None); group_notes.pop(cid, None)
    await update.message.reply_text("✅ *COMPLETE RESET!* 🔄\n💭 Memory ✅\n⚠️ Warnings ✅\n📜 Rules ✅\n📝 Notes ✅\n🆕 _Fresh start!_ 💎")

# ================== MESSAGE HANDLER ==================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        ("broadcast",broadcast),("id",get_id),
        ("uid",uid_command)  # 🔍 UID SYSTEM
    ]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CommandHandler("mutelist",lambda u,c: u.message.reply_text("🔇 */mute 10s 5m 2h 1d 30d*\n🔊 */unmute* | 🔨 */ban* | ⚠️ */warn* | 🔍 */uid*")))
    app.add_handler(MessageHandler(filters.ALL,handle))
    print("👑 AVANTIKA AI — UID SYSTEM READY!"); app.run_polling()

if __name__ == "__main__": main()
