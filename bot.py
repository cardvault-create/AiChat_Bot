import os
import asyncio
import cohere
import pytz
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

SYSTEM_PROMPT = """You are AVANTIKA AI.
CRITICAL: Detect user's language, reply in SAME language.
Hindi→Hindi, English→English, Hinglish→Hinglish, ANY→Same.
Complete detailed answers. **Bold**, _Italic_, emojis. Natural friendly tone."""

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

def get_reply(text, chat_id):
    if chat_id not in user_history: user_history[chat_id] = []
    prompt = f"{SYSTEM_PROMPT}\n\nPrevious chat:\n"
    for msg in user_history[chat_id][-4:]:
        prompt += f"{msg['role']}: {msg['content']}\n"
    prompt += f"user: {text}\nassistant:"
    try:
        response = co.generate(
            model='command-r-plus',
            prompt=prompt,
            max_tokens=800,
            temperature=0.95
        )
        return response.generations[0].text
    except:
        return "😅 _Fir se bol bhai!_ 💎"

# ================== ALL FEATURES (Compact) ==================
async def adduser(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: return
    if not ctx.args: return
    try: allowed_users.add(int(ctx.args[0])); await update.message.reply_text("✅ Added!")
    except: pass

async def removeuser(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: return
    if not ctx.args: return
    try:
        rid = int(ctx.args[0])
        if rid == OWNER_USER_ID: return
        allowed_users.discard(rid); await update.message.reply_text("✅ Removed!")
    except: pass

async def userlist(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: return
    await update.message.reply_text(f"👥 Users: {len(allowed_users)}")

async def broadcast(update, ctx):
    if update.effective_user.id != OWNER_USER_ID: return
    if not ctx.args: return
    for uid in allowed_users:
        try: await ctx.bot.send_message(uid, "📢 BOSS 👑\n\n" + " ".join(ctx.args))
        except: pass

async def get_id(update, ctx):
    if update.message.reply_to_message: await update.message.reply_text(f"🆔 {update.message.reply_to_message.from_user.id}")
    else: await update.message.reply_text(f"🆔 {update.effective_user.id}")

async def setrules(update, ctx):
    if not ctx.args: return
    group_rules[update.effective_chat.id] = " ".join(ctx.args)
    await update.message.reply_text("📜 Rules Set!")

async def rules(update, ctx):
    await update.message.reply_text(group_rules.get(update.effective_chat.id, "📜 No rules!"))

async def addnote(update, ctx):
    cid = update.effective_chat.id
    if not ctx.args: return
    if cid not in group_notes: group_notes[cid] = []
    group_notes[cid].append(" ".join(ctx.args))
    await update.message.reply_text("✅ Note Added!")

async def notes(update, ctx):
    cid = update.effective_chat.id
    if cid in group_notes and group_notes[cid]: await update.message.reply_text("📝 " + "\n".join([f"• {n}" for n in group_notes[cid]]))
    else: await update.message.reply_text("📝 No notes!")

async def clearnotes(update, ctx): group_notes[update.effective_chat.id] = []; await update.message.reply_text("✅ Cleared!")

async def warn(update, ctx):
    cid = update.effective_chat.id
    if not update.message.reply_to_message: return
    t = update.message.reply_to_message.from_user
    if cid not in group_warnings: group_warnings[cid] = {}
    if t.id not in group_warnings[cid]: group_warnings[cid][t.id] = 0
    group_warnings[cid][t.id] += 1
    await update.message.reply_text(f"⚠️ Warning! {t.first_name} {group_warnings[cid][t.id]}/3")

async def clearwarns(update, ctx):
    cid = update.effective_chat.id
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        if cid in group_warnings and t.id in group_warnings[cid]: group_warnings[cid][t.id] = 0
    else: group_warnings[cid] = {}
    await update.message.reply_text("✅ Cleared!")

async def ban_user(update, ctx):
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t: return
    try: await ctx.bot.ban_chat_member(update.effective_chat.id, t.id); await update.message.reply_text("🔨 BANNED!")
    except: pass

async def unban_user(update, ctx):
    if not ctx.args: return
    try: await ctx.bot.unban_chat_member(update.effective_chat.id, int(ctx.args[0])); await update.message.reply_text("✅ UNBANNED!")
    except: pass

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
    else: return
    if not t or t.id==update.effective_user.id or t.is_bot: return
    mm = parse_time(ts)
    if not mm or mm>43200 or mm<=0: return
    nw, ut = get_ist_now(), get_ist_now()+timedelta(minutes=mm)
    try:
        await ctx.bot.restrict_chat_member(chat_id=cid,user_id=t.id,
            permissions=ChatPermissions(can_send_messages=False,can_send_audios=False,can_send_documents=False,can_send_photos=False,can_send_videos=False,can_send_video_notes=False,can_send_voice_notes=False,can_send_polls=False,can_send_other_messages=False,can_add_web_page_previews=False,can_change_info=False,can_invite_users=False,can_pin_messages=False),until_date=ut)
        await update.message.reply_text(f"🔇 MUTED! 👤 {t.first_name}\n⏱️ {format_time(mm)}\n🔓 {ut.strftime('%I:%M %p')}")
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await ctx.bot.restrict_chat_member(chat_id=cid,user_id=t.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await ctx.bot.send_message(cid, f"✅ AUTO UNMUTED! {t.first_name}")
            except: pass
        asyncio.create_task(auto())
    except: pass

async def unmute_user(update, ctx):
    t = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not t: return
    try:
        await ctx.bot.restrict_chat_member(chat_id=update.effective_chat.id,user_id=t.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        await update.message.reply_text(f"✅ UNMUTED!")
    except: pass

async def welcome(update, ctx):
    if not update.message.new_chat_members: return
    for u in update.message.new_chat_members:
        if u.id == ctx.bot.id: await ctx.bot.send_message(update.effective_chat.id, "✨ AVANTIKA AI JOINED! ✨\n👑 /activate | 💻 Coding | 📚 Knowledge | 😂 Fun")
        else: await ctx.bot.send_message(update.effective_chat.id, f"✨ WELCOME! ✨\n👤 {u.first_name}\n🌟 Happy you're here! 🎉")

async def start(update, ctx):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text("👑 WELCOME BACK BOSS! 👑\n\n💎 AVANTIKA AI — COHERE\n✅ All Languages\n✅ Coding | Knowledge | Fun\n\n/start /clear /activate\n/mute /unmute /ban /unban /warn\n/setrules /rules /addnote /notes\n/pin /unpin /info\n/adduser /removeuser /userlist\n/broadcast /id\n\n_Bolo boss!_ 🔥")
        elif is_allowed(uid): user_history[cid] = []; await update.message.reply_text("✅ Access Granted! 💬")
        else: await update.message.reply_text("🔒 Access Denied!")
    else:
        user_history[cid] = []
        await update.message.reply_text("👋 AVANTIKA AI 💎\n👑 Admin /activate\n🔇 /mute | 🔨 /ban | ⚠️ /warn")

async def activate(update, ctx):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    if update.effective_user.id not in [a.user.id for a in await ctx.bot.get_chat_administrators(cid)]: await update.message.reply_text("❌ ADMIN ONLY!"); return
    active_groups[cid] = True; user_history[cid] = []
    await update.message.reply_text("✅ ACTIVATED! 🔥\n❌ /deactivate")

async def deactivate(update, ctx):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False; await update.message.reply_text("🔴 OFF! /activate")

async def clear(update, ctx):
    cid = update.effective_chat.id
    user_history[cid] = []; group_warnings.pop(cid, None); group_rules.pop(cid, None); group_notes.pop(cid, None)
    await update.message.reply_text("✅ COMPLETE RESET! 🔄")

async def handle(update, ctx):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    if msg.new_chat_members: await welcome(update, ctx); return
    if ct == ChatType.PRIVATE and not is_allowed(uid): await msg.reply_text("🔒 Permission nahi!"); return
    if ct != ChatType.PRIVATE and (cid not in active_groups or not active_groups[cid]): return
    if not msg.text: return
    await ctx.bot.send_chat_action(chat_id=cid, action="typing")
    try:
        reply = get_reply(msg.text, cid)
        if cid not in user_history: user_history[cid] = []
        user_history[cid].append({"role":"user","content":msg.text})
        user_history[cid].append({"role":"assistant","content":reply})
        user_history[cid] = user_history[cid][-10:]
        await msg.reply_text(reply)
    except: pass

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    for cmd, fn in [("start",start),("activate",activate),("deactivate",deactivate),("clear",clear),("mute",mute_user),("unmute",unmute_user),("ban",ban_user),("unban",unban_user),("warn",warn),("clearwarns",clearwarns),("setrules",setrules),("rules",rules),("addnote",addnote),("notes",notes),("clearnotes",clearnotes),("pin",lambda u,c: None),("info",lambda u,c: u.message.reply_text(f"🆔 {u.effective_user.id}")),("adduser",adduser),("removeuser",removeuser),("userlist",userlist),("broadcast",broadcast),("id",get_id)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CommandHandler("mutelist",lambda u,c: u.message.reply_text("🔇 /mute 10s 5m 2h 1d 30d\n🔊 /unmute | 🔨 /ban | ⚠️ /warn")))
    app.add_handler(MessageHandler(filters.ALL,handle))
    print("👑 AVANTIKA AI — COHERE READY!"); app.run_polling()

if __name__ == "__main__": main()
