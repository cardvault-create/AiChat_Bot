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

# ================== AVANTIKA — PURE LANGUAGE MASTER ==================
AVANTIKA_PREAMBLE = """You are AVANTIKA AI. Your ONLY job is to reply in the EXACT SAME LANGUAGE the user is typing in.

CRITICAL RULE — FOLLOW THIS 100%:
- User types in HINDI → You reply in HINDI
- User types in ENGLISH → You reply in ENGLISH
- User types in HINGLISH → You reply in HINGLISH
- User types in TAMIL → You reply in TAMIL
- User types in TELUGU → You reply in TELUGU
- User types in ANY language → Reply in THAT SAME language

DO NOT reply in Hindi if the user is typing in English.
DO NOT reply in English if the user is typing in Hindi.
MATCH THE USER'S LANGUAGE EXACTLY. This is your most important job.

Style: Use ** for BOLD, _ for ITALIC, emojis naturally. Be helpful, friendly, give complete answers."""

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

def get_reply(text, cid):
    if cid not in user_history: user_history[cid] = []
    ch = []
    for msg in user_history[cid][-4:]:
        r = "USER" if msg["role"]=="user" else "CHATBOT"
        ch.append({"role":r,"message":msg["content"]})
    try:
        resp = co.chat(message=text, chat_history=ch, preamble=AVANTIKA_PREAMBLE, temperature=0.95, max_tokens=800)
        return resp.text
    except:
        return "😅 _Fir se bol na dost!_ 💎"

