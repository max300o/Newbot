import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TOKEN or not GEMINI_API_KEY:
    raise ValueError("متغیرهای محیطی به درستی تنظیم نشده‌اند!")

genai.configure(api_key=GEMINI_API_KEY)

# لیست مدل‌های جدید به ترتیب اولویت
MODELS = [
    "gemini-2.0-flash-exp",
    "gemini-2.5-pro-exp-03-25",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]

model = None
for model_name in MODELS:
    try:
        test_model = genai.GenerativeModel(model_name)
        # تست با یک درخواست ساده
        test_model.generate_content("test")
        model = test_model
        logger.info(f"✅ مدل {model_name} با موفقیت فعال شد")
        break
    except Exception as e:
        logger.warning(f"⚠️ مدل {model_name} در دسترس نیست: {e}")

if model is None:
    raise RuntimeError("هیچ مدلی از Gemini در دسترس نیست! کلید API را بررسی کن.")

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
