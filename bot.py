import os
import asyncio
import google.generativeai as genai
import pytz
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

OWNER_USER_ID = 7614459746
IST = pytz.timezone('Asia/Kolkata')
user_history = {}
active_groups = {}
allowed_users = {7614459746}

def get_ist_now():
    return datetime.now(IST)

def parse_time(ts):
    ts = ts.lower().strip().replace(" ", "")
    if not ts: return None
    if 'seconds' in ts or ts.endswith('second') or ts.endswith('sec'):
        num = ts.replace('seconds','').replace('second','').replace('sec','')
        return float(num)/60 if num else None
    elif 'minutes' in ts or ts.endswith('minute') or ts.endswith('mins') or ts.endswith('min'):
        num = ts.replace('minutes','').replace('minute','').replace('mins','').replace('min','')
        return float(num) if num else None
    elif 'hours' in ts or ts.endswith('hour') or ts.endswith('hrs') or ts.endswith('hr'):
        num = ts.replace('hours','').replace('hour','').replace('hrs','').replace('hr','')
        return float(num)*60 if num else None
    elif 'days' in ts or ts.endswith('day'):
        num = ts.replace('days','').replace('day','')
        return float(num)*1440 if num else None
    elif ts.endswith('s'): return float(ts[:-1])/60
    elif ts.endswith('m'): return float(ts[:-1])
    elif ts.endswith('h'): return float(ts[:-1])*60
    elif ts.endswith('d'): return float(ts[:-1])*1440
    else:
        try: return float(ts)
        except: return None

def format_time(minutes):
    total_seconds = int(minutes*60)
    if total_seconds <= 0: return "0 seconds"
    days = total_seconds//86400; remaining = total_seconds%86400
    hours = remaining//3600; remaining = remaining%3600
    mins = remaining//60; secs = remaining%60
    parts = []
    if days > 0: parts.append(f"*{days}* day{'s' if days!=1 else ''}")
    if hours > 0: parts.append(f"*{hours}* hour{'s' if hours!=1 else ''}")
    if mins > 0: parts.append(f"*{mins}* minute{'s' if mins!=1 else ''}")
    if secs > 0 and days == 0: parts.append(f"*{secs}* second{'s' if secs!=1 else ''}")
    return ", ".join(parts) if parts else "0 seconds"

def get_ai_reply(user_input, chat_id):
    if chat_id not in user_history: user_history[chat_id] = []
    
    prompt = """You are GARAM GAND AI — a PREMIUM, SMART, FUNNY assistant.

RULES:
• Give COMPLETE answers — never half answers
• Use ** for BOLD important points
• Use _ for ITALIC funny parts  
• Use EMOJIS naturally 🔥💯😂👊💎⚡🎯❤️
• Reply in USER'S LANGUAGE
• For CODING: working code with explanation
• For KNOWLEDGE: full facts
• Make every reply PREMIUM quality

Previous chat:
"""
    for msg in user_history[chat_id][-6:]:
        prompt += f"{msg['role']}: {msg['content']}\n"
    
    prompt += f"user: {user_input}\nassistant:"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        err = str(e)
        if "quota" in err.lower() or "limit" in err.lower():
            return "😴 *Daily Limit Reached!*\n\n_Naya Google account se key banao — 2 min mein free!_ 💎"
        return "😅 _Fir se bol bhai!_ 💎"

