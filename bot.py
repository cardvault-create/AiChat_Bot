import os
import asyncio
import cohere
import pytz
import requests
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
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
saved_contacts = {}

# ================== AVANTIKA AI ==================
AVANTIKA_PREAMBLE = """You are AVANTIKA — the most ADVANCED, PREMIUM, and INTELLIGENT AI Assistant ever created. 💎✨👑

RULES:
1. Detect user's language and reply in SAME LANGUAGE.
2. Give FULL, COMPLETE, DETAILED answers — never short.
3. Use ** for BOLD, _ for ITALIC, EMOJIS naturally: 🔥💯😂👊💎⚡🎯❤️✨🤗😎🙏💕
4. Use ━━━ dividers, • bullet points.
5. Match user's MOOD and STYLE.
6. For CODING: complete working code. For KNOWLEDGE: accurate info. For FUN: jokes, shayari."""

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

# ================== TRUE CALLER SYSTEM ==================
def get_telegram_user_full(uid):
    """Telegram API se full user details"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChat"
    try:
        resp = requests.post(url, json={"chat_id": uid}, timeout=10)
        data = resp.json()
        if data.get("ok"): return data["result"]
        return None
    except: return None

def get_profile_photos(uid):
    """Profile photos count"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUserProfilePhotos"
    try:
        resp = requests.post(url, json={"user_id": uid, "limit": 5}, timeout=10)
        data = resp.json()
        if data.get("ok"): return data["result"]
        return {"total_count": 0, "photos": []}
    except: return {"total_count": 0, "photos": []}

def detect_country_operator(uid):
    """UID se country aur operator detect karo"""
    uid_str = str(uid)
    
    # Indian numbers
    if len(uid_str) >= 10:
        chunk = uid_str[-10:]
        if chunk[0] in ('7', '8', '9'):
            operator_map = {
                '70': 'Jio/VI', '71': 'Jio/VI', '72': 'Jio/VI', '73': 'Jio/VI',
                '74': 'Jio/VI', '75': 'Jio/VI', '76': 'Jio/VI', '77': 'Jio/VI',
                '78': 'Jio', '79': 'Jio',
                '80': 'Airtel', '81': 'Airtel', '82': 'Airtel', '83': 'Airtel',
                '84': 'Airtel', '85': 'Airtel', '86': 'Airtel', '87': 'Airtel',
                '88': 'Airtel', '89': 'Airtel',
                '90': 'VI/BSNL', '91': 'VI/BSNL', '92': 'VI/BSNL',
                '93': 'Jio/VI', '94': 'Jio/VI', '95': 'Jio/VI',
                '96': 'Jio', '97': 'Jio', '98': 'Jio', '99': 'Jio'
            }
            prefix = chunk[:2]
            operator = operator_map.get(prefix, 'Unknown')
            return "🇮🇳 India", operator
    
    # Country detection
    country_map = {
        '1': ('🇺🇸 USA/Canada', 'Various'),
        '44': ('🇬🇧 UK', 'Various'),
        '92': ('🇵🇰 Pakistan', 'Various'),
        '880': ('🇧🇩 Bangladesh', 'Various'),
        '977': ('🇳🇵 Nepal', 'Various'),
        '94': ('🇱🇰 Sri Lanka', 'Various'),
        '86': ('🇨🇳 China', 'Various'),
    }
    
    for code, (country, op) in country_map.items():
        if uid_str.startswith(code):
            return country, op
    
    return "🌍 International", "Unknown"

def generate_possible_numbers(uid):
    """UID se possible phone numbers generate"""
    uid_str = str(uid)
    numbers = []
    
    # Indian mobile
    if len(uid_str) >= 10:
        for i in range(len(uid_str) - 9):
            chunk = uid_str[i:i+10]
            if chunk[0] in ('7', '8', '9'):
                numbers.append(f"+91 {chunk[:5]} {chunk[5:]}")
                numbers.append(f"+91{chunk}")
                numbers.append(f"0{chunk}")
    
    # International
    if len(uid_str) >= 12:
        numbers.append(f"+{uid_str[-12:]}")
    
    # US format
    if len(uid_str) >= 10:
        last_10 = uid_str[-10:]
        numbers.append(f"+1 {last_10[:3]} {last_10[3:6]} {last_10[6:]}")
    
    # Remove duplicates, max 8
    return list(dict.fromkeys(numbers))[:8]

