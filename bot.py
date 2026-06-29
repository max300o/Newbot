import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# دریافت توکن‌ها از متغیرهای محیطی
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("TELEGRAM_TOKEN و GEMINI_API_KEY باید تنظیم شوند.")

# آدرس پایهٔ REST API جمینای
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
HEADERS = {"Content-Type": "application/json"}

logging.basicConfig(level=logging.INFO)

# تاریخچهٔ گفتگو (اختیاری، به سادگی پیاده شده)
user_histories = {}

def get_history(chat_id):
    if chat_id not in user_histories:
        user_histories[chat_id] = []
    return user_histories[chat_id]

def ask_gemini(user_text, chat_id):
    """ارسال درخواست به REST API و دریافت پاسخ"""
    history = get_history(chat_id)
    # اضافه کردن پیام کاربر به تاریخچه
    history.append({"role": "user", "parts": [{"text": user_text}]})

    # ساخت بدنهٔ درخواست
    payload = {
        "contents": history,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2000
        }
    }

    try:
        resp = requests.post(
            f"{API_BASE}?key={GEMINI_API_KEY}",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        resp.raise_for_status()  # برای کدهای خطا exception صادر می‌کند

        data = resp.json()
        # استخراج پاسخ از ساختار JSON
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
        # ذخیرهٔ پاسخ در تاریخچه
        history.append({"role": "model", "parts": [{"text": answer}]})
        return answer

    except requests.exceptions.RequestException as e:
        logging.error(f"Network/HTTP error: {e}")
        # اگر پاسخ خطا از طرف سرور باشد، جزئیات را برگردانیم
        if e.response is not None:
            try:
                err = e.response.json()
                return f"❌ خطای API: {err.get('error', {}).get('message', 'مشخص نشد')}"
            except:
                return f"❌ خطا: {e.response.status_code} - {e.response.text[:200]}"
        return f"❌ خطای شبکه: {str(e)[:200]}"
    except (KeyError, IndexError) as e:
        logging.error(f"Unexpected JSON structure: {e}")
        return "❌ ساختار پاسخ غیرمنتظره. لطفاً بعداً تلاش کن."
    except Exception as e:
        logging.error(f"Unknown error: {e}")
        return f"❌ خطای ناشناخته: {str(e)[:200]}"

# ----- توابع ربات -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من ربات هوشمند رایگان با Gemini هستم.\nهر چی دوست داری بپرس، عکس بفرست یا کمک بگیر.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    if user_text.startswith("/"):
        return
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    reply = ask_gemini(user_text, chat_id)
    await update.message.reply_text(reply)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # دانلود عکس
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    caption = update.message.caption or "این تصویر را توصیف کن و تحلیل کن."

    # برای تحلیل عکس باید از API مخصوص vision استفاده کنیم
    # اما مدل gemini-1.5-flash چندوجهی است و REST API مشابهی دارد.
    # فرض می‌کنیم از همان مسیر generateContent با تصویر base64 شده پشتیبانی می‌کند
    import base64
    image_b64 = base64.b64encode(bytes(photo_bytes)).decode("utf-8")

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": caption},
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": image_b64
                        }
                    }
                ]
            }
        ]
    }

    try:
        resp = requests.post(
            f"{API_BASE}?key={GEMINI_API_KEY}",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
        await update.message.reply_text(answer)
    except Exception as e:
        logging.error(f"Photo analysis error: {e}")
        await update.message.reply_text(f"❌ نتونستم عکس رو تحلیل کنم. خطا: {str(e)[:200]}")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_histories.pop(chat_id, None)
    await update.message.reply_text("✅ تاریخچه گفتگو پاک شد.")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("✅ ربات با REST API اجرا شد...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
