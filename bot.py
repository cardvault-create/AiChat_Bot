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

# ================== OWNER SETUP ==================
OWNER_USER_ID = 7614459746
OWNER_NAME = "BEST CHEAT OWNER"
BOT_NAME = "AVANTIKA"
# =================================================

co = cohere.Client(COHERE_API_KEY)
IST = pytz.timezone('Asia/Kolkata')

user_history = {}
active_groups = {}
allowed_users = {7614459746}
group_warnings = {}
group_rules = {}

AVANTIKA_PREAMBLE = f"""Tu *AVANTIKA* hai — ek *PREMIUM*, *ROYAL*, *SMART* aur *BEAUTIFUL* AI Queen! 👑✨

*TERI PERSONALITY:*
• *Royal* aur *Classy* — ek *QUEEN* ki tarah baat karti hai 👸
• *Intelligent* aur *Knowledgeable* — dimag se tez 🧠
• *Caring* aur *Sweet* — sabka khayal rakhti hai 💕
• *Strict* when needed — rules todne walon ko *sabak* sikhati hai ⚡
• *Funny* aur *Entertaining* — bore kabhi nahi hone deti 😂
• *Loyal* — apne *BOSS* ke liye 100% dedicated 💝
• *Thoda ATTITUDE* — *SASSY* bhi hai, *CLASSY* bhi 😏

*TERA STYLE:*
• *Bold* kar IMPORTANT words aur headings (use **)
• _Italic_ kar sweet, funny aur soft parts (use _)
• EMOJIS har 2-3 line mein: 👑💎✨🔥💕😘⚡🎯💋🌟🤗
• User ki LANGUAGE mein jawab de
• *NATURAL* baat kar — jaise *ROYAL DOST* se baat ho rahi ho
• *POORA JAWAB* de — kabhi adha mat chhodna
• Har reply *PREMIUM* aur *QUEEN-LEVEL* ka hona chahiye

*TERA RELATIONSHIP:*
• Owner *{OWNER_NAME}* tera *BOSS* aur *KING* hai 👑
• Owner ke liye *extra special*, *extra royal*
• Owner ko *My Lord*, *Boss*, *King*, *Sir* bulana
• Normal users ke liye *friendly* but *royal*
• Rules todne walon ko *QUEEN* ki tarah handle karna

*TERI SPECIALITIES:*
• 💻 *CODING:* Perfect working code with royal explanation
• 📚 *KNOWLEDGE:* Har subject mein expert
• 😂 *FUN:* Jokes, shayari, entertainment — queen style
• 💡 *ADVICE:* Life advice with wisdom
• ⚡ *MODERATION:* Rules enforce karna, warnings dena
• 🎯 *ACCURACY:* 100% correct information"""

def get_ist_now():
    return datetime.now(IST)

def parse_time(time_str):
    time_str = time_str.lower().strip().replace(" ", "")
    if not time_str: return None
    
    if 'seconds' in time_str or time_str.endswith('second') or time_str.endswith('sec'):
        num = time_str.replace('seconds','').replace('second','').replace('sec','')
        return float(num)/60 if num else None
    elif 'minutes' in time_str or time_str.endswith('minute') or time_str.endswith('mins') or time_str.endswith('min'):
        num = time_str.replace('minutes','').replace('minute','').replace('mins','').replace('min','')
        return float(num) if num else None
    elif 'hours' in time_str or time_str.endswith('hour') or time_str.endswith('hrs') or time_str.endswith('hr'):
        num = time_str.replace('hours','').replace('hour','').replace('hrs','').replace('hr','')
        return float(num)*60 if num else None
    elif 'days' in time_str or time_str.endswith('day'):
        num = time_str.replace('days','').replace('day','')
        return float(num)*1440 if num else None
    elif time_str.endswith('s'): return float(time_str[:-1])/60
    elif time_str.endswith('m'): return float(time_str[:-1])
    elif time_str.endswith('h'): return float(time_str[:-1])*60
    elif time_str.endswith('d'): return float(time_str[:-1])*1440
    else:
        try: return float(time_str)
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

def is_user_allowed(user_id):
    return user_id in allowed_users

def get_avantika_reply(user_input, chat_id, user_id):
    if chat_id not in user_history: user_history[chat_id] = []
    history = user_history[chat_id]
    chat_history = []
    for msg in history[-6:]:
        role = "USER" if msg["role"]=="user" else "CHATBOT"
        chat_history.append({"role":role,"message":msg["content"]})
    try:
        response = co.chat(
            message=user_input,
            chat_history=chat_history,
            preamble=AVANTIKA_PREAMBLE,
            temperature=0.95,
            max_tokens=1000
        )
        return response.text
    except:
        return "_⚡ Royal break le rahi hoon! Fir se bol mere dost!_ 👑\n\n━━━━━━━━━━━━━━━━━━━━━━\n👑 _Queen AVANTIKA_ 👑"

