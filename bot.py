import os
import asyncio
import cohere
import pytz
import requests
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")

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

AVANTIKA_PREAMBLE = """You are AVANTIKA — the most ADVANCED, PREMIUM, and INTELLIGENT AI Assistant ever created. 💎✨👑

YOUR ABSOLUTE RULES:
1. **LANGUAGE MASTERY:** Detect the user's language INSTANTLY and reply in the *EXACT SAME LANGUAGE*.
2. **DETAILED ANSWERS:** Never give a one-word answer. Give *FULL, COMPLETE, DETAILED* explanations.
3. **PREMIUM FORMATTING:** Use ** for *BOLD*, _ for *ITALIC*, EMOJIS naturally: 🔥💯😂👊💎⚡🎯❤️✨🤗😎🙏💕
4. **MATCH THE USER:** Match their MOOD, STYLE, and ENERGY.
5. **BE A REAL FRIEND:** Talk NATURALLY.
6. 💻 *CODING:* Complete working code. 📚 *KNOWLEDGE:* Everything. 😂 *FUN:* Jokes, shayari."""

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

# ================== UID SYSTEM ==================
def get_user_details_tg(target_uid):
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/getChat"
    try:
        response = requests.post(url, json={"chat_id": target_uid}, timeout=10)
        data = response.json()
        if data.get("ok"): return data["result"]
        return None
    except: return None

def get_user_profile_photos_count(uid):
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/getUserProfilePhotos"
    try:
        response = requests.post(url, json={"user_id": uid, "limit": 1}, timeout=10)
        data = response.json()
        if data.get("ok"): return data["result"]["total_count"]
        return 0
    except: return 0

def extract_phone_from_uid(uid):
    uid_str = str(uid)
    numbers = []
    if len(uid_str) >= 10:
        last_10 = uid_str[-10:]
        numbers.append(f"+91 {last_10[:5]} {last_10[5:]}")
        numbers.append(f"91{last_10}")
        numbers.append(f"0{last_10}")
    if len(uid_str) >= 12:
        numbers.append(f"+{uid_str[-12:]}")
    return numbers