# ================== OWNER ==================
async def adduser(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS ke liye hai yeh!* 👑", parse_mode="Markdown"); return
    if not ctx.args: await update.message.reply_text("📝 */adduser user_id*"); return
    try: allowed_users.add(int(ctx.args[0])); await update.message.reply_text(f"✅ *User Added Successfully!* 🆔 `{ctx.args[0]}` 🔓", parse_mode="Markdown")
    except: await update.message.reply_text("❌ _Valid ID do!_")

async def removeuser(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS ke liye hai!* 👑", parse_mode="Markdown"); return
    if not ctx.args: await update.message.reply_text("📝 */removeuser user_id*"); return
    try:
        rid = int(ctx.args[0])
        if rid == OWNER_USER_ID: await update.message.reply_text("😎 *BOSS ko remove nahi kar sakte!* 👑", parse_mode="Markdown"); return
        allowed_users.discard(rid); await update.message.reply_text(f"✅ *User Removed!* 🆔 `{rid}` 🔒", parse_mode="Markdown")
    except: await update.message.reply_text("❌ _Valid ID do!_")

async def userlist(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    ul = "\n".join([f"• `{uid}` {'👑 BOSS' if uid==OWNER_USER_ID else '✅ Allowed'}" for uid in allowed_users])
    await update.message.reply_text(f"👥 *Premium Users List:*\n\n{ul}\n\n📊 *Total:* {len(allowed_users)}", parse_mode="Markdown")

async def broadcast(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not ctx.args: await update.message.reply_text("📝 */broadcast message*"); return
    msg = "📢 *BOSS Message* 👑\n\n" + " ".join(ctx.args)
    s = 0
    for uid in allowed_users:
        try: await ctx.bot.send_message(uid, msg, parse_mode="Markdown"); s += 1
        except: pass
    await update.message.reply_text(f"✅ *Sent!* 📊 `{s}/{len(allowed_users)}` users", parse_mode="Markdown")

async def get_id(update, ctx):
    if update.message.reply_to_message: await update.message.reply_text(f"👤 *{update.message.reply_to_message.from_user.first_name}*\n🆔 `{update.message.reply_to_message.from_user.id}`", parse_mode="Markdown")
    else: await update.message.reply_text(f"🆔 *Your ID:* `{update.effective_user.id}`", parse_mode="Markdown")

# ================== GROUP ==================
async def setrules(update, ctx):
    cid = update.effective_chat.id
    if not ctx.args: await update.message.reply_text("📝 */setrules rules*"); return
    group_rules[cid] = " ".join(ctx.args)
    await update.message.reply_text("📜 *Group Rules Updated!* ✅", parse_mode="Markdown")

async def rules(update, ctx):
    cid = update.effective_chat.id
    if cid in group_rules: await update.message.reply_text(f"📜 *Group Rules:*\n\n{group_rules[cid]}", parse_mode="Markdown")
    else: await update.message.reply_text("📜 _No rules set yet!_ */setrules*", parse_mode="Markdown")

async def addnote(update, ctx):
    cid = update.effective_chat.id
    if not ctx.args: await update.message.reply_text("📝 */addnote note*"); return
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(ctx.args))
    await update.message.reply_text(f"✅ *Note Added!* 📝 ({len(group_notes[cid])} notes)", parse_mode="Markdown")

async def notes(update, ctx):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]:
        await update.message.reply_text("📝 *Saved Notes:*\n\n" + "\n".join([f"• {n}" for n in group_notes[cid]]), parse_mode="Markdown")
    else: await update.message.reply_text("📝 _No notes saved!_ */addnote*", parse_mode="Markdown")

async def clearnotes(update, ctx):
    group_notes[update.effective_chat.id] = []
    await update.message.reply_text("✅ *All Notes Cleared!* 🧹", parse_mode="Markdown")

async def pin(update, ctx):
    if not update.message.reply_to_message: await update.message.reply_text("📌 _Reply to a message to pin!_"); return
    try: await update.message.reply_to_message.pin(); await update.message.reply_text("📌 *Pinned!* ✅", parse_mode="Markdown")
    except: pass

async def unpin(update, ctx):
    try: await ctx.bot.unpin_all_chat_messages(update.effective_chat.id); await update.message.reply_text("📌 *Unpinned!* ✅", parse_mode="Markdown")
    except: pass

async def info(update, ctx):
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text(f"👤 *{update.effective_user.first_name}*\n🆔 `{update.effective_user.id}`", parse_mode="Markdown")
    else:
        try:
            c = await ctx.bot.get_chat(update.effective_chat.id)
            await update.message.reply_text(f"👥 *{c.title}*\n🆔 `{update.effective_chat.id}`\n👥 {await c.get_member_count()} members", parse_mode="Markdown")
        except: pass

# ================== MODERATION ==================
async def warn(update, ctx):
    cid = update.effective_chat.id
    if not update.message.reply_to_message: await update.message.reply_text("⚠️ _Reply to a message to warn!_"); return
    t = update.message.reply_to_message.from_user
    if t.id == update.effective_user.id: return
    if cid not in group_warnings: group_warnings[cid] = {}
    if t.id not in group_warnings[cid]: group_warnings[cid][t.id] = 0
    group_warnings[cid][t.id] += 1
    wc = group_warnings[cid][t.id]
    await update.message.reply_text(f"⚠️ *Warning Issued!* 👤 {t.first_name}\n📊 *{wc}/3* {'🔴 *Mute recommended!*' if wc>=3 else '⚡ _Be careful!_'}")

async def clearwarns(update, ctx):
    cid = update.effective_chat.id
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if cid in group_warnings and t.id in group_warnings[cid]: group_warnings[cid][t.id] = 0
        await update.message.reply_text(f"✅ *Cleared for {t.first_name}!*")
    else: group_warnings[cid] = {}; await update.message.reply_text("✅ *All warnings cleared!*")

async def ban_user(update, ctx):
    cid = update.effective_chat.id
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t and ctx.args:
        try: t = (await ctx.bot.get_chat_member(cid, int(ctx.args[0]))).user
        except: return
    if not t: return
    try: await ctx.bot.ban_chat_member(cid, t.id); await update.message.reply_text(f"🔨 *BANNED!* 👤 {t.first_name} _has been removed!_", parse_mode="Markdown")
    except: pass

async def unban_user(update, ctx):
    if not ctx.args: await update.message.reply_text("📝 */unban user_id*"); return
    try: await ctx.bot.unban_chat_member(update.effective_chat.id, int(ctx.args[0])); await update.message.reply_text(f"✅ *UNBANNED!* 🆔 `{ctx.args[0]}`", parse_mode="Markdown")
    except: pass

# ================== MUTE ==================
async def mute_user(update, ctx):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    t, ts = None, "1h"
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if ctx.args: ts = " ".join(ctx.args)
    elif ctx.args and len(ctx.args)>=2:
        try: t = (await ctx.bot.get_chat_member(cid,int(ctx.args[0]))).user; ts = " ".join(ctx.args[1:])
        except: return
    else: await update.message.reply_text("🔇 */mute 10s 5m 2h 1d 30d*\n_Reply karke!_ 🇮🇳 ⏰ Auto", parse_mode="Markdown"); return
    if not t or t.id==update.effective_user.id or t.is_bot: return
    mm = parse_time(ts)
    if not mm or mm>43200 or mm<=0: return
    nw, ut = get_ist_now(), get_ist_now()+timedelta(minutes=mm)
    try:
        await ctx.bot.restrict_chat_member(chat_id=cid,user_id=t.id,
            permissions=ChatPermissions(can_send_messages=False,can_send_audios=False,can_send_documents=False,can_send_photos=False,can_send_videos=False,can_send_video_notes=False,can_send_voice_notes=False,can_send_polls=False,can_send_other_messages=False,can_add_web_page_previews=False,can_change_info=False,can_invite_users=False,can_pin_messages=False),until_date=ut)
        tn = t.first_name or "User"
        await update.message.reply_text(
            f"🔇 *MUTED!* 🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {tn}\n🆔 `{t.id}`\n"
            f"⏱️ *Duration:* {format_time(mm)}\n"
            f"📅 *Muted:* `{nw.strftime('%I:%M %p, %d %b')}`\n"
            f"🔓 *Unmute:* `{ut.strftime('%I:%M %p, %d %b')}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⏰ *Auto Unmute ON* | 🔊 */unmute*",
            parse_mode="Markdown"
        )
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await ctx.bot.restrict_chat_member(chat_id=cid,user_id=t.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await ctx.bot.send_message(cid, f"✅ *AUTO UNMUTED!* 👤 {tn} 💬", parse_mode="Markdown")
            except: pass
        asyncio.create_task(auto())
    except: pass

async def unmute_user(update, ctx):
    cid = update.effective_chat.id
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t and ctx.args:
        try: t = (await ctx.bot.get_chat_member(cid,int(ctx.args[0]))).user
        except: return
    if not t: await update.message.reply_text("🔊 _Reply with /unmute_"); return
    try:
        await ctx.bot.restrict_chat_member(chat_id=cid,user_id=t.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        await update.message.reply_text(f"✅ *UNMUTED!* 👤 {t.first_name} 💬", parse_mode="Markdown")
    except: pass

# ================== WELCOME ==================
async def welcome(update, ctx):
    if not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for u in update.message.new_chat_members:
        if u.id == ctx.bot.id:
            await ctx.bot.send_message(cid,
                "✨ *AVANTIKA AI JOINED!* ✨\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "👑 _Admin use_ */activate* _to start_\n"
                "📢 _Then everyone gets_ *PREMIUM REPLIES!*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💻 *Coding* | 📚 *Knowledge* | 😂 *Fun*\n"
                "🔇 *Mute* | 🔨 *Ban* | ⚠️ *Warn* | 📌 *Pin*\n\n"
                "🔥 _Activate and let the magic begin!_",
                parse_mode="Markdown"
            )
        else:
            await ctx.bot.send_message(cid,
                f"✨ *A WARM WELCOME!* ✨\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *{u.first_name}*\n"
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
async def start(update, ctx):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK, BOSS!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 *AVANTIKA AI — ULTIMATE BOT*\n"
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
                "_Your wish is my command!_ 🔥",
                parse_mode="Markdown"
            )
        elif is_allowed(uid): user_history[cid] = []; await update.message.reply_text("✅ *Access Granted!*\n\n💬 _Ask me anything, I'm here to help!_", parse_mode="Markdown")
        else: await update.message.reply_text("🔒 *Access Denied!*\n\n_Please contact the owner._", parse_mode="Markdown")
    else:
        user_history[cid] = []
        await update.message.reply_text(
            "👋 *AVANTIKA AI — WORLD'S #1* 💎\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 _Admin_ */activate* _karo_\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔇 */mute* | 🔨 */ban* | ⚠️ */warn*\n"
            "📜 */rules* | 📝 */notes* | 📌 */pin*\n"
            "🆔 */id* | ℹ️ */info*\n\n"
            "_Activate and let's go!_ 🔥",
            parse_mode="Markdown"
        )

async def activate(update, ctx):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if update.effective_user.id not in [a.user.id for a in await ctx.bot.get_chat_administrators(cid)]: await update.message.reply_text("❌ *ADMIN ONLY!* 👑\n_1️⃣ Make me Admin_\n_2️⃣ All Permissions ON_\n_3️⃣ /activate_", parse_mode="Markdown"); return
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text("✅ *ACTIVATED!* 🔥\n\n💬 *AI* | 🔇 *Mute* | 🔨 *Ban* | ⚠️ *Warn* | 📜 *Rules* | 📝 *Notes* | 📌 *Pin* | 👋 *Welcome*\n❌ /deactivate", parse_mode="Markdown")

async def deactivate(update, ctx):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *OFF!* /activate", parse_mode="Markdown")

async def clear(update, ctx):
    cid = update.effective_chat.id
    if update.effective_user.id != OWNER_USER_ID: return
    user_history[cid] = []
    group_warnings.pop(cid, None)
    group_rules.pop(cid, None)
    group_notes.pop(cid, None)
    await update.message.reply_text(
        "✅ *COMPLETE RESET!* 🔄\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💭 *Memory* — Clear ✅\n"
        "⚠️ *Warnings* — Clear ✅\n"
        "📜 *Rules* — Clear ✅\n"
        "📝 *Notes* — Clear ✅\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🆕 _Bilkul fresh start! Naye conversation!_ 💎",
        parse_mode="Markdown"
    )

# ================== HANDLER ==================
async def handle(update, ctx):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    if msg.new_chat_members: await welcome(update, ctx); return
    if ct == ChatType.PRIVATE and not is_allowed(uid): await msg.reply_text("🔒 *Permission nahi!*", parse_mode="Markdown"); return
    if ct != ChatType.PRIVATE and (cid not in active_groups or not active_groups[cid]): return
    if not msg.text: return
    await ctx.bot.send_chat_action(chat_id=cid, action="typing")
    try:
        reply = get_reply(msg.text, cid)
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
    app.add_handler(CommandHandler("mutelist",lambda u,c: u.message.reply_text("🔇 */mute 10s 5m 2h 1d 30d*\n🔊 */unmute* | 🔨 */ban* | ⚠️ */warn*")))
    app.add_handler(MessageHandler(filters.ALL,handle))
    print("👑 AVANTIKA AI — LANGUAGE MASTER!"); app.run_polling()

if __name__ == "__main__": main()
