import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

HF_MODEL_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

headers = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

def generate_image(prompt: str):
    payload = {"inputs": prompt}
    response = requests.post(HF_MODEL_URL, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    return response.content  # ảnh dạng bytes

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot AI tạo ảnh đã online.\n"
        "Dùng: /ve <mô tả ảnh>\n"
        "Ví dụ: /ve con mèo phi hành gia phong cách cyberpunk"
    )

# /ve command
async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gõ mô tả sau lệnh. Ví dụ: /ve rồng lửa bay trên thành phố tương lai")
        return

    prompt = " ".join(context.args)
    msg = await update.message.reply_text("Đang vẽ... AI đang suy nghĩ 🧠🎨")

    try:
        image_bytes = generate_image(prompt)
        await update.message.reply_photo(photo=image_bytes)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"Lỗi khi tạo ảnh:\n{e}")

# Cho phép dùng trong group khi bot được add
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.lower().startswith("vẽ "):
        prompt = text[3:]
        msg = await update.message.reply_text("Đang vẽ ảnh cho nhóm...")
        try:
            image_bytes = generate_image(prompt)
            await update.message.reply_photo(photo=image_bytes)
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"Lỗi: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ve", draw))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()