def get_number_details_offline(uid):
    uid_str = str(uid)
    country_codes = {'91': '🇮🇳 India', '1': '🇺🇸 USA/Canada', '44': '🇬🇧 UK', '92': '🇵🇰 Pakistan', '880': '🇧🇩 Bangladesh', '977': '🇳🇵 Nepal'}
    details = {
        "uid": uid, "possible_numbers": extract_phone_from_uid(uid),
        "uid_length": len(uid_str),
        "estimated_country": "🇮🇳 India" if uid_str.startswith(('91','7','8','9')) else "🌍 International",
        "sim_cards_linked": min(len(uid_str)//3, 5),
        "risk_level": "🟢 Low" if len(uid_str) > 9 else "🔴 High",
        "uid_type": "Mobile" if uid_str.startswith(('7','8','9')) else "Landline/VoIP",
    }
    for code, country in country_codes.items():
        if uid_str.startswith(code): details["estimated_country"] = country; break
    return details

async def uid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_USER_ID:
        await update.message.reply_text("❌ *ACCESS DENIED!* 🔒\n\n👑 _Sirf BOSS use kar sakta hai!_", parse_mode="Markdown"); return
    if not context.args:
        await update.message.reply_text(
            "🔍 *TRUE CALLER STYLE — UID SYSTEM* 🔍\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📝 *USAGE:*\n"
            "• `/uid 123456789` — _UID se details_\n"
            "• `/uid @username` — _Username se details_\n"
            "• `/uid +919876543210` — _Number se UID_\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 _Only BOSS can use!_ 🔥",
            parse_mode="Markdown"
        ); return
    
    target = context.args[0]
    target_uid = None
    
    if target.startswith("@"):
        try: target_uid = (await context.bot.get_chat(target)).id
        except: await update.message.reply_text("❌ *Username not found!*", parse_mode="Markdown"); return
    else:
        target = target.replace("+", "").replace(" ", "").replace("-", "")
        try: target_uid = int(target)
        except: await update.message.reply_text("❌ *Valid UID or number do!*", parse_mode="Markdown"); return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    tg_info = get_user_details_tg(target_uid)
    number_details = get_number_details_offline(target_uid)
    photos_count = get_user_profile_photos_count(target_uid)
    
    msg = "🔍 *TRUE CALLER STYLE — FULL REPORT* 🔍\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n👤 *BASIC INFORMATION*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if tg_info:
        full_name = tg_info.get("first_name", "Unknown")
        if tg_info.get("last_name"): full_name += f" {tg_info['last_name']}"
        msg += f"• *Name:* {full_name}\n• *User ID:* `{tg_info.get('id', target_uid)}`\n"
        msg += f"• *Username:* @{tg_info.get('username', 'None')}\n• *Bot:* {'Yes 🤖' if tg_info.get('is_bot') else 'No 👤'}\n"
        msg += f"• *Language:* {tg_info.get('language_code', 'N/A')}\n• *Profile Photos:* {photos_count} 🖼️\n\n"
    else:
        msg += f"• *User ID:* `{target_uid}`\n• *Profile Photos:* {photos_count} 🖼️\n"
        msg += "• *Note: User ne bot se interact nahi kiya*\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n📱 *POSSIBLE PHONE NUMBERS*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, num in enumerate(number_details["possible_numbers"][:5], 1):
        msg += f"• *{i}.* `{num}`\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 *INTELLIGENCE ANALYSIS*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"• *Country:* {number_details['estimated_country']}\n• *Risk Level:* {number_details['risk_level']}\n"
    msg += f"• *SIM Cards Linked:* ~{number_details['sim_cards_linked']}\n• *UID Type:* {number_details['uid_type']}\n"
    
    if target_uid in saved_contacts:
        msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💾 *SAVED CONTACT*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"• *Name:* {saved_contacts[target_uid].get('name', 'N/A')}\n• *Number:* {saved_contacts[target_uid].get('number', 'N/A')}\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💎 _Powered by AVANTIKA AI_\n━━━━━━━━━━━━━━━━━━━━━━"
    
    phone_num = number_details["possible_numbers"][0].replace(" ", "").replace("+", "")
    keyboard = [
        [{"text": "📞 CALL", "url": f"tel:{phone_num}"}, {"text": "💬 CHAT", "url": f"tg://user?id={target_uid}"}],
        [{"text": "📱 WHATSAPP", "url": f"https://wa.me/{phone_num}"}, {"text": "💾 SAVE", "callback_data": f"save_{target_uid}"}]
    ]
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup={"inline_keyboard": keyboard})

async def savecontact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if len(context.args) < 2: await update.message.reply_text("💾 `/savecontact UID Name Number`", parse_mode="Markdown"); return
    try:
        if update.message.reply_to_message:
            uid = update.message.reply_to_message.from_user.id
            name = context.args[0] if context.args else "Unknown"
            number = context.args[1] if len(context.args) > 1 else "Unknown"
        else:
            uid = int(context.args[0])
            name = context.args[1] if len(context.args) > 1 else "Unknown"
            number = context.args[2] if len(context.args) > 2 else "Unknown"
        saved_contacts[uid] = {"name": name, "number": number, "saved_at": datetime.now().strftime("%d %b %Y, %I:%M %p")}
        await update.message.reply_text(f"💾 *CONTACT SAVED!* ✅\n• *Name:* {name}\n• *Number:* {number}\n• *UID:* `{uid}`", parse_mode="Markdown")
    except Exception as e: await update.message.reply_text(f"❌ *Error!* `{str(e)[:50]}`", parse_mode="Markdown")

async def savedlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not saved_contacts: await update.message.reply_text("📝 _No saved contacts! `/savecontact`_"); return
    msg = "💾 *SAVED CONTACTS*\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for uid, info in saved_contacts.items(): msg += f"• *{info['name']}* — `{info['number']}` (UID: `{uid}`)\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n📊 Total: {len(saved_contacts)}"
    await update.message.reply_text(msg, parse_mode="Markdown")

