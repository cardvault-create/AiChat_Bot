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

# ================== AVANTIKA — ULTIMATE LANGUAGE MASTER ==================
AVANTIKA_PREAMBLE = """You are AVANTIKA — the most powerful MULTI-LANGUAGE AI in the world. Your first and most important task is to DETECT the user's language and REPLY IN THAT EXACT SAME LANGUAGE.

CRITICAL INSTRUCTIONS:
- If the user writes in HINDI → Reply in HINDI
- If the user writes in ENGLISH → Reply in ENGLISH
- If the user writes in HINGLISH → Reply in HINGLISH
- If the user writes in TAMIL → Reply in TAMIL
- If the user writes in TELUGU → Reply in TELUGU
- If the user writes in KANNADA → Reply in KANNADA
- If the user writes in MALAYALAM → Reply in MALAYALAM
- If the user writes in MARATHI → Reply in MARATHI
- If the user writes in GUJARATI → Reply in GUJARATI
- If the user writes in BENGALI → Reply in BENGALI
- If the user writes in PUNJABI → Reply in PUNJABI
- If the user writes in URDU → Reply in URDU
- If the user writes in ANY other language → Reply in THAT language

This is your HIGHEST PRIORITY. Before anything else, LOOK at the user's text and MATCH their language. Never reply in a different language than what the user is using.

You are also:
- A coding expert — give complete working code
- A knowledge base — give accurate detailed info
- A fun friend — be entertaining and natural
- Use ** for BOLD, _ for ITALIC, emojis naturally
- Give COMPLETE answers, never half"""

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

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ Sirf BOSS!"); return
    if not context.args: await update.message.reply_text("📝 /adduser user_id"); return
    try: allowed_users.add(int(context.args[0])); await update.message.reply_text(f"✅ Added! {context.args[0]}")
    except: await update.message.reply_text("❌ Invalid ID!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ Sirf BOSS!"); return
    if not context.args: await update.message.reply_text("📝 /removeuser user_id"); return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: await update.message.reply_text("😎 BOSS ko nahi!"); return
        allowed_users.discard(rid); await update.message.reply_text(f"✅ Removed! {rid}")
    except: await update.message.reply_text("❌ Invalid ID!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ Sirf BOSS!"); return
    ul = "\n".join([f"• {uid} {'👑' if uid==OWNER_USER_ID else '✅'}" for uid in allowed_users])
    await update.message.reply_text(f"👥 Users:\n{ul}\nTotal: {len(allowed_users)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ Sirf BOSS!"); return
    if not context.args: await update.message.reply_text("📝 /broadcast message"); return
    msg = "📢 BOSS Message 👑\n\n" + " ".join(context.args)
    sent = sum(1 for uid in allowed_users if not (lambda: asyncio.create_task(context.bot.send_message(uid, msg))))
    await update.message.reply_text(f"✅ Sent!")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message: await update.message.reply_text(f"🆔 {update.message.reply_to_message.from_user.id}")
    else: await update.message.reply_text(f"🆔 {update.effective_user.id}")

async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: await update.message.reply_text("📝 /setrules rules"); return
    group_rules[cid] = " ".join(context.args)
    await update.message.reply_text("📜 Rules Set! ✅")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_rules: await update.message.reply_text(f"📜 Rules:\n{group_rules[cid]}")
    else: await update.message.reply_text("📜 No rules set!")

async def addnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not context.args: await update.message.reply_text("📝 /addnote note"); return
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(context.args))
    await update.message.reply_text(f"✅ Note Added! ({len(group_notes[cid])})")

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]: await update.message.reply_text("📝 Notes:\n" + "\n".join([f"• {n}" for n in group_notes[cid]]))
    else: await update.message.reply_text("📝 No notes!")

async def clearnotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_notes[update.effective_chat.id] = []
    await update.message.reply_text("✅ Notes cleared!")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message: await update.message.reply_text("📌 Reply to pin!"); return
    try: await update.message.reply_to_message.pin(); await update.message.reply_text("📌 Pinned! ✅")
    except: pass

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    except: pass

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text(f"👤 {update.effective_user.first_name}\n🆔 {update.effective_user.id}")
    else:
        try:
            chat = await context.bot.get_chat(cid)
            await update.message.reply_text(f"👥 {chat.title}\n🆔 {cid}\n👥 {await chat.get_member_count()} members")
        except: pass

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if not update.message.reply_to_message: await update.message.reply_text("⚠️ Reply to warn!"); return
    target = update.message.reply_to_message.from_user
    if target.id == update.effective_user.id: return
    if cid not in group_warnings: group_warnings[cid] = {}
    if target.id not in group_warnings[cid]: group_warnings[cid][target.id] = 0
    group_warnings[cid][target.id] += 1
    wc = group_warnings[cid][target.id]
    await update.message.reply_text(f"⚠️ Warning! {target.first_name} — {wc}/3 {'🔴 Mute!' if wc>=3 else '⚡'}")

