import os, asyncio, requests, pytz
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
OWNER_USER_ID = 7614459746
IST = pytz.timezone('Asia/Kolkata')
user_history, active_groups, allowed_users = {}, {}, {7614459746}

def get_ist_now(): return datetime.now(IST)

def parse_time(ts):
    ts = ts.lower().strip().replace(" ", "")
    if not ts: return None
    for word, mult in [('second',1/60),('sec',1/60),('minute',1),('mins',1),('min',1),('hour',60),('hrs',60),('hr',60),('day',1440)]:
        if ts.endswith(word):
            try: return float(ts[:-len(word)])*mult
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
    if ts <= 0: return "0s"
    d,ts = divmod(ts,86400); h,ts = divmod(ts,3600); mi,s = divmod(ts,60)
    p = []
    if d: p.append(f"{d}d")
    if h: p.append(f"{h}h")
    if mi: p.append(f"{mi}m")
    if s and not d: p.append(f"{s}s")
    return " ".join(p)

def get_reply(text, cid):
    if cid not in user_history: user_history[cid] = []
    msgs = [{"role":"system","content":"You are GARAM GAND AI. Give accurate detailed answers. Use emojis. Reply in user's language."}]
    for m in user_history[cid][-4:]:
        msgs.append({"role":"user" if m["role"]=="user" else "assistant","content":m["content"]})
    msgs.append({"role":"user","content":text})
    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {DEEPSEEK_API_KEY}","Content-Type":"application/json"},
            json={"model":"deepseek-chat","messages":msgs,"temperature":0.8,"max_tokens":500},timeout=20)
        d = r.json()
        return d["choices"][0]["message"]["content"] if "choices" in d else "😅 Error: "+str(d.get("error",{}).get("message",""))[:50]
    except: return "😅 Network issue!"

def ok(uid): return uid in allowed_users

async def adduser(u,c):
    if u.effective_user.id!=OWNER_USER_ID: return await u.message.reply_text("❌ Sirf BOSS!")
    if not c.args: return await u.message.reply_text("📝 /adduser id")
    try: allowed_users.add(int(c.args[0])); await u.message.reply_text("✅ Added!")
    except: await u.message.reply_text("❌ Valid ID!")

async def remuser(u,c):
    if u.effective_user.id!=OWNER_USER_ID: return await u.message.reply_text("❌ Sirf BOSS!")
    if not c.args: return await u.message.reply_text("📝 /removeuser id")
    try:
        rid = int(c.args[0])
        if rid==OWNER_USER_ID: return await u.message.reply_text("😎 BOSS!")
        allowed_users.discard(rid); await u.message.reply_text("✅ Removed!")
    except: await u.message.reply_text("❌ Valid ID!")

async def ulist(u,c):
    if u.effective_user.id!=OWNER_USER_ID: return await u.message.reply_text("❌ Sirf BOSS!")
    ul = "\n".join([f"• `{x}` {'👑' if x==OWNER_USER_ID else '✅'}" for x in allowed_users])
    await u.message.reply_text(f"👥 Users:\n{ul}\n\nTotal: {len(allowed_users)}")

async def getid(u,c):
    if u.message.reply_to_message: t = u.message.reply_to_message.from_user; await u.message.reply_text(f"👤 {t.first_name}\n🆔 `{t.id}`")
    else: await u.message.reply_text(f"🆔 `{u.effective_user.id}`")

async def welcome(u,c):
    if not u.message.new_chat_members: return
    for nu in u.message.new_chat_members:
        if nu.id==c.bot.id: await c.bot.send_message(u.effective_chat.id,"🤖 Bot Ready!\n👑 /activate")
        else: await c.bot.send_message(u.effective_chat.id,f"✨ Welcome {nu.first_name}! 🎉")

