import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 🚀 دریافت توکن‌ها از متغیرهای محیطی
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("TELEGRAM_TOKEN و GEMINI_API_KEY باید در متغیرهای محیطی تنظیم شوند.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

logging.basicConfig(level=logging.INFO)

# 🧠 تاریخچهٔ گفتگو
user_histories = {}

def get_history(chat_id):
    if chat_id not in user_histories:
        user_histories[chat_id] = []
    return user_histories[chat_id]

async def gemini_reply(chat_id, user_text):
    history = get_history(chat_id)
    history.append({"role": "user", "parts": [user_text]})
    try:
        chat = model.start_chat(history=history)
        response = chat.send_message(user_text)
        reply = response.text
        history.append({"role": "model", "parts": [reply]})
        return reply
    except Exception as e:
        logging.error(f"Gemini error: {e}")
        return "متأسفم، مشکلی پیش آمد. لطفاً دوباره تلاش کن."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من ربات هوشمند رایگان با Google Gemini هستم.\n"
        "هر سؤالی داری بپرس، عکس بفرست، یا کمک بخواه."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    if user_text.startswith("/"):
        return
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    reply = await gemini_reply(chat_id, user_text)
    await update.message.reply_text(reply)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    caption = update.message.caption or "این تصویر را توصیف کن و تحلیل کن."
    try:
        image_part = {"mime_type": "image/jpeg", "data": bytes(photo_bytes)}
        response = model.generate_content([caption, image_part])
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Photo analysis error: {e}")
        await update.message.reply_text("نتونستم عکس رو تحلیل کنم، دوباره امتحان کن.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_histories.pop(chat_id, None)
    await update.message.reply_text("تاریخچه گفتگو پاک شد!")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("✅ ربات رایگان با Gemini اجرا شد...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