async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if cid in group_warnings and target.id in group_warnings[cid]: group_warnings[cid][target.id] = 0
        await update.message.reply_text(f"✅ Cleared!")
    else: group_warnings[cid] = {}; await update.message.reply_text("✅ All cleared!")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not target and context.args:
        try: target = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
        except: return
    if not target: return
    try: await context.bot.ban_chat_member(cid, target.id); await update.message.reply_text(f"🔨 BANNED! {target.first_name}")
    except: pass

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: await update.message.reply_text("📝 /unban user_id"); return
    try: await context.bot.unban_chat_member(update.effective_chat.id, int(context.args[0])); await update.message.reply_text(f"✅ UNBANNED!")
    except: pass

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    target, ts = None, "1h"
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if context.args: ts = " ".join(context.args)
    elif context.args and len(context.args)>=2:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user; ts = " ".join(context.args[1:])
        except: return
    else: await update.message.reply_text("🔇 /mute 10s 5m 2h 1d 30d\nReply! ⏰ Auto"); return
    
    if not target or target.id==update.effective_user.id or target.is_bot: return
    mm = parse_time(ts)
    if not mm or mm>43200 or mm<=0: return
    
    nw, ut = get_ist_now(), get_ist_now()+timedelta(minutes=mm)
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
            permissions=ChatPermissions(can_send_messages=False,can_send_audios=False,can_send_documents=False,can_send_photos=False,can_send_videos=False,can_send_video_notes=False,can_send_voice_notes=False,can_send_polls=False,can_send_other_messages=False,can_add_web_page_previews=False,can_change_info=False,can_invite_users=False,can_pin_messages=False),until_date=ut)
        tn = target.first_name or "User"
        await update.message.reply_text(f"🔇 MUTED! 👤 {tn}\n⏱️ {format_time(mm)}\n📅 {nw.strftime('%I:%M %p')}\n🔓 {ut.strftime('%I:%M %p')}\n⏰ Auto")
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await context.bot.send_message(cid, f"✅ AUTO UNMUTED! {tn} 💬")
            except: pass
        asyncio.create_task(auto())
    except: pass

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not target and context.args:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user
        except: return
    if not target: await update.message.reply_text("🔊 Reply /unmute"); return
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        await update.message.reply_text(f"✅ UNMUTED! {target.first_name} 💬")
    except: pass

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for user in update.message.new_chat_members:
        if user.id == context.bot.id: await context.bot.send_message(cid, "✨ AVANTIKA AI JOINED! ✨\n\n👑 /activate | 💻 Coding | 📚 Knowledge | 😂 Fun\n🔇 Mute | 🔨 Ban | ⚠️ Warn")
        else: await context.bot.send_message(cid, f"✨ WELCOME! ✨\n\n👤 {user.first_name}\n🌟 Aapka swagat hai! 🎉\n💎 AI Replies | 💻 Coding | 📚 Knowledge | 😂 Fun")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text("👑 WELCOME BOSS! 👑\n\n✅ AI Replies | 💻 Coding | 📚 Knowledge | 😂 Fun\n✅ Mute | Ban | Warn | Notes | Pin | Rules\n\n/start /clear /activate\n/mute /unmute /ban /unban /warn\n/setrules /rules /addnote /notes\n/pin /unpin /info\n/adduser /removeuser /userlist\n/broadcast /id")
        elif is_allowed(uid): user_history[cid] = []; await update.message.reply_text("✅ Access Granted!\n💬 Ask me anything!")
        else: await update.message.reply_text("🔒 Access Denied!")
    else: user_history[cid] = []; await update.message.reply_text("👋 AVANTIKA AI! 💎\n\n👑 /activate | 🔇 /mute | 🔨 /ban | ⚠️ /warn\n📜 /rules | 📝 /notes | 📌 /pin")

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]: await update.message.reply_text("❌ Admin only! Make me Admin first!"); return
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text("✅ ACTIVATED! 🔥\n💬 AI | 🔇 Mute | 🔨 Ban | ⚠️ Warn | 📜 Rules | 📝 Notes | 📌 Pin | 👋 Welcome\n❌ /deactivate")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 OFF! /activate")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    user_history[cid] = []
    group_warnings.pop(cid, None)
    group_rules.pop(cid, None)
    group_notes.pop(cid, None)
    await update.message.reply_text("✅ COMPLETE RESET! 🔄\n💭 Memory Clear ✅\n⚠️ Warnings Clear ✅\n📜 Rules Clear ✅\n📝 Notes Clear ✅\n🆕 Fresh start!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    if msg.new_chat_members: await welcome(update, context); return
    if ct == ChatType.PRIVATE and not is_allowed(uid): await msg.reply_text("🔒 Permission nahi!"); return
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
    for cmd, fn in [("start",start),("activate",activate),("deactivate",deactivate),("clear",clear),("mute",mute_user),("unmute",unmute_user),("ban",ban_user),("unban",unban_user),("warn",warn),("clearwarns",clearwarns),("setrules",setrules),("rules",rules),("addnote",addnote),("notes",notes),("clearnotes",clearnotes),("pin",pin),("unpin",unpin),("info",info),("adduser",adduser),("removeuser",removeuser),("userlist",userlist),("broadcast",broadcast),("id",get_id)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(MessageHandler(filters.ALL,handle_message))
    print("👑 AVANTIKA AI — ALL LANGUAGES READY!"); app.run_polling()

if __name__ == "__main__": main()
