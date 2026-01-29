import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- CẤU HÌNH WEB SERVER ĐỂ TREO TRÊN RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CẤU HÌNH BOT TELEGRAM ---
# Lấy API Key từ Environment Variables (Biến môi trường) để bảo mật
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chào bạn! Mình là Bot tích hợp AI.\n- Chat trực tiếp để hỏi đáp.\n- Dùng lệnh /draw [nội dung] để vẽ ảnh.")

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ['group', 'supergroup'] and not f"@{context.bot.username}" in update.message.text:
        return # Chỉ trả lời trong nhóm khi được nhắc tên (tùy chọn)
    
    try:
        response = model.generate_content(update.message.text)
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Lỗi Chat: {e}")

async def draw_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Bạn cần nhập mô tả! Ví dụ: /draw mâm cơm gia đình Việt Nam")
        return

    await update.message.reply_text("⏳ Đang vẽ ảnh, đợi mình xíu...")
    
    # Sử dụng Pollinations AI (Miễn phí, không cần Key)
    image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024&nologo=true&seed=42"
    
    try:
        await update.message.reply_photo(photo=image_url, caption=f"🎨 Ảnh của bạn: {prompt}")
    except Exception as e:
        await update.message.reply_text("Có lỗi khi tạo ảnh rồi!")

def main():
    # Khởi tạo ứng dụng Telegram
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("draw", draw_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    # Chạy Web server song song
    keep_alive()

    # Bắt đầu chạy Bot
    print("Bot đang khởi động...")
    application.run_polling()

if __name__ == '__main__':
    main()