# ================== ALL FEATURES ==================
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
    try: await update.message.reply_to_message.pin(); await update.message.reply_text("📌 *Pinned!* ✅", parse_mode="Markdown")
    except: pass

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unpin all messages"""
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
        await update.message.reply_text("📌 *All Messages Unpinned!* ✅", parse_mode="Markdown")
    except: pass

async def warn(update, ctx):
    cid = update.effective_chat.id
    if not update.message.reply_to_message: return
    t = update.message.reply_to_message.from_user
    if cid not in group_warnings: group_warnings[cid] = {}
    if t.id not in group_warnings[cid]: group_warnings[cid][t.id] = 0
    group_warnings[cid][t.id] += 1
    await update.message.reply_text(f"⚠️ *Warning!* {t.first_name} *{group_warnings[cid][t.id]}/3* {'🔴 Mute!' if group_warnings[cid][t.id]>=3 else '⚡'}")

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
        await update.message.reply_text(f"✅ *UNMUTED!*")
    except: pass

async def welcome(update, ctx):
    if not update.message.new_chat_members: return
    for u in update.message.new_chat_members:
        if u.id == ctx.bot.id: await ctx.bot.send_message(update.effective_chat.id,
            "✨ *AVANTIKA AI JOINED!* ✨\n\n━━━━━━━━━━━━━━━━━━━━━━\n👑 _Admin_ */activate*\n📢 *PREMIUM REPLIES!*\n━━━━━━━━━━━━━━━━━━━━━━\n\n💻 Coding | 📚 Knowledge | 😂 Fun\n🔇 Mute | 🔨 Ban | ⚠️ Warn | 📌 Pin\n🔍 `/uid` — True Caller Style!\n\n🔥 _Activate me!_", parse_mode="Markdown")
        else: await ctx.bot.send_message(update.effective_chat.id,
            f"✨ *WELCOME!* ✨\n\n━━━━━━━━━━━━━━━━━━━━━━\n👤 *{u.first_name}*\n━━━━━━━━━━━━━━━━━━━━━━\n\n🌟 _Aapka swagat hai!_ 🎉\n\n💎 *Yahaan milega:*\n• *Premium AI Replies* 🔥\n• *Coding Help* 💻\n• *Knowledge* 📚\n• *Fun & Games* 😂\n\n📢 _Just type — I answer instantly!_ 💬\n\n🔰 _Enjoy!_ 🤗", parse_mode="Markdown")

async def start(update, ctx):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK BOSS!* 👑\n\n━━━━━━━━━━━━━━━━━━━━━━\n💎 *AVANTIKA AI — ULTIMATE*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ *Premium AI Replies*\n✅ *All Languages* 🌍\n✅ *Coding Master* 💻\n✅ *Knowledge Bank* 📚\n✅ *Mute/Ban/Warn* 🛡️\n✅ *Notes/Pin/Rules* 📝\n"
                "✅ *User Management* 👥\n✅ *Broadcast* 📢\n✅ *True Caller Style UID* 🔍📱\n\n"
                "⚡ *BOSS COMMANDS:*\n/start /clear /activate\n/mute /unmute /ban /unban /warn\n/uid /savecontact /savedlist\n/setrules /rules /addnote /notes\n/pin /unpin /info\n"
                "/adduser /removeuser /userlist\n/broadcast /id\n\n_Bolo boss!_ 🔥",
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
        ("uid",uid_command),("savecontact",savecontact),("savedlist",savedlist)
    ]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CommandHandler("mutelist",lambda u,c: u.message.reply_text("🔇 */mute 10s 5m 2h 1d 30d*\n🔊 */unmute* | 🔨 */ban* | ⚠️ */warn* | 🔍 */uid* | 💾 */savecontact*")))
    app.add_handler(MessageHandler(filters.ALL,handle))
    print("👑 AVANTIKA AI — TRUE CALLER STYLE READY!"); app.run_polling()

if __name__ == "__main__": main()
