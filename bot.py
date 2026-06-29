import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# تنظیم لاگ‌گیری دقیق
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TOKEN or not GEMINI_API_KEY:
    raise ValueError("متغیرهای محیطی به درستی تنظیم نشده‌اند!")

# پیکربندی Gemini
genai.configure(api_key=GEMINI_API_KEY)

# تلاش برای مدل‌های مختلف (اول فلش، بعد پرو)
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    # یک درخواست تستی برای اعتبارسنجی کلید
    model.generate_content("test")
    logger.info("✅ مدل gemini-1.5-flash فعال شد")
except Exception as e:
    logger.warning(f"⚠️ مدل فلش کار نکرد، رفتیم سراغ gemini-pro: {e}")
    model = genai.GenerativeModel("gemini-pro")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من یک ربات هوشمند هستم. هر سوالی داری، بپرس.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        response = model.generate_content(user_message)
        reply = response.text if response.text else "پاسخی دریافت نشد."
        logger.info(f"پاسخ به: {user_message[:30]}")
    except Exception as e:
        logger.error(f"❌ خطای Gemini: {e}", exc_info=True)
        # ارسال متن دقیق خطا به تلگرام برای فهمیدن مشکل
        await update.message.reply_text(f"❌ خطا: {str(e)}")
        return

    await update.message.reply_text(reply[:4096])

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🚀 ربات راه‌اندازی شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