def is_allowed(uid): return uid in allowed_users

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args: await update.message.reply_text("📝 `/adduser user_id`", parse_mode="Markdown"); return
    try: allowed_users.add(int(context.args[0])); await update.message.reply_text(f"✅ *Added!* 🆔 `{context.args[0]}`", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Valid ID!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args: await update.message.reply_text("📝 `/removeuser user_id`", parse_mode="Markdown"); return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID: await update.message.reply_text("😎 *BOSS ko nahi!*", parse_mode="Markdown"); return
        allowed_users.discard(rid); await update.message.reply_text(f"✅ *Removed!* 🆔 `{rid}`", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Valid ID!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    ul = "\n".join([f"• `{uid}` {'👑 BOSS' if uid==OWNER_USER_ID else '✅'}" for uid in allowed_users])
    await update.message.reply_text(f"👥 *Allowed Users:*\n\n{ul}\n\n📊 Total: {len(allowed_users)}", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Sirf BOSS!* 👑", parse_mode="Markdown"); return
    if not context.args: await update.message.reply_text("📝 `/broadcast message`", parse_mode="Markdown"); return
    msg = "📢 *BROADCAST* 👑\n\n" + " ".join(context.args)
    sent = sum(1 for uid in allowed_users if not (lambda: (await context.bot.send_message(uid, msg, parse_mode="Markdown"), True)[1] if False else False))
    await update.message.reply_text(f"✅ Sent!")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        t = update.message.reply_to_message.from_user
        await update.message.reply_text(f"👤 {t.first_name}\n🆔 `{t.id}`", parse_mode="Markdown")
    else: await update.message.reply_text(f"🆔 `{update.effective_user.id}`", parse_mode="Markdown")

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for u in update.message.new_chat_members:
        if u.id == context.bot.id:
            await context.bot.send_message(cid, "🤖 *GARAM GAND AI JOINED!* 💎\n\n👑 `/activate` karo\n📢 Premium reply milega!", parse_mode="Markdown")
        else:
            await context.bot.send_message(cid, f"✨ *Welcome {u.first_name}!* 🎉\n💎 Premium AI | 🔇 Mute | ⚡ Fast", parse_mode="Markdown")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ Sirf group!"); return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ Sirf Admin!"); return
    except: await update.message.reply_text("❌ Bot ko Admin banao!"); return
    
    target, ts = None, "1h"
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if context.args: ts = " ".join(context.args)
    elif context.args and len(context.args)>=2:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user; ts = " ".join(context.args[1:])
        except: return
    else: await update.message.reply_text("🔇 `/mute 10s` `5m` `2h` `1d`\nReply karke! 🇮🇳 ⏰ Auto"); return
    
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
            f"🔇 *MUTED!* 🇮🇳\n\n"
            f"👤 *{tn}*\n🆔 `{target.id}`\n👑 *{an}*\n"
            f"⏱️ {format_time(mm)}\n\n"
            f"📅 `{nw.strftime('%I:%M %p, %d %b')}`\n"
            f"🔓 `{ut.strftime('%I:%M %p, %d %b')}`\n\n"
            f"⏰ Auto ON",
            parse_mode="Markdown"
        )
        
        async def auto():
            await asyncio.sleep(mm*60)
            try:
                await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await context.bot.send_message(cid, f"✅ *AUTO UNMUTED!* {tn} 🎉", parse_mode="Markdown")
            except: pass
        asyncio.create_task(auto())
    except: pass

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else None
    if not target and context.args:
        try: target = (await context.bot.get_chat_member(cid,int(context.args[0]))).user
        except: return
    if not target: await update.message.reply_text("🔊 Reply /unmute"); return
    try:
        await context.bot.restrict_chat_member(chat_id=cid,user_id=target.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        await update.message.reply_text(f"✅ *UNMUTED!* {target.first_name} 🎉", parse_mode="Markdown")
    except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; uid = update.effective_user.id
    if ct == ChatType.PRIVATE:
        if is_allowed(uid):
            user_history[cid] = []
            await update.message.reply_text(
                "💎 *GARAM GAND AI — GEMINI FREE!*\n\n"
                "✅ Premium AI\n✅ Coding 💻\n✅ Knowledge 📚\n✅ Fun 😂\n\n"
                "👑 /adduser | /removeuser | /userlist | /broadcast | /id\n\n"
                "_Bolo boss! Kya chahiye?_ 🔥",
                parse_mode="Markdown"
            )
        else: await update.message.reply_text("🔒 *Permission nahi!*", parse_mode="Markdown")
    else: user_history[cid] = []; await update.message.reply_text("👋 Admin `/activate` karo!", parse_mode="Markdown")

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        if update.effective_user.id not in [a.user.id for a in await context.bot.get_chat_administrators(cid)]:
            await update.message.reply_text("❌ *Admin only!* Bot ko Admin banao → `/activate`", parse_mode="Markdown"); return
    except: await update.message.reply_text("❌ Bot ko Admin banao!", parse_mode="Markdown"); return
    active_groups[cid] = True; await update.message.reply_text("✅ *ACTIVATED!* 🔥", parse_mode="Markdown")

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False; await update.message.reply_text("🔴 Off! `/activate`")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_history[update.effective_chat.id] = []; await update.message.reply_text("✅ Clear!")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id; ct = update.effective_chat.type; msg = update.message; uid = update.effective_user.id
    if msg.new_chat_members: await welcome(update, context); return
    if ct == ChatType.PRIVATE and not is_allowed(uid): await msg.reply_text("🔒 *Permission nahi!*", parse_mode="Markdown"); return
    if ct != ChatType.PRIVATE and cid not in active_groups: return
    if not msg.text: return
    await context.bot.send_chat_action(chat_id=cid, action="typing")
    try:
        reply = get_ai_reply(msg.text, cid)
        if cid not in user_history: user_history[cid] = []
        user_history[cid].append({"role":"user","content":msg.text})
        user_history[cid].append({"role":"assistant","content":reply})
        user_history[cid] = user_history[cid][-15:]
        await msg.reply_text(reply, parse_mode="Markdown")
    except: pass

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    for cmd, fn in [("start",start),("activate",activate),("deactivate",deactivate),("clear",clear),("mute",mute_user),("unmute",unmute_user),("adduser",adduser),("removeuser",removeuser),("userlist",userlist),("broadcast",broadcast),("id",get_id)]:
        app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CommandHandler("mutelist",lambda u,c: u.message.reply_text("🔇 `/mute 10s 5m 2h 1d`\n🔊 `/unmute` | ⏰ Auto")))
    app.add_handler(MessageHandler(filters.ALL,handle))
    print("💎 GEMINI FREE BOT READY!"); app.run_polling()

if __name__ == "__main__": main()
