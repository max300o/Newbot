import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# تنظیم لاگ‌گیری
logging.basicConfig(level=logging.INFO)

# خواندن متغیرهای محیطی (از GitHub Secrets)
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TOKEN or not GEMINI_API_KEY:
    raise ValueError("متغیرهای محیطی به درستی تنظیم نشده‌اند!")

# پیکربندی Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # یا مدل دلخواه

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من یک ربات هوشمند هستم. هر سوالی داری، بپرس."
    )

# پاسخ به پیام‌های متنی
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        response = model.generate_content(user_message)
        reply = response.text if response.text else "پاسخی دریافت نشد."
    except Exception as e:
        logging.error(f"خطا در Gemini: {e}")
        reply = "متأسفم، خطایی رخ داد. دوباره تلاش کن."

    await update.message.reply_text(reply[:4096])  # محدودیت طول پیام تلگرام

# اجرای ربات
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
