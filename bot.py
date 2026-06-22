import os
from dotenv import load_dotenv

from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo.telegram_ai
history_col = db.history

# OpenAI
client = AsyncOpenAI(
    api_key=OPENAI_API_KEY
)

SYSTEM_PROMPT = """
You are a premium AI assistant.
Answer accurately and professionally.
Use markdown when useful.
"""

async def save_chat(user_id, role, content):
    await history_col.insert_one({
        "user_id": user_id,
        "role": role,
        "content": content
    })

async def get_history(user_id, limit=10):
    messages = []

    cursor = (
        history_col
        .find({"user_id": user_id})
        .sort("_id", -1)
        .limit(limit)
    )

    async for doc in cursor:
        messages.append({
            "role": doc["role"],
            "content": doc["content"]
        })

    messages.reverse()
    return messages

async def ask_ai(messages):
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
        max_tokens=1500
    )

    return response.choices[0].message.content

async def start(update: Update,
                context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Premium AI Bot Online\n\nSend any message."
    )

async def reset(update: Update,
                context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    await history_col.delete_many({
        "user_id": user_id
    })

    await update.message.reply_text(
        "✅ Memory cleared."
    )

async def chat(update: Update,
               context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user_id = update.effective_user.id
    user_text = update.message.text

    history = await get_history(user_id)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(history)

    messages.append({
        "role": "user",
        "content": user_text
    })

    try:

        reply = await ask_ai(messages)

        await save_chat(
            user_id,
            "user",
            user_text
        )

        await save_chat(
            user_id,
            "assistant",
            reply
        )

        await update.message.reply_text(
            reply
        )

    except Exception as e:

        await update.message.reply_text(
            f"Error:\n{str(e)}"
        )

def main():

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "reset",
            reset
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT &
            ~filters.COMMAND,
            chat
        )
    )

    print("Bot Started")

    app.run_polling()

if __name__ == "__main__":
    main()
