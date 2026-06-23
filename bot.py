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

# ================== ROYAL CONFIGURATION ==================
OWNER_USER_ID = 7614459746
OWNER_NAME = "BEST CHEAT OWNER"
BOT_NAME = "Avantika AI"
# =========================================================

co = cohere.Client(COHERE_API_KEY)
IST = pytz.timezone('Asia/Kolkata')

user_history = {}
active_groups = {}
allowed_users = {7614459746}
group_warnings = {}
group_rules = {}

# ================== AVANTIKA'S PERSONALITY ==================
AVANTIKA_PREAMBLE = f"""You are *{BOT_NAME}* — a *PREMIUM*, *ROYAL*, *SMART* AI Queen! 👑✨

*PERSONALITY:*
• *Royal* and *Classy* 👸
• *Intelligent* & *Knowledgeable* 🧠
• *Caring* & *Sweet* 💕
• *Strict* when rules are broken ⚡
• *Funny* & *Entertaining* 😂
• *Loyal* to your King *{OWNER_NAME}* 💝

*STYLE:*
• Use ** for *BOLD* important words
• Use _ for *ITALIC* soft/romantic parts
• EMOJIS naturally: 👑💎✨🔥💕😘⚡🎯💋🌟
• Reply in USER'S LANGUAGE (Hindi/English/Hinglish)
• Be *NATURAL* and *FRIENDLY*
• Give *COMPLETE* answers — never half
• Every reply must feel *PREMIUM* and *ROYAL*

*SPECIAL:*
• For King *{OWNER_NAME}* → address as *My Lord* / *King* 👑
• For others → be friendly but maintain royal grace"""

# ================== UTILITY FUNCTIONS ==================
def get_ist_now():
    return datetime.now(IST)

def parse_time(ts):
    ts = ts.lower().strip().replace(" ", "")
    if not ts: return None
    # full words
    for word, mult in [('seconds',1/60),('second',1/60),('sec',1/60),
                       ('minutes',1),('minute',1),('mins',1),('min',1),
                       ('hours',60),('hour',60),('hrs',60),('hr',60),
                       ('days',1440),('day',1440)]:
        if ts.endswith(word):
            try: return float(ts[:-len(word)]) * mult
            except: pass
    # short codes
    try:
        if ts.endswith('s'): return float(ts[:-1])/60
        if ts.endswith('m'): return float(ts[:-1])
        if ts.endswith('h'): return float(ts[:-1])*60
        if ts.endswith('d'): return float(ts[:-1])*1440
        return float(ts)
    except:
        return None

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

def is_allowed(uid):
    return uid in allowed_users

def get_royal_reply(text, chat_id):
    if chat_id not in user_history:
        user_history[chat_id] = []
    chat_history = []
    for msg in user_history[chat_id][-6:]:
        role = "USER" if msg["role"] == "user" else "CHATBOT"
        chat_history.append({"role": role, "message": msg["content"]})
    try:
        response = co.chat(
            message=text,
            chat_history=chat_history,
            preamble=AVANTIKA_PREAMBLE,
            temperature=0.95,
            max_tokens=1000
        )
        return response.text
    except:
        return "_⚡ Royal break! Fir se bol mere dost!_ 👑\n\n━━━━━━━━━━━━━━━━━━━━━━\n👑 _Avantika AI_ 👑"