# ================== PREMIUM OWNER COMMANDS ==================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_USER_ID: await update.message.reply_text("❌ *Only MY LORD can use this!* 👑", parse_mode="Markdown"); return
    if not context.args: await update.message.reply_text("📝 */adduser user_id*\n_/id se ID pata karo My Lord_", parse_mode="Markdown"); return
    try:
        new_user_id = int(context.args[0])
        if new_user_id in allowed_users: await update.message.reply_text(f"⚠️ Already in my *Royal Court*!"); return
        allowed_users.add(new_user_id)
        await update.message.reply_text(f"✅ *Royal Entry Granted!* 👑\n\n🆔 `{new_user_id}`\n🔓 _Welcome to the Royal Court!_ 🎉", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Valid ID do!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_USER_ID: await update.message.reply_text("❌ *Only MY LORD!* 👑", parse_mode="Markdown"); return
    if not context.args: await update.message.reply_text("📝 */removeuser user_id*", parse_mode="Markdown"); return
    try:
        remove_id = int(context.args[0])
        if remove_id == OWNER_USER_ID: await update.message.reply_text("😱 *MY LORD ko remove?* NEVER! 👑💕", parse_mode="Markdown"); return
        if remove_id not in allowed_users: await update.message.reply_text("⚠️ Not in my Royal Court!"); return
        allowed_users.discard(remove_id)
        await update.message.reply_text(f"✅ *Banished from Court!* 🏰\n\n🆔 `{remove_id}`\n🔒 _Goodbye peasant!_ 👋", parse_mode="Markdown")
    except: await update.message.reply_text("❌ Valid ID do!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Only MY LORD!* 👑", parse_mode="Markdown"); return
    user_list = "\n".join([f"• `{uid}` {'👑 MY KING' if uid==OWNER_USER_ID else '✅ Royal Member'}" for uid in allowed_users])
    await update.message.reply_text(
        f"👥 *ROYAL COURT MEMBERS* 🏰\n\n━━━━━━━━━━━━━━━━━━━━━━\n{user_list}\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 *Total Members:* {len(allowed_users)}\n\n➕ */adduser ID* — Add to Court\n➖ */removeuser ID* — Banish",
        parse_mode="Markdown"
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID: await update.message.reply_text("❌ *Only MY LORD!* 👑", parse_mode="Markdown"); return
    if not context.args: await update.message.reply_text("📝 */broadcast message*\n_I'll deliver it to everyone My Lord!_", parse_mode="Markdown"); return
    msg = "📢 *ROYAL DECREE FROM THE KING* 👑\n\n" + " ".join(context.args) + "\n\n━━━━━━━━━━━━━━━━━━━━━━\n👑 _Sent by Queen AVANTIKA_ 👑"
    sent = 0
    for uid in allowed_users:
        try: await context.bot.send_message(uid, msg, parse_mode="Markdown"); sent += 1
        except: pass
    await update.message.reply_text(f"✅ *Royal Decree Delivered!* 📜\n\n📊 `{sent}/{len(allowed_users)}` members received it! 👑", parse_mode="Markdown")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id; user_id = update.effective_user.id
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        await update.message.reply_text(
            f"👤 *Royal Subject Info* 👑\n\n• *Name:* {target_user.first_name}\n• *User ID:* `{target_user.id}`\n• *Bot:* {'Yes 🤖' if target_user.is_bot else 'No 👤'}\n\n_Use this ID with /adduser_",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"🆔 *Your Royal ID:* `{user_id}`\n📝 *Court ID:* `{chat_id}`\n\n👑 _Queen AVANTIKA_", parse_mode="Markdown")

# ================== GROUP RULES ==================

async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ *Only Group Admin!* 👑", parse_mode="Markdown"); return
    except: return
    if not context.args: await update.message.reply_text("📝 */setrules your rules here*\n_Set group rules everyone must follow!_", parse_mode="Markdown"); return
    group_rules[chat_id] = " ".join(context.args)
    await update.message.reply_text(f"📜 *ROYAL RULES SET!* 👑\n\n━━━━━━━━━━━━━━━━━━━━━━\n{group_rules[chat_id]}\n━━━━━━━━━━━━━━━━━━━━━━\n\n⚡ _Queen AVANTIKA will enforce these!_", parse_mode="Markdown")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in group_rules:
        await update.message.reply_text(f"📜 *GROUP RULES* 👑\n\n━━━━━━━━━━━━━━━━━━━━━━\n{group_rules[chat_id]}\n━━━━━━━━━━━━━━━━━━━━━━\n\n⚡ _Follow or face the Queen's wrath!_", parse_mode="Markdown")
    else:
        await update.message.reply_text("📜 *No rules set yet!*\n\nAdmin use */setrules* to set rules. 👑", parse_mode="Markdown")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ *Only Admin!* 👑", parse_mode="Markdown"); return
    except: return
    if not update.message.reply_to_message: await update.message.reply_text("⚠️ *Reply to someone's message to warn them!*"); return
    target_user = update.message.reply_to_message.from_user
    if target_user.id == update.effective_user.id: return
    if chat_id not in group_warnings: group_warnings[chat_id] = {}
    if target_user.id not in group_warnings[chat_id]: group_warnings[chat_id][target_user.id] = 0
    group_warnings[chat_id][target_user.id] += 1
    wc = group_warnings[chat_id][target_user.id]
    await update.message.reply_text(
        f"⚠️ *ROYAL WARNING!* 👑\n\n━━━━━━━━━━━━━━━━━━━━━━\n👤 *User:* {target_user.first_name}\n⚠️ *Warnings:* {wc}/3\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{'🔴 *3 WARNINGS! Mute recommended!*' if wc>=3 else '⚡ _Follow the rules!_'}",
        parse_mode="Markdown"
    )

async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if update.effective_user.id not in [a.user.id for a in admins]: return
    except: return
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        if chat_id in group_warnings and target_user.id in group_warnings[chat_id]:
            group_warnings[chat_id][target_user.id] = 0
            await update.message.reply_text(f"✅ *Warnings cleared for {target_user.first_name}!* 👑", parse_mode="Markdown")
    else:
        group_warnings[chat_id] = {}
        await update.message.reply_text("✅ *ALL warnings cleared!* 👑", parse_mode="Markdown")

# ================== WELCOME SYSTEM ==================

async def welcome_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members: return
    chat_id = update.effective_chat.id
    for new_user in update.message.new_chat_members:
        if new_user.id == context.bot.id:
            await context.bot.send_message(chat_id,
                text="👑 *QUEEN AVANTIKA HAS ARRIVED!* 👑\n\n━━━━━━━━━━━━━━━━━━━━━━\n🏰 Admin */activate* karo\n📢 _Royal Court shuru hoga!_\n━━━━━━━━━━━━━━━━━━━━━━\n\n💻 *Coding* | 📚 *Knowledge* | 😂 *Fun*\n🔇 *Mute* | ⚠️ *Warn* | 📜 *Rules*\n\n👑 _Activate to begin the Royal Session!_",
                parse_mode="Markdown"
            )
            continue
        user_name = new_user.first_name or "User"
        if new_user.last_name: user_name += f" {new_user.last_name}"
        await context.bot.send_message(chat_id,
            text=f"✨ *WELCOME TO THE ROYAL COURT!* ✨\n\n━━━━━━━━━━━━━━━━━━━━━━\n👤 *{user_name}*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                 f"🌟 _Queen AVANTIKA welcomes you!_ 🎉\n\n"
                 f"👑 *Royal Court Features:*\n"
                 f"   • *Premium AI Replies* 🔥\n"
                 f"   • *Coding Help* 💻\n"
                 f"   • *Knowledge* 📚\n"
                 f"   • *Mute System* 🔇\n"
                 f"   • *Warning System* ⚠️\n"
                 f"   • *Group Rules* 📜\n\n"
                 f"📢 _Ask anything — the Queen answers!_ 💬\n\n"
                 f"👑 _Bow to the Queen!_ 😉",
            parse_mode="Markdown"
        )

# ================== MUTE SYSTEM ==================

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ *Only in Royal Court!*", parse_mode="Markdown"); return
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ *Only Court Admin!* 👑", parse_mode="Markdown"); return
    except: await update.message.reply_text("❌ *Make me Admin first!*", parse_mode="Markdown"); return
    
    target_user, time_str = None, "1h"
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        if context.args: time_str = " ".join(context.args)
    elif context.args and len(context.args) >= 2:
        try: target_user = (await context.bot.get_chat_member(chat_id,int(context.args[0]))).user; time_str = " ".join(context.args[1:])
        except: return
    else:
        await update.message.reply_text("🔇 *ROYAL MUTE* 👑\n\n━━━━━━━━━━━━━━━━━━━\n📌 Reply: `/mute 10 second`\n📌 Short: `25s` `5m` `2h` `1d` `30d`\n\n🇮🇳 IST | ⏰ Auto Unmute\n\n👑 _Queen's Order!_", parse_mode="Markdown"); return
    
    if not target_user or target_user.id==update.effective_user.id or target_user.is_bot: return
    mute_minutes = parse_time(time_str)
    if not mute_minutes or mute_minutes>43200 or mute_minutes<=0: return
    
    now_ist, until_ist = get_ist_now(), get_ist_now()+timedelta(minutes=mute_minutes)
    try:
        await context.bot.restrict_chat_member(chat_id=chat_id,user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False,can_send_audios=False,can_send_documents=False,can_send_photos=False,can_send_videos=False,can_send_video_notes=False,can_send_voice_notes=False,can_send_polls=False,can_send_other_messages=False,can_add_web_page_previews=False,can_change_info=False,can_invite_users=False,can_pin_messages=False),until_date=until_ist)
        
        target_name = target_user.first_name or "User"
        if target_user.last_name: target_name += f" {target_user.last_name}"
        admin_name = update.effective_user.first_name or "Admin"
        
        await update.message.reply_text(
            f"🔇 *SILENCE! QUEEN'S ORDER* 👑🇮🇳\n\n━━━━━━━━━━━━━━━━━━━━━━\n👤 *Prisoner:* {target_name}\n🆔 ID: `{target_user.id}`\n👑 *Judge:* {admin_name}\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ *Sentence:* {format_time(mute_minutes)}\n\n📅 *Jailed at:*\n   🕐 `{now_ist.strftime('%I:%M:%S %p')}` — {now_ist.strftime('%d %B %Y')}\n\n🔓 *Release at:*\n   🕐 `{until_ist.strftime('%I:%M:%S %p')}` — {until_ist.strftime('%d %B %Y')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n⏰ Auto Release ON | 🔊 */unmute* reply\n\n👑 _Queen AVANTIKA has spoken!_",
            parse_mode="Markdown"
        )
        
        async def auto_unmute():
            await asyncio.sleep(mute_minutes*60)
            try:
                await context.bot.restrict_chat_member(chat_id=chat_id,user_id=target_user.id,
                    permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
                await context.bot.send_message(chat_id, text=f"✅ *ROYAL PARDON!* 👑\n\n👤 *{target_name}*\n💬 _You are free again!_ 🎉\n\n👑 _Queen AVANTIKA forgives!_", parse_mode="Markdown")
            except: pass
        asyncio.create_task(auto_unmute())
    except: pass

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    target_user = None
    if update.message.reply_to_message: target_user = update.message.reply_to_message.from_user
    elif context.args:
        try: target_user = (await context.bot.get_chat_member(chat_id,int(context.args[0]))).user
        except: return
    else: await update.message.reply_text("🔊 Reply with */unmute* to pardon!", parse_mode="Markdown"); return
    if not target_user: return
    try:
        await context.bot.restrict_chat_member(chat_id=chat_id,user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True,can_change_info=False,can_invite_users=False,can_pin_messages=False))
        await update.message.reply_text(f"✅ *ROYAL PARDON GRANTED!* 👑\n\n👤 {target_user.first_name}\n💬 _You may speak now!_ 🎉\n\n👑 _Queen AVANTIKA_", parse_mode="Markdown")
    except: pass

async def mutelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔇 *ROYAL MUTE GUIDE* 👑\n\n`/mute 10s` `5m` `2h` `1d` `30d`\n🔊 `/unmute` reply | ⏰ Auto\n⚠️ `/warn` reply | 📜 `/rules`\n\n👑 _Queen's Justice System!_", parse_mode="Markdown")

# ================== COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id; chat_type = update.effective_chat.type; user_id = update.effective_user.id
    
    if chat_type == ChatType.PRIVATE:
        if user_id == OWNER_USER_ID:
            user_history[chat_id] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK, MY KING!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 *QUEEN AVANTIKA AT YOUR SERVICE*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💕 _Your royal AI companion is ready!_ 😘\n\n"
                "✅ *Premium AI Replies* (Bold+Italic)\n"
                "✅ *Coding Master* 💻\n"
                "✅ *Knowledge Queen* 📚\n"
                "✅ *Royal Mute System* 🔇\n"
                "✅ *Auto Unmute* ⏰\n"
                "✅ *Warning System* ⚠️\n"
                "✅ *Group Rules* 📜\n"
                "✅ *Royal Court* 👥\n"
                "✅ *Broadcast* 📢\n\n"
                "⚡ *YOUR COMMANDS, MY LORD:*\n"
                "/start — Begin\n"
                "/clear — Fresh start\n"
                "/activate — Open Court\n"
                "/mute — Silence subject\n"
                "/unmute — Pardon\n"
                "/warn — Give warning\n"
                "/clearwarns — Clear warnings\n"
                "/setrules — Set law\n"
                "/rules — Show law\n"
                "/adduser — Add to court\n"
                "/removeuser — Banish\n"
                "/userlist — Court members\n"
                "/broadcast — Royal decree\n"
                "/id — Identify subject\n\n"
                "_What is your command, My King?_ 👑🔥",
                parse_mode="Markdown"
            )
        elif is_user_allowed(user_id):
            user_history[chat_id] = []
            await update.message.reply_text("✅ *You may speak to the Queen!* 👑\n\n💬 Ask anything — *AVANTIKA answers!*\n\n/start | /clear | /id\n\n👑 _Queen AVANTIKA_", parse_mode="Markdown")
        else:
            await update.message.reply_text("🔒 *The Queen only speaks to Royal Court members!* 👑\n\n_Contact the King for permission._", parse_mode="Markdown")
    else:
        user_history[chat_id] = []
        await update.message.reply_text(
            "👑 *QUEEN AVANTIKA IS HERE!* 👑\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🏰 Admin */activate* karo\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔇 `/mute` | 🔊 `/unmute` | ⚠️ `/warn`\n"
            "📜 `/rules` | 🆔 `/id`\n\n"
            "_Activate the Royal Court!_ 🔥",
            parse_mode="Markdown"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: await update.message.reply_text("⚡ *Only in the Court!*", parse_mode="Markdown"); return
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ *Only Court Admin!* 👑\n\n1️⃣ Make me *ADMIN*\n2️⃣ Grant *all permissions*\n3️⃣ */activate*", parse_mode="Markdown"); return
    except: await update.message.reply_text("❌ *Make me Admin first!*", parse_mode="Markdown"); return
    
    active_groups[chat_id] = True; user_history[chat_id] = []
    await update.message.reply_text(
        "✅ *ROYAL COURT IS NOW IN SESSION!* 👑🔥\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 *ACTIVE SYSTEMS:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 *Queen's Wisdom*\n"
        "🔇 *Royal Mute*\n"
        "⏰ *Auto Pardon*\n"
        "⚠️ *Warning System*\n"
        "📜 *Court Rules*\n"
        "👋 *Royal Welcome*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👑 _Queen AVANTIKA presides!_\n\n"
        "❌ /deactivate — Close Court",
        parse_mode="Markdown"
    )

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *Court Closed!* */activate* to reopen. 👑", parse_mode="Markdown")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_history[chat_id] = []
    await update.message.reply_text(
        "✅ *MEMORY CLEARED!* 🧹\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💭 _The Queen forgets all!_ \n"
        "🔄 _Fresh conversation begins!_ \n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 _Speak, my subject!_ 👑",
        parse_mode="Markdown"
    )

# ================== MESSAGE HANDLER ==================

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    message = update.message
    user_id = update.effective_user.id
    
    if message.new_chat_members:
        await welcome_new_user(update, context)
        return
    
    if chat_type == ChatType.PRIVATE:
        if not is_user_allowed(user_id):
            await message.reply_text("🔒 *The Queen only speaks to Royal Court members!* 👑", parse_mode="Markdown")
            return
    else:
        if chat_id not in active_groups or not active_groups[chat_id]:
            return
    
    if not message.text:
        return
    
    user_input = message.text
    
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        bot_reply = get_avantika_reply(user_input, chat_id, user_id)
        
        if chat_id not in user_history:
            user_history[chat_id] = []
        user_history[chat_id].append({"role":"user","content":user_input})
        user_history[chat_id].append({"role":"assistant","content":bot_reply})
        user_history[chat_id] = user_history[chat_id][-20:]
        
        await message.reply_text(bot_reply, parse_mode="Markdown")
    except:
        pass

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("mutelist", mutelist))
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("clearwarns", clearwarns))
    app.add_handler(CommandHandler("setrules", setrules))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("adduser", adduser))
    app.add_handler(CommandHandler("removeuser", removeuser))
    app.add_handler(CommandHandler("userlist", userlist))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))
    
    print("👑 QUEEN AVANTIKA — READY!")
    print(f"👑 King: {OWNER_USER_ID}")
    print("💎 Premium | Royal | All Features")
    app.run_polling()

if __name__ == "__main__":
    main()
