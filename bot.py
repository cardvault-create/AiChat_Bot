import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

user_history = {}

def get_reply(text, cid):
    if cid not in user_history: user_history[cid] = []
    prompt = "You are GARAM GAND AI, a friendly assistant. Reply in user's language. Be helpful.\n\n"
    for m in user_history[cid][-3:]:
        prompt += f"{m['role']}: {m['content']}\n"
    prompt += f"user: {text}\nassistant:"
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        return f"Error: {str(e)[:50]}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    user_history[cid] = []
    await update.message.reply_text("💎 Ready! Kuch bhi puchho!")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.text: return
    reply = get_reply(msg.text, update.effective_chat.id)
    await msg.reply_text(reply)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))
    print("✅ Bot Ready!")
    app.run_polling()

if __name__ == "__main__": main()