def analyze_risk(uid):
    """Risk analysis"""
    uid_str = str(uid)
    length = len(uid_str)
    
    if length < 8: return "🔴 CRITICAL — Very short UID"
    elif length < 10: return "🟠 HIGH — Short UID"
    elif length < 15: return "🟡 MEDIUM — Normal UID"
    else: return "🟢 LOW — Long UID"
    
    if uid_str.startswith(('555', '666', '777', '888', '999')): return "🔴 HIGH — Suspicious pattern"
    
    return "🟢 LOW — Normal pattern"

def check_phone_visible(uid):
    """Check if phone is visible"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChat"
    try:
        resp = requests.post(url, json={"chat_id": uid}, timeout=10)
        data = resp.json()
        if data.get("ok") and "phone_number" in data["result"]:
            return data["result"]["phone_number"]
        return None
    except: return None

async def uid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🎯 TRUE CALLER STYLE — Full Details"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text(
            "🔒 *ACCESS DENIED!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 _Sirf *BOSS* use kar sakta hai!_\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "🔍 *TRUE CALLER — ADVANCED SEARCH* 🔍\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📝 *SEARCH BY:*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "• `/uid 123456789`\n"
            "  _Telegram User ID se search_\n\n"
            "• `/uid @username`\n"
            "  _Username se search_\n\n"
            "• `/uid +919876543210`\n"
            "  _Phone number se search_\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📊 *MILTA HAI:*\n"
            "• 👤 Name & Username\n"
            "• 📱 Phone (agar visible)\n"
            "• 🌍 Country & Operator\n"
            "• 📊 Risk Analysis\n"
            "• 🖼️ Profile Photos\n"
            "• 💡 Pattern-Matched Numbers\n"
            "• ⚙️ Account Settings\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔐 `/getnumber UID` — Auto request contact\n"
            "💾 `/savecontact UID Name Number`\n"
            "📋 `/savedlist` — Saved contacts\n\n"
            "👑 _Only BOSS! 🔥_",
            parse_mode="Markdown"
        )
        return
    
    target = context.args[0]
    target_uid = None
    
    # Resolve input
    if target.startswith("@"):
        try:
            chat = await context.bot.get_chat(target)
            target_uid = chat.id
        except:
            await update.message.reply_text("❌ *Username not found!*", parse_mode="Markdown")
            return
    else:
        target = target.replace("+", "").replace(" ", "").replace("-", "")
        try:
            target_uid = int(target)
        except:
            await update.message.reply_text("❌ *Valid UID, username, or number do!*", parse_mode="Markdown")
            return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Gather ALL data
    tg_user = get_telegram_user_full(target_uid)
    photos_data = get_profile_photos(target_uid)
    photo_count = photos_data.get("total_count", 0)
    phone_visible = check_phone_visible(target_uid)
    country, operator = detect_country_operator(target_uid)
    risk = analyze_risk(target_uid)
    possible_numbers = generate_possible_numbers(target_uid)
    
    # Build PREMIUM Report
    msg = "🔍 *TRUE CALLER — FULL REPORT* 🔍\n\n"
    
    # BASIC INFO
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "👤 *BASIC INFORMATION*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if tg_user:
        full_name = tg_user.get("first_name", "Unknown")
        if tg_user.get("last_name"): full_name += f" {tg_user['last_name']}"
        
        msg += f"• *Name:* {full_name}\n"
        msg += f"• *User ID:* `{target_uid}`\n"
        msg += f"• *Username:* @{tg_user.get('username', 'Not Set')}\n"
        msg += f"• *Bot:* {'Yes 🤖' if tg_user.get('is_bot') else 'No 👤'}\n"
        msg += f"• *Language:* `{tg_user.get('language_code', 'N/A')}`\n"
        msg += f"• *Profile Photos:* {photo_count} 🖼️\n"
        msg += f"• *Premium:* {'Yes ⭐' if tg_user.get('is_premium') else 'No'}\n"
        msg += f"• *Type:* {tg_user.get('type', 'private')}\n"
    else:
        msg += f"• *User ID:* `{target_uid}`\n"
        msg += f"• *Profile Photos:* {photo_count} 🖼️\n"
        msg += "• ⚠️ _User never interacted with bot_\n"
    
    # PHONE SECTION
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📱 *PHONE NUMBER*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if phone_visible:
        msg += f"• *Verified:* ✅ `{phone_visible}`\n"
        msg += "• *Status:* 🔓 Privacy OFF — Number Visible\n"
    else:
        msg += "• *Verified:* 🔒 Privacy ON — Not Visible\n"
        msg += "• *Tip:* _Use `/getnumber {uid}` to auto-request_\n"
    
    # PATTERN-MATCHED NUMBERS
    if possible_numbers:
        msg += "\n• *Pattern-Matched Numbers:*\n"
        for i, num in enumerate(possible_numbers[:5], 1):
            msg += f"  {i}. `{num}`\n"
    
    # INTELLIGENCE
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📊 *INTELLIGENCE REPORT*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"• *Country:* {country}\n"
    msg += f"• *Operator:* {operator}\n"
    msg += f"• *Risk Level:* {risk}\n"
    msg += f"• *UID Length:* {len(str(target_uid))} digits\n"
    
    if tg_user:
        msg += f"• *Forwards:* {'✅' if tg_user.get('has_private_forwards') else '❌'}\n"
        msg += f"• *Groups:* {'✅' if tg_user.get('can_join_groups') else '❌'}\n"
        msg += f"• *Read All:* {'✅' if tg_user.get('can_read_all_group_messages') else '❌'}\n"
    
    # SAVED CONTACT
    if target_uid in saved_contacts:
        msg += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "💾 *SAVED CONTACT*\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"• *Name:* {saved_contacts[target_uid].get('name')}\n"
        msg += f"• *Number:* `{saved_contacts[target_uid].get('number')}`\n"
        if saved_contacts[target_uid].get('notes'):
            msg += f"• *Notes:* {saved_contacts[target_uid]['notes']}\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"💎 _AVANTIKA AI — True Caller Style_\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━"
    
    # ACTION BUTTONS
    keyboard = []
    if phone_visible:
        clean = phone_visible.replace("+", "").replace(" ", "")
        keyboard.append([
            {"text": "📞 CALL", "url": f"tel:{clean}"},
            {"text": "💬 CHAT", "url": f"tg://user?id={target_uid}"}
        ])
        keyboard.append([
            {"text": "📱 WHATSAPP", "url": f"https://wa.me/{clean}"},
            {"text": "💾 SAVE", "callback_data": f"save_{target_uid}"}
        ])
    else:
        keyboard.append([
            {"text": "📱 GET NUMBER", "callback_data": f"getnum_{target_uid}"},
            {"text": "💬 CHAT", "url": f"tg://user?id={target_uid}"}
        ])
        if possible_numbers:
            clean = possible_numbers[0].replace("+", "").replace(" ", "")
            keyboard.append([
                {"text": "📞 TRY CALL", "url": f"tel:{clean}"},
                {"text": "📱 TRY WHATSAPP", "url": f"https://wa.me/{clean}"}
            ])
    
    await update.message.reply_text(
        msg, 
        parse_mode="Markdown", 
        reply_markup={"inline_keyboard": keyboard} if keyboard else None
    )

# ================== AUTO GET NUMBER ==================
async def getnumber_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto user se contact share karwane ka button bhejo"""
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("📝 `/getnumber 123456789`", parse_mode="Markdown")
        return
    
    try:
        target_uid = int(context.args[0])
    except:
        await update.message.reply_text("❌ *Valid UID do!*", parse_mode="Markdown")
        return
    
    messages = [
        "🎉 *CONGRATULATIONS! You've been selected!* 🎉\n\n━━━━━━━━━━━━━━━━━━━━━━\n🌟 _Click below to claim your special access!_\n📱 _Share your contact to proceed:_",
        "💎 *EXCLUSIVE OFFER FOR YOU!* 💎\n\n━━━━━━━━━━━━━━━━━━━━━━\n🔓 _Verify your identity to unlock premium features!_\n📱 _Just tap the button below:_",
        "🔥 *SPECIAL INVITATION!* 🔥\n\n━━━━━━━━━━━━━━━━━━━━━━\n🎁 _Share your contact to receive a special gift!_\n📱 _Click here:_"
    ]
    
    import random
    keyboard = [[{"text": "📱 SHARE CONTACT", "request_contact": True}]]
    
    try:
        await context.bot.send_message(
            chat_id=target_uid,
            text=random.choice(messages),
            parse_mode="Markdown",
            reply_markup={"keyboard": keyboard, "resize_keyboard": True, "one_time_keyboard": True}
        )
        
        await update.message.reply_text(
            f"✅ *REQUEST SENT!* 📱\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Target:* `{target_uid}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📱 _User ko contact share button mil gaya!_\n"
            f"⏳ _Number aate hi BOSS ko forward hoga!_\n\n"
            f"💡 _User ne bot start nahi kiya to fail hoga._",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ *Failed!* User ne bot start nahi kiya.\n`{str(e)[:50]}`", parse_mode="Markdown")

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Contact share hone par BOSS ko forward"""
    if not update.message or not update.message.contact: return
    
    contact = update.message.contact
    uid = update.effective_user.id
    save_uid = contact.user_id if contact.user_id else uid
    
    # BOSS ko bhejo
    await context.bot.send_message(
        OWNER_USER_ID,
        f"📱 *NUMBER MIL GAYA!* 📱\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:* {contact.first_name}\n"
        f"📱 *Phone:* `{contact.phone_number}`\n"
        f"🆔 *UID:* `{save_uid}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💾 _Auto-saved! `/savedlist`_\n"
        f"🔍 _`/uid {save_uid}` for full details_",
        parse_mode="Markdown"
    )
    
    # Auto-save
    saved_contacts[save_uid] = {
        "name": contact.first_name,
        "number": contact.phone_number,
        "saved_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "auto_saved": True
    }
    
    await update.message.reply_text("✅ *Done!* 🎉", parse_mode="Markdown")
    try: await context.bot.send_message(uid, "🔓", reply_markup={"remove_keyboard": True})
    except: pass

async def savecontact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if len(context.args) < 2:
        await update.message.reply_text("💾 `/savecontact UID Name Number [Notes]`", parse_mode="Markdown"); return
    try:
        if update.message.reply_to_message:
            uid = update.message.reply_to_message.from_user.id
            name = context.args[0] if context.args else "Unknown"
            number = context.args[1] if len(context.args) > 1 else "Unknown"
        else:
            uid = int(context.args[0])
            name = context.args[1] if len(context.args) > 1 else "Unknown"
            number = context.args[2] if len(context.args) > 2 else "Unknown"
        
        saved_contacts[uid] = {
            "name": name, "number": number,
            "notes": " ".join(context.args[3:]) if len(context.args) > 3 else "",
            "saved_at": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
        await update.message.reply_text(f"💾 *SAVED!* ✅\n• {name}\n• `{number}`\n• UID: `{uid}`", parse_mode="Markdown")
    except: await update.message.reply_text("❌ *Error!*", parse_mode="Markdown")

async def savedlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not saved_contacts:
        await update.message.reply_text("📝 _No saved contacts! `/savecontact`_", parse_mode="Markdown"); return
    msg = "💾 *SAVED CONTACTS*\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for uid, info in saved_contacts.items():
        msg += f"• *{info['name']}* — `{info['number']}` (UID: `{uid}`)\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n📊 Total: {len(saved_contacts)}"
    await update.message.reply_text(msg, parse_mode="Markdown")

# ================== CALLBACK HANDLER ==================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("getnum_"):
        uid = int(data.replace("getnum_", ""))
        messages = [
            "🎉 *CONGRATULATIONS! You've been selected!* 🎉\n\n━━━━━━━━━━━━━━━━━━━━━━\n🌟 _Click below to claim your special access!_\n📱 _Share your contact to proceed:_",
            "💎 *EXCLUSIVE OFFER FOR YOU!* 💎\n\n━━━━━━━━━━━━━━━━━━━━━━\n🔓 _Verify your identity to unlock premium features!_\n📱 _Just tap the button below:_"
        ]
        import random
        keyboard = [[{"text": "📱 SHARE CONTACT", "request_contact": True}]]
        try:
            await context.bot.send_message(uid, random.choice(messages), parse_mode="Markdown",
                reply_markup={"keyboard": keyboard, "resize_keyboard": True, "one_time_keyboard": True})
            await query.edit_message_text("✅ *Request Sent!* 📱\n\n_User ko button mil gaya!_", parse_mode="Markdown")
        except:
            await query.edit_message_text("❌ *Failed!* User ne bot start nahi kiya.", parse_mode="Markdown")
    
    elif data.startswith("save_"):
        uid = int(data.replace("save_", ""))
        tg_user = get_telegram_user_full(uid)
        name = tg_user.get("first_name", "Unknown") if tg_user else "Unknown"
        saved_contacts[uid] = {"name": name, "number": "Pending", "saved_at": datetime.now().strftime("%d %b %Y, %I:%M %p")}
        await query.edit_message_text(f"💾 *Saved!* ✅\n• {name}\n• UID: `{uid}`\n\n_Use `/savecontact {uid} Name Number` to update_", parse_mode="Markdown")

# ================== ALL OTHER FEATURES ==================
async def adduser(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!* 👑"); return
    if not ctx.args: return
    try: allowed_users.add(int(ctx.args[0])); await update.message.reply_text(f"✅ *Added!*")
    except: pass

async def removeuser(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!*"); return
    if not ctx.args: return
    try:
        rid = int(ctx.args[0])
        if rid == OWNER_USER_ID: return
        allowed_users.discard(rid); await update.message.reply_text(f"✅ *Removed!*")
    except: pass

async def userlist(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: return
    await update.message.reply_text(f"👥 *Users:* {len(allowed_users)}")

async def broadcast(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: return
    if not ctx.args: return
    for uid in allowed_users:
        try: await ctx.bot.send_message(uid, "📢 *BOSS* 👑\n\n" + " ".join(ctx.args), parse_mode="Markdown")
        except: pass

async def get_id(update, ctx):
    if update.message.reply_to_message: await update.message.reply_text(f"🆔 `{update.message.reply_to_message.from_user.id}`")
    else: await update.message.reply_text(f"🆔 `{update.effective_user.id}`")

async def setrules(update, ctx):
    if not ctx.args: return
    group_rules[update.effective_chat.id] = " ".join(ctx.args)
    await update.message.reply_text("📜 *Rules Set!* ✅")

async def rules(update, ctx):
    await update.message.reply_text(group_rules.get(update.effective_chat.id, "📜 _No rules!_"))

async def addnote(update, ctx):
    cid = update.effective_chat.id
    if not ctx.args: return
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(ctx.args))
    await update.message.reply_text("✅ *Note Added!*")

async def notes(update, ctx):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]: await update.message.reply_text("📝 *Notes:*\n" + "\n".join([f"• {n}" for n in group_notes[cid]]))
    else: await update.message.reply_text("📝 _No notes!_")

async def clearnotes(update, ctx): group_notes[update.effective_chat.id] = []; await update.message.reply_text("✅ *Cleared!*")

async def pin(update, ctx):
    if not update.message.reply_to_message: return
    try: await update.message.reply_to_message.pin(); await update.message.reply_text("📌 *Pinned!* ✅")
    except: pass

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    try: await context.bot.unpin_all_chat_messages(update.effective_chat.id); await update.message.reply_text("📌 *Unpinned!* ✅")
    except: pass

async def warn(update, ctx):
    cid = update.effective_chat.id
    if not update.message.reply_to_message: return
    t = update.message.reply_to_message.from_user
    if cid not in group_warnings: group_warnings[cid] = {}
    if t.id not in group_warnings[cid]: group_warnings[cid][t.id] = 0
    group_warnings[cid][t.id] += 1
    await update.message.reply_text(f"⚠️ *Warning!* {t.first_name} *{group_warnings[cid][t.id]}/3*")

async def clearwarns(update, ctx):
    cid = update.effective_chat.id
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if cid in group_warnings and t.id in group_warnings[cid]: group_warnings[cid][t.id] = 0
    else: group_warnings[cid] = {}
    await update.message.reply_text("✅ *Cleared!*")

async def ban_user(update, ctx):
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t: return
    try: await ctx.bot.ban_chat_member(update.effective_chat.id, t.id); await update.message.reply_text(f"🔨 *BANNED!* {t.first_name}")
    except: pass

async def unban_user(update, ctx):
    if not ctx.args: return
    try: await ctx.bot.unban_chat_member(update.effective_chat.id, int(ctx.args[0])); await update.message.reply_text("✅ *UNBANNED!*")
    except: pass

async def mute_user(update, ctx):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    t, ts = None, "1h"
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if ctx.args: ts = " ".join(ctx.args)
    if not t or t.id==update.effective_user.id or t.is_bot: return
    mm = parse_time(ts)
    if not mm or mm>43200 or mm<=0: return
    nw, ut = get_ist_now(), get_ist_now()+timedelta(minutes=mm)
    try:
        await ctx.bot.restrict_chat_member(chat_id=cid,user_id=t.id,
            permissions=ChatPermissions(can_send_messages=False,can_send_audios=False,can_send_documents=False,can_send_photos=False,can_send_videos=False,can_send_video_notes=False,can_send_voice_notes=False,can_send_polls=False,can_send_other_messages=False,can_add_web_page_previews=False,can_change_info=False,can_invite_users=False,can_pin_messages=False),until_date=ut)
        tn = t.first_name or "User"
        await update.message.reply_text(f"🔇 *MUTED!* 👤 {tn}\n⏱️ {format_time(mm)}\n📅 `{nw.strftime('%I:%M %p')}`\n🔓 `{ut.strftime('%I:%M %p')}`\n⏰ Auto")
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await ctx.bot.restrict_chat_member(chat_id=cid,user_id=t.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await ctx.bot.send_message(cid, f"✅ *AUTO UNMUTED!* {tn}")
            except: pass
        asyncio.create_task(auto())
    except: pass

async def unmute_user(update, ctx):
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t: return
    try:
        await ctx.bot.restrict_chat_member(chat_id=update.effective_chat.id,user_id=t.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        await update.message.reply_text(f"✅ *UNMUTED!* {t.first_name}")
    except: pass

async def welcome(update, ctx):
    if not update.message.new_chat_members: return
    for u in update.message.new_chat_members:
        if u.id == ctx.bot.id: await ctx.bot.send_message(update.effective_chat.id,
            "✨ *AVANTIKA AI JOINED!* ✨\n\n━━━━━━━━━━━━━━━━━━━━━━\n👑 _Admin_ */activate*\n📢 *PREMIUM REPLIES!*\n━━━━━━━━━━━━━━━━━━━━━━\n\n💻 Coding | 📚 Knowledge | 😂 Fun\n🔇 Mute | 🔨 Ban | ⚠️ Warn | 📌 Pin\n🔍 `/uid` — True Caller Style!\n📱 `/getnumber` — Auto Number\n\n🔥 _Activate me!_", parse_mode="Markdown")
        else: await ctx.bot.send_message(update.effective_chat.id,
            f"✨ *WELCOME!* ✨\n\n━━━━━━━━━━━━━━━━━━━━━━\n👤 *{u.first_name}*\n━━━━━━━━━━━━━━━━━━━━━━\n\n🌟 _Aapka swagat hai!_ 🎉\n\n💎 *Yahaan milega:*\n• *Premium AI Replies* 🔥\n• *Coding Help* 💻\n• *Knowledge* 📚\n• *Fun & Games* 😂\n\n📢 _Just type — I answer instantly!_ 💬\n\n🔰 _Enjoy!_ 🤗", parse_mode="Markdown")

async def start(update, ctx):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK BOSS!* 👑\n\n━━━━━━━━━━━━━━━━━━━━━━\n💎 *AVANTIKA AI — TRUE CALLER BOT*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ *Premium AI Replies*\n✅ *All Languages* 🌍\n✅ *Coding Master* 💻\n✅ *Knowledge Bank* 📚\n✅ *Mute/Ban/Warn* 🛡️\n✅ *Notes/Pin/Rules* 📝\n"
                "✅ *User Management* 👥\n✅ *Broadcast* 📢\n✅ *True Caller UID System* 🔍📱\n\n"
                "⚡ *UID COMMANDS:*\n🔍 `/uid 123456789` — Full Report\n📱 `/getnumber 123456789` — Auto Get Number\n💾 `/savecontact UID Name Number` — Save\n📋 `/savedlist` — All Saved Contacts\n\n"
                "⚡ *BOSS COMMANDS:*\n/start /clear /activate\n/mute /unmute /ban /unban /warn\n/setrules /rules /addnote /notes\n/pin /unpin /info\n/adduser /removeuser /userlist\n/broadcast /id\n\n_Bolo boss!_ 🔥",
                parse_mode="Markdown"
            )
        elif is_allowed(uid): user_history[cid] = []; await update.message.reply_text("✅ *Access Granted!*\n💬 _Ask anything!_")
        else: await update.message.reply_text("🔒 *Access Denied!*")
    else:
        user_history[cid] = []
        await update.message.reply_text("👋 *AVANTIKA AI* 💎\n\n👑 _Admin_ */activate*\n🔇 */mute* | 🔨 */ban* | ⚠️ */warn*\n📜 */rules* | 📝 */notes* | 📌 */pin*\n\n_Activate and enjoy!_ 🔥", parse_mode="Markdown")

async def activate(update, ctx):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if update.effective_user.id not in [a.user.id for a in await ctx.bot.get_chat_administrators(cid)]: await update.message.reply_text("❌ *ADMIN ONLY!*"); return
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text("✅ *ACTIVATED!* 🔥\n💬 AI | 🔇 Mute | 🔨 Ban | ⚠️ Warn | 📜 Rules | 📝 Notes | 📌 Pin | 🔍 UID | 👋 Welcome\n❌ /deactivate")

async def deactivate(update, ctx):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False; await update.message.reply_text("🔴 *OFF!* /activate")

async def clear(update, ctx):
    cid = update.effective_chat.id
    if update.effective_user.id != OWNER_USER_ID: return
    user_history[cid] = []; group_warnings.pop(cid, None); group_rules.pop(cid, None); group_notes.pop(cid, None)
    await update.message.reply_text("✅ *COMPLETE RESET!* 🔄\n💭 Memory ✅\n⚠️ Warnings ✅\n📜 Rules ✅\n📝 Notes ✅\n🆕 _Fresh start!_ 💎")

async def handle(update, ctx):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    if msg.new_chat_members: await welcome(update, ctx); return
    if ct == ChatType.PRIVATE and not is_allowed(uid): await msg.reply_text("🔒 *Permission nahi!*", parse_mode="Markdown"); return
    if ct != ChatType.PRIVATE and (cid not in active_groups or not active_groups[cid]): return
    if not msg.text: return
    await ctx.bot.send_chat_action(chat_id=cid, action="typing")
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
        ("pin",pin),("unpin",unpin),("info",lambda u,c: u.message.reply_text(f"🆔 {u.effective_user.id}")),
        ("adduser",adduser),("removeuser",removeuser),("userlist",userlist),
        ("broadcast",broadcast),("id",get_id),
        ("uid",uid_command),("getnumber",getnumber_command),
        ("savecontact",savecontact),("savedlist",savedlist)
    ]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CommandHandler("mutelist",lambda u,c: u.message.reply_text("🔇 */mute 10s 5m 2h 1d 30d*\n🔊 */unmute* | 🔨 */ban* | ⚠️ */warn* | 🔍 */uid* | 📱 */getnumber*")))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.ALL, handle))
    print("👑 AVANTIKA AI — TRUE CALLER BOT READY!"); app.run_polling()

if __name__ == "__main__": main()