async def mute(u,c):
    cid = u.effective_chat.id
    if u.effective_chat.type==ChatType.PRIVATE: return await u.message.reply_text("⚡ Sirf group!")
    try:
        if u.effective_user.id not in [a.user.id for a in await c.bot.get_chat_administrators(cid)]:
            return await u.message.reply_text("❌ Sirf Admin!")
    except: return await u.message.reply_text("❌ Bot ko Admin banao!")
    target, ts = None, "1h"
    if u.message.reply_to_message:
        target = u.message.reply_to_message.from_user
        if c.args: ts = " ".join(c.args)
    elif c.args and len(c.args)>=2:
        try: target = (await c.bot.get_chat_member(cid,int(c.args[0]))).user; ts = " ".join(c.args[1:])
        except: return
    else: return await u.message.reply_text("🔇 /mute 10s 5m 2h 1d\nReply karke!")
    if not target or target.id==u.effective_user.id or target.is_bot: return
    mm = parse_time(ts)
    if not mm or mm>43200 or mm<=0: return
    nw, ut = get_ist_now(), get_ist_now()+timedelta(minutes=mm)
    try:
        await c.bot.restrict_chat_member(chat_id=cid,user_id=target.id,permissions=ChatPermissions(can_send_messages=False,can_send_audios=False,can_send_documents=False,can_send_photos=False,can_send_videos=False,can_send_video_notes=False,can_send_voice_notes=False,can_send_polls=False,can_send_other_messages=False,can_add_web_page_previews=False,can_change_info=False,can_invite_users=False,can_pin_messages=False),until_date=ut)
        tn = target.first_name or "User"
        if target.last_name: tn += f" {target.last_name}"
        await u.message.reply_text(f"🔇 MUTED!\n👤 {tn}\n👑 {u.effective_user.first_name}\n⏱️ {format_time(mm)}\n📅 {nw.strftime('%I:%M %p, %d %b')}\n🔓 {ut.strftime('%I:%M %p, %d %b')}\n⏰ Auto ON")
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await c.bot.restrict_chat_member(chat_id=cid,user_id=target.id,permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await c.bot.send_message(cid,f"✅ UNMUTED! {tn} 🎉")
            except: pass
        asyncio.create_task(auto())
    except: pass

async def unmute(u,c):
    cid = u.effective_chat.id
    if u.effective_chat.type==ChatType.PRIVATE: return
    target = u.message.reply_to_message.from_user if u.message.reply_to_message else None
    if not target and c.args:
        try: target = (await c.bot.get_chat_member(cid,int(c.args[0]))).user
        except: return
    if not target: return await u.message.reply_text("🔊 Reply /unmute")
    try:
        await c.bot.restrict_chat_member(chat_id=cid,user_id=target.id,permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        await u.message.reply_text(f"✅ UNMUTED! {target.first_name} 🎉")
    except: pass

async def start(u,c):
    cid = u.effective_chat.id; ct = u.effective_chat.type; uid = u.effective_user.id
    if ct==ChatType.PRIVATE:
        if ok(uid): user_history[cid]=[]; await u.message.reply_text("💎 GARAM GAND AI!\n✅ Premium AI\n✅ Coding 💻\n✅ Knowledge 📚\n\nKuch bhi puchho! 🔥")
        else: await u.message.reply_text("🔒 Permission nahi!")
    else: user_history[cid]=[]; await u.message.reply_text("👋 /activate karo!")

async def activate(u,c):
    cid = u.effective_chat.id
    if u.effective_chat.type==ChatType.PRIVATE: return
    try:
        if u.effective_user.id not in [a.user.id for a in await c.bot.get_chat_administrators(cid)]:
            return await u.message.reply_text("❌ Bot ko Admin banao!")
    except: return await u.message.reply_text("❌ Bot ko Admin banao!")
    active_groups[cid]=True; await u.message.reply_text("✅ ACTIVATED! 🔥")

async def deactivate(u,c):
    if u.effective_chat.type!=ChatType.PRIVATE: active_groups[u.effective_chat.id]=False; await u.message.reply_text("🔴 Off!")

async def clear(u,c): user_history[u.effective_chat.id]=[]; await u.message.reply_text("✅ Clear!")

async def handle(u,c):
    cid = u.effective_chat.id; ct = u.effective_chat.type; msg = u.message; uid = u.effective_user.id
    if msg.new_chat_members: return await welcome(u,c)
    if ct==ChatType.PRIVATE and not ok(uid): return await msg.reply_text("🔒 Permission nahi!")
    if ct!=ChatType.PRIVATE and cid not in active_groups: return
    if not msg.text: return
    await c.bot.send_chat_action(chat_id=cid,action="typing")
    reply = get_reply(msg.text,cid)
    if cid not in user_history: user_history[cid]=[]
    user_history[cid].extend([{"role":"user","content":msg.text},{"role":"assistant","content":reply}])
    user_history[cid]=user_history[cid][-15:]
    await msg.reply_text(reply)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    for cmd, fn in [("start",start),("activate",activate),("deactivate",deactivate),("clear",clear),("mute",mute),("unmute",unmute),("adduser",adduser),("removeuser",remuser),("userlist",ulist),("id",getid)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CommandHandler("mutelist",lambda u,c: u.message.reply_text("🔇 /mute 10s 5m 2h 1d\n🔊 /unmute")))
    app.add_handler(MessageHandler(filters.ALL,handle))
    print("💎 READY!"); app.run_polling()

if __name__=="__main__": main()