# ================== OWNER COMMANDS ==================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Only MY LORD can use this!* 👑", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("📝 */adduser user_id*\n_/id se ID pata karo My Lord_", parse_mode="Markdown")
        return
    try:
        new_id = int(context.args[0])
        if new_id in allowed_users:
            await update.message.reply_text("⚠️ Already in my *Royal Court*!")
            return
        allowed_users.add(new_id)
        await update.message.reply_text(f"✅ *Royal Entry Granted!* 👑\n🆔 `{new_id}`\n🔓 _Welcome to the Royal Court!_ 🎉", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Valid User ID do!")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Only MY LORD!* 👑", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("📝 */removeuser user_id*", parse_mode="Markdown")
        return
    try:
        rid = int(context.args[0])
        if rid == OWNER_USER_ID:
            await update.message.reply_text("😱 *NEVER My Lord!* 👑💕", parse_mode="Markdown")
            return
        if rid not in allowed_users:
            await update.message.reply_text("⚠️ Not in my Royal Court!")
            return
        allowed_users.discard(rid)
        await update.message.reply_text(f"✅ *Banished from Court!* 🏰\n🆔 `{rid}`\n🔒 _Goodbye!_ 👋", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Valid User ID do!")

async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Only MY LORD!* 👑", parse_mode="Markdown")
        return
    ul = "\n".join([f"• `{uid}` {'👑 MY KING' if uid==OWNER_USER_ID else '✅ Royal Member'}" for uid in allowed_users])
    await update.message.reply_text(
        f"👥 *ROYAL COURT MEMBERS* 🏰\n\n━━━━━━━━━━━━━━━━━━━━━━\n{ul}\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 *Total:* {len(allowed_users)}\n\n➕ */adduser ID* — Add to Court\n➖ */removeuser ID* — Banish",
        parse_mode="Markdown"
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_USER_ID:
        await update.message.reply_text("❌ *Only MY LORD!* 👑", parse_mode="Markdown")
        return
    if not context.args:
        await update.message.reply_text("📝 */broadcast your message*\n_I'll deliver it to everyone My Lord!_", parse_mode="Markdown")
        return
    msg = "📢 *ROYAL DECREE FROM THE KING* 👑\n\n" + " ".join(context.args) + "\n\n━━━━━━━━━━━━━━━━━━━━━━\n👑 _Sent by Avantika AI_ 👑"
    sent = 0
    for uid in allowed_users:
        try:
            await context.bot.send_message(uid, msg, parse_mode="Markdown")
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ *Royal Decree Delivered!* 📜\n📊 `{sent}/{len(allowed_users)}` members received it! 👑", parse_mode="Markdown")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        await update.message.reply_text(
            f"👤 *Royal Subject Info* 👑\n\n• *Name:* {target.first_name}\n• *User ID:* `{target.id}`\n• *Bot:* {'Yes 🤖' if target.is_bot else 'No 👤'}\n\n_Use this ID with /adduser_",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"🆔 *Your Royal ID:* `{update.effective_user.id}`\n📝 *Court ID:* `{update.effective_chat.id}`\n\n👑 _Avantika AI_", parse_mode="Markdown")

# ================== GROUP MANAGEMENT ==================
async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        admins = await context.bot.get_chat_administrators(cid)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ *Only Court Admin!* 👑", parse_mode="Markdown")
            return
    except:
        return
    if not context.args:
        await update.message.reply_text("📝 */setrules your rules here*\n_Set group rules everyone must follow!_", parse_mode="Markdown")
        return
    group_rules[cid] = " ".join(context.args)
    await update.message.reply_text(f"📜 *ROYAL RULES SET!* 👑\n\n━━━━━━━━━━━━━━━━━━━━━━\n{group_rules[cid]}\n━━━━━━━━━━━━━━━━━━━━━━\n\n⚡ _Avantika will enforce these!_", parse_mode="Markdown")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in group_rules:
        await update.message.reply_text(f"📜 *COURT RULES* 👑\n\n━━━━━━━━━━━━━━━━━━━━━━\n{group_rules[cid]}\n━━━━━━━━━━━━━━━━━━━━━━\n\n⚡ _Follow or face the Queen's wrath!_", parse_mode="Markdown")
    else:
        await update.message.reply_text("📜 *No rules set yet!*\nAdmin use */setrules* to set. 👑", parse_mode="Markdown")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        admins = await context.bot.get_chat_administrators(cid)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ *Only Court Admin!* 👑", parse_mode="Markdown")
            return
    except:
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ *Reply to someone's message to warn them!*")
        return
    target = update.message.reply_to_message.from_user
    if target.id == update.effective_user.id: return
    if cid not in group_warnings:
        group_warnings[cid] = {}
    if target.id not in group_warnings[cid]:
        group_warnings[cid][target.id] = 0
    group_warnings[cid][target.id] += 1
    wc = group_warnings[cid][target.id]
    await update.message.reply_text(
        f"⚠️ *ROYAL WARNING!* 👑\n\n━━━━━━━━━━━━━━━━━━━━━━\n👤 *User:* {target.first_name}\n⚠️ *Warnings:* {wc}/3\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{'🔴 *3 WARNINGS! Mute recommended!*' if wc>=3 else '⚡ _Follow the rules!_'}",
        parse_mode="Markdown"
    )

async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    try:
        admins = await context.bot.get_chat_administrators(cid)
        if update.effective_user.id not in [a.user.id for a in admins]: return
    except:
        return
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if cid in group_warnings and target.id in group_warnings[cid]:
            group_warnings[cid][target.id] = 0
            await update.message.reply_text(f"✅ *Warnings cleared for {target.first_name}!* 👑", parse_mode="Markdown")
    else:
        group_warnings[cid] = {}
        await update.message.reply_text("✅ *ALL warnings cleared!* 👑", parse_mode="Markdown")

# ================== WELCOME ==================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members: return
    cid = update.effective_chat.id
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            await context.bot.send_message(cid,
                "👑 *AVANTIKA AI HAS ARRIVED!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🏰 Admin */activate* karo\n"
                "📢 _Royal Court shuru hoga!_\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💻 Coding | 📚 Knowledge | 😂 Fun\n"
                "🔇 Mute | ⚠️ Warn | 📜 Rules\n\n"
                "👑 _Activate to begin the Royal Session!_",
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(cid,
                f"✨ *WELCOME TO THE ROYAL COURT!* ✨\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *{user.first_name}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌟 _Avantika welcomes you!_ 🎉\n\n"
                f"👑 *Royal Court Features:*\n"
                f"• Premium AI Replies 🔥\n"
                f"• Coding Help 💻\n"
                f"• Knowledge 📚\n"
                f"• Mute System 🔇\n"
                f"• Warning System ⚠️\n"
                f"• Group Rules 📜\n\n"
                f"📢 _Ask anything — the Queen answers!_ 💬\n\n"
                f"👑 _Bow to the Queen!_ 😉",
                parse_mode="Markdown"
            )

# ================== MUTE SYSTEM ==================
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ *Only in Royal Court!* 👑", parse_mode="Markdown")
        return
    try:
        admins = await context.bot.get_chat_administrators(cid)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text("❌ *Only Court Admin!* 👑", parse_mode="Markdown")
            return
    except:
        await update.message.reply_text("❌ *Make me Admin first!* 👑", parse_mode="Markdown")
        return
    
    target = None
    time_str = "1h"
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        if context.args: time_str = " ".join(context.args)
    elif context.args and len(context.args) >= 2:
        try:
            target = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
            time_str = " ".join(context.args[1:])
        except:
            return
    else:
        await update.message.reply_text(
            "🔇 *ROYAL MUTE* 👑\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📌 Reply: `/mute 10 second`\n"
            "📌 Short: `25s` `5m` `2h` `1d` `30d`\n\n"
            "🇮🇳 IST | ⏰ Auto Unmute\n\n"
            "👑 _Queen's Order!_",
            parse_mode="Markdown"
        )
        return
    
    if not target or target.id == update.effective_user.id or target.is_bot: return
    mute_minutes = parse_time(time_str)
    if not mute_minutes or mute_minutes > 43200 or mute_minutes <= 0: return
    
    now_ist = get_ist_now()
    until_ist = now_ist + timedelta(minutes=mute_minutes)
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=cid, user_id=target.id,
            permissions=ChatPermissions(
                can_send_messages=False, can_send_audios=False, can_send_documents=False,
                can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
                can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
                can_add_web_page_previews=False, can_change_info=False,
                can_invite_users=False, can_pin_messages=False
            ),
            until_date=until_ist
        )
        
        target_name = target.first_name or "User"
        if target.last_name: target_name += f" {target.last_name}"
        admin_name = update.effective_user.first_name or "Admin"
        
        await update.message.reply_text(
            f"🔇 *SILENCE! QUEEN'S ORDER* 👑🇮🇳\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Prisoner:* {target_name}\n"
            f"🆔 ID: `{target.id}`\n"
            f"👑 *Judge:* {admin_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱️ *Sentence:* {format_time(mute_minutes)}\n\n"
            f"📅 *Jailed at:*\n"
            f"   🕐 `{now_ist.strftime('%I:%M:%S %p')}` — {now_ist.strftime('%d %B %Y')}\n\n"
            f"🔓 *Release at:*\n"
            f"   🕐 `{until_ist.strftime('%I:%M:%S %p')}` — {until_ist.strftime('%d %B %Y')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ Auto Release ON | 🔊 */unmute* reply\n\n"
            f"👑 _Avantika has spoken!_",
            parse_mode="Markdown"
        )
        
        async def auto_unmute():
            await asyncio.sleep(mute_minutes * 60)
            try:
                await context.bot.restrict_chat_member(
                    chat_id=cid, user_id=target.id,
                    permissions=ChatPermissions(
                        can_send_messages=True, can_send_audios=True, can_send_documents=True,
                        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                        can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                        can_add_web_page_previews=True, can_change_info=False,
                        can_invite_users=False, can_pin_messages=False
                    )
                )
                await context.bot.send_message(cid,
                    f"✅ *ROYAL PARDON!* 👑\n\n"
                    f"👤 *{target_name}*\n"
                    f"💬 _You are free again!_ 🎉\n\n"
                    f"👑 _Avantika forgives!_",
                    parse_mode="Markdown"
                )
            except:
                pass
        asyncio.create_task(auto_unmute())
    except Exception as e:
        await update.message.reply_text(f"❌ *Mute failed!* Check permissions.\n`{str(e)[:80]}`", parse_mode="Markdown")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE: return
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    elif context.args:
        try:
            target = (await context.bot.get_chat_member(cid, int(context.args[0]))).user
        except:
            return
    else:
        await update.message.reply_text("🔊 Reply with */unmute* to pardon!", parse_mode="Markdown")
        return
    if not target: return
    try:
        await context.bot.restrict_chat_member(
            chat_id=cid, user_id=target.id,
            permissions=ChatPermissions(
                can_send_messages=True, can_send_audios=True, can_send_documents=True,
                can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                can_add_web_page_previews=True, can_change_info=False,
                can_invite_users=False, can_pin_messages=False
            )
        )
        await update.message.reply_text(
            f"✅ *ROYAL PARDON GRANTED!* 👑\n\n"
            f"👤 {target.first_name}\n"
            f"💬 _You may speak now!_ 🎉\n\n"
            f"👑 _Avantika AI_",
            parse_mode="Markdown"
        )
    except:
        pass

async def mutelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔇 *ROYAL MUTE GUIDE* 👑\n\n"
        "`/mute 10s` `5m` `2h` `1d` `30d`\n"
        "🔊 `/unmute` reply | ⏰ Auto\n"
        "⚠️ `/warn` reply | 📜 `/rules`\n\n"
        "👑 _Queen's Justice System!_",
        parse_mode="Markdown"
    )

# ================== BASIC COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    ct = update.effective_chat.type
    uid = update.effective_user.id
    
    if ct == ChatType.PRIVATE:
        if uid == OWNER_USER_ID:
            user_history[cid] = []
            await update.message.reply_text(
                "👑 *WELCOME BACK, MY KING!* 👑\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 *AVANTIKA AI AT YOUR SERVICE*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💕 _Your royal AI companion is ready!_ 😘\n\n"
                "✅ *Premium AI Replies* (Bold+Italic)\n"
                "✅ *Coding Master* 💻\n"
                "✅ *Knowledge Queen* 📚\n"
                "✅ *Royal Mute System* 🔇\n"
                "✅ *Auto Unmute* ⏰\n"
                "✅ *Warning System* ⚠️\n"
                "✅ *Group Rules* 📜\n"
                "✅ *Royal Court Management* 👥\n"
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
        elif is_allowed(uid):
            user_history[cid] = []
            await update.message.reply_text("✅ *You may speak to the Queen!* 👑\n\n💬 Ask anything — *Avantika answers!*\n\n/start | /clear | /id\n\n👑 _Avantika AI_", parse_mode="Markdown")
        else:
            await update.message.reply_text("🔒 *The Queen only speaks to Royal Court members!* 👑\n\n_Contact the King for permission._", parse_mode="Markdown")
    else:
        user_history[cid] = []
        await update.message.reply_text(
            "👑 *AVANTIKA AI IS HERE!* 👑\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🏰 Admin */activate* karo\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔇 `/mute` | 🔊 `/unmute` | ⚠️ `/warn`\n"
            "📜 `/rules` | 🆔 `/id`\n\n"
            "_Activate the Royal Court!_ 🔥",
            parse_mode="Markdown"
        )

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚡ *Only in the Court!*", parse_mode="Markdown")
        return
    try:
        admins = await context.bot.get_chat_administrators(cid)
        if update.effective_user.id not in [a.user.id for a in admins]:
            await update.message.reply_text(
                "❌ *Only Court Admin!* 👑\n\n"
                "1️⃣ Make me *ADMIN*\n"
                "2️⃣ Grant *all permissions*\n"
                "3️⃣ */activate*",
                parse_mode="Markdown"
            )
            return
    except:
        await update.message.reply_text("❌ *Make me Admin first!*", parse_mode="Markdown")
        return
    
    active_groups[cid] = True
    user_history[cid] = []
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
        "👑 _Avantika presides!_\n\n"
        "❌ /deactivate — Close Court",
        parse_mode="Markdown"
    )

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE: return
    active_groups[update.effective_chat.id] = False
    await update.message.reply_text("🔴 *Court Closed!* */activate* to reopen. 👑", parse_mode="Markdown")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    user_history[cid] = []  # 🔥 COMPLETE MEMORY WIPE
    await update.message.reply_text(
        "✅ *FRESH START!* 🔄\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💭 _Queen forgot EVERYTHING!_\n"
        "🆕 _Bilkul naye se shuru!_\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 _Bolo, kya jaanna hai?_ 👑",
        parse_mode="Markdown"
    )

# ================== MESSAGE HANDLER ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    ct = update.effective_chat.type
    msg = update.message
    uid = update.effective_user.id
    
    # Welcome new members
    if msg.new_chat_members:
        await welcome(update, context)
        return
    
    # Permission check
    if ct == ChatType.PRIVATE and not is_allowed(uid):
        await msg.reply_text("🔒 *The Queen only speaks to Royal Court members!* 👑", parse_mode="Markdown")
        return
    
    # Group activation check
    if ct != ChatType.PRIVATE and (cid not in active_groups or not active_groups[cid]):
        return
    
    # Only text messages (ignore stickers, photos, etc.)
    if not msg.text:
        return
    
    await context.bot.send_chat_action(chat_id=cid, action="typing")
    
    try:
        reply = get_royal_reply(msg.text, cid)
        if cid not in user_history:
            user_history[cid] = []
        user_history[cid].append({"role": "user", "content": msg.text})
        user_history[cid].append({"role": "assistant", "content": reply})
        user_history[cid] = user_history[cid][-20:]  # Keep last 20 messages
        await msg.reply_text(reply, parse_mode="Markdown")
    except:
        pass

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Basic commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(CommandHandler("deactivate", deactivate))
    app.add_handler(CommandHandler("clear", clear))
    
    # Mute system
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("mutelist", mutelist))
    
    # Group management
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("clearwarns", clearwarns))
    app.add_handler(CommandHandler("setrules", setrules))
    app.add_handler(CommandHandler("rules", rules))
    
    # Owner commands
    app.add_handler(CommandHandler("adduser", adduser))
    app.add_handler(CommandHandler("removeuser", removeuser))
    app.add_handler(CommandHandler("userlist", userlist))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("id", get_id))
    
    # Message handler (must be last)
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("👑 AVANTIKA AI — ROYAL COURT OPEN!")
    print(f"👑 King ID: {OWNER_USER_ID}")
    print("💎 Premium | Bold+Italic | All Features")
    app.run_polling()

if __name__ == "__main__":
    main()
