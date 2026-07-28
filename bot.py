import os
import logging
import random
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# ---------------------------------------------------------------------------
# CONFIG — values are read from environment variables, never hardcoded here.
# Set these in Choreo's "Configs & Secrets" panel (or a local .env file).
# ---------------------------------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# In-memory store of verified users. Resets if the bot restarts.
# For production you'd swap this for a small database, but this is fine for testing.
verified_users: set[int] = set()

SYSTEM_PROMPT = (
    "You are a warm, friendly, casual Telegram chat companion. "
    "Use a light, upbeat tone and emoji naturally (not excessively). "
    "Keep replies fairly short and conversational, like texting a friend. "
    "Be genuinely helpful when asked real questions. "
    "Never use slurs, hate speech, or discriminatory language of any kind."
)

# ---------------------------------------------------------------------------
# HUMAN VERIFICATION
# ---------------------------------------------------------------------------
def build_verification_keyboard() -> InlineKeyboardMarkup:
    a, b = random.randint(1, 9), random.randint(1, 9)
    correct = a + b
    options = {correct}
    while len(options) < 3:
        options.add(correct + random.choice([-3, -2, -1, 1, 2, 3]))
    options = list(options)
    random.shuffle(options)

    buttons = [
        InlineKeyboardButton(str(opt), callback_data=f"verify:{opt}:{correct}")
        for opt in options
    ]
    return a, b, InlineKeyboardMarkup([buttons])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in verified_users:
        await update.message.reply_text(
            "Hey, welcome back! 👋 You're already verified — just start chatting with me anytime 💬"
        )
        return

    a, b, keyboard = build_verification_keyboard()
    context.user_data["captcha_a"] = a
    context.user_data["captcha_b"] = b
    await update.message.reply_text(
        f"👋 Hey there! Welcome!\n\n"
        f"Before we chat, quick check that you're human 🙂\n"
        f"What's **{a} + {b}**?",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, chosen, correct = query.data.split(":")
    user_id = update.effective_user.id

    if chosen == correct:
        verified_users.add(user_id)
        await query.edit_message_text(
            "✅ Verified! You're officially human (or a very smart bot 👀).\n\n"
            "Say hi, ask me anything, or just chat — I'm here 24/7! 😄"
        )
    else:
        a, b, keyboard = build_verification_keyboard()
        context.user_data["captcha_a"] = a
        context.user_data["captcha_b"] = b
        await query.edit_message_text(
            f"❌ Not quite! Let's try again.\nWhat's **{a} + {b}**?",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


# ---------------------------------------------------------------------------
# AI CHAT (OpenRouter)
# ---------------------------------------------------------------------------
async def ask_ai(user_message: str) -> str:
    if not OPENROUTER_API_KEY:
        return "⚠️ AI chat isn't configured yet — the bot owner needs to set OPENROUTER_API_KEY."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 400,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"AI request failed: {e}")
        return "Oops, my brain glitched for a second 😅 try asking that again?"


# ---------------------------------------------------------------------------
# MESSAGE HANDLER
# ---------------------------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text or ""

    if user_id not in verified_users:
        await update.message.reply_text(
            "Hold up — you haven't passed human verification yet! 🙂 Type /start to do that first."
        )
        return

    greetings = {"hi", "hello", "hey", "hola", "yo", "hii", "helo"}
    if text.strip().lower() in greetings:
        await update.message.reply_text("Heyyy! 👋😄 What's up?")
        return

    await update.message.chat.send_action("typing")
    reply = await ask_ai(text)
    await update.message.reply_text(reply)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern=r"^verify:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
