import os
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # ví dụ https://ten-app.onrender.com/webhook

HF_MODEL_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

bot = Bot(BOT_TOKEN)
app = Flask(__name__)

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

def generate_image(prompt: str):
    payload = {"inputs": prompt}
    r = requests.post(HF_MODEL_URL, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.content


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot AI tạo ảnh online.\nDùng /ve <mô tả>"
    )


async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Thiếu mô tả ảnh.")
        return

    prompt = " ".join(context.args)
    msg = await update.message.reply_text("Đang vẽ...")

    try:
        image = generate_image(prompt)
        await update.message.reply_photo(photo=image)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"Lỗi: {e}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text.startswith("vẽ "):
        prompt = text[3:]
        msg = await update.message.reply_text("Đang vẽ cho nhóm...")
        try:
            image = generate_image(prompt)
            await update.message.reply_photo(photo=image)
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"Lỗi: {e}")


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("ve", draw))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


@app.route("/webhook", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    await telegram_app.process_update(update)
    return "ok"


@app.route("/")
def home():
    return "Bot is running."


def set_webhook():
    bot.set_webhook(WEBHOOK_URL)


if __name__ == "__main__":
    set_webhook()
    telegram_app.initialize()
    telegram_app.start()
