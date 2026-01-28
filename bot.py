import os
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ===== ENV =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
BASE_URL = os.getenv("BASE_URL")  # https://your-app.onrender.com

# ===== HF MODEL (đổi nếu muốn) =====
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# ===== TẠO APP TELEGRAM =====
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
bot = Bot(BOT_TOKEN)

# ===== HÀM GỌI HUGGING FACE =====
def generate_image(prompt: str):
    response = requests.post(
        HF_API_URL,
        headers=headers,
        json={"inputs": prompt},
        timeout=120
    )

    if response.status_code != 200:
        return None, response.text

    return response.content, None


# ===== LỆNH /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Gửi:\n/ve mô tả ảnh\nVí dụ:\n/ve chiến binh samurai máy móc giữa thành phố neon"
    )


# ===== LỆNH TẠO ẢNH =====
async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Thiếu mô tả ảnh.")
        return

    prompt = " ".join(context.args)
    msg = await update.message.reply_text("Đang tạo ảnh...")

    img, err = generate_image(prompt)

    if err:
        await msg.edit_text("Lỗi AI: " + err[:200])
        return

    await update.message.reply_photo(photo=img)
    await msg.delete()


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("ve", draw))


# ===== FLASK WEBHOOK SERVER =====
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    await telegram_app.process_update(update)
    return "ok"


@app.route("/")
def home():
    return "Bot is running"


# ===== SET WEBHOOK KHI SERVER START =====
async def set_webhook():
    await bot.set_webhook(f"{BASE_URL}/webhook")


if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().run_until_complete(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
