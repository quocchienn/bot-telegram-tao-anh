import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- CẤU HÌNH ---
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run(): app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
# Sử dụng model flash để xử lý cả text và ảnh
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# --- XỬ LÝ CHỨC NĂNG ---

# 1. Hàm vẽ ảnh từ Prompt (Dùng chung cho cả chat và draw)
async def generate_and_send_photo(update, prompt):
    # Tạo URL ảnh từ Pollinations (có thêm seed ngẫu nhiên để ảnh không bị lặp)
    import random
    seed = random.randint(1, 100000)
    image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1024&height=1024&nologo=true&seed={seed}"
    try:
        await update.message.reply_photo(photo=image_url, caption=f"🎨 Ảnh mới dựa trên yêu cầu: {prompt}")
    except Exception as e:
        await update.message.reply_text("Lỗi khi vẽ ảnh!")

# 2. Xử lý khi người dùng gửi ảnh (Vẽ lại)
async def image_reimagine_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return

    # Lấy ảnh có chất lượng cao nhất
    photo_file = await update.message.photo[-1].get_file()
    # Tải ảnh về dưới dạng byte để gửi cho Gemini
    image_data = await photo_file.download_as_bytearray()
    
    user_caption = update.message.caption or "vẽ lại ảnh này theo phong cách nghệ thuật"
    
    await update.message.reply_text("🔍 Đang xem ảnh và lên ý tưởng vẽ lại...")

    try:
        # Gemini phân tích ảnh và tạo prompt vẽ hình
        prompt_request = f"Mô tả chi tiết nội dung ảnh này bằng tiếng Anh để dùng làm prompt cho AI vẽ ảnh (Stable Diffusion). Yêu cầu thêm phong cách: {user_caption}. Chỉ trả về đoạn prompt tiếng Anh, không giải thích thêm."
        
        response = model.generate_content([
            prompt_request,
            {'mime_type': 'image/jpeg', 'data': bytes(image_data)}
        ])
        
        new_prompt = response.text.strip()
        await generate_and_send_photo(update, new_prompt)

    except Exception as e:
        print(f"Lỗi Vision: {e}")
        await update.message.reply_text("Mình không xem được ảnh này, thử lại nhé!")

# 3. Các lệnh cũ giữ nguyên (Start, Draw, Chat)
async def start(update, context):
    await update.message.reply_text("Bot đã sẵn sàng!\n- Gửi ảnh kèm chú thích để mình vẽ lại.\n- /draw [nội dung] để vẽ mới.\n- Chat bình thường để hỏi đáp.")

async def draw_handler(update, context):
    prompt = " ".join(context.args)
    if prompt: await generate_and_send_photo(update, prompt)
    else: await update.message.reply_text("Nhập mô tả sau lệnh /draw")

async def chat_handler(update, context):
    try:
        response = model.generate_content(update.message.text)
        await update.message.reply_text(response.text)
    except: await update.message.reply_text("Hệ thống bận!")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("draw", draw_handler))
    # Xử lý tin nhắn có chứa ảnh
    application.add_handler(MessageHandler(filters.PHOTO, image_reimagine_handler))
    # Xử lý tin nhắn văn bản
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    keep_alive()
    application.run_polling()

if __name__ == '__main__':
    main()
