import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

HF_MODEL_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}


def generate_image(prompt):
    r = requests.post(HF_MODEL_URL, headers=headers, json={"inputs": prompt}, timeout=120)
    r.raise_for_status()
    return r.content


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot tạo ảnh online. Dùng /ve <mô tả>")


async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Thiếu mô tả.")
        return

    msg = await update.message.reply_text("Đang vẽ...")
    try:
        img = generate_image(prompt)
        await update.message.reply_photo(photo=img)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(str(e))


app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ve", draw))


if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )
