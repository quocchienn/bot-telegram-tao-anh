import telebot
from huggingface_hub import InferenceClient
from io import BytesIO
from PIL import Image
from flask import Flask, request, abort
import os

# Token từ env vars
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
HF_TOKEN = os.getenv('HF_TOKEN')

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)  # Thêm threaded=False để tương thích Render free
client = InferenceClient(api_key=HF_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Chào! Sử dụng /img <prompt> để tạo ảnh. Ví dụ: /img Astronaut riding a horse.")

@bot.message_handler(commands=['img'])
def generate_image(message):
    # Lấy prompt từ sau lệnh (bỏ command)
    prompt = ' '.join(message.text.split()[1:])
    if not prompt:
        bot.reply_to(message, "Vui lòng cung cấp prompt sau /img. Ví dụ: /img A beautiful sunset.")
        return
    
    bot.reply_to(message, "Đang tạo ảnh... Hãy chờ một chút.")
    
    try:
        image = client.text_to_image(
            prompt,
            model="zai-org/GLM-Image",
            provider="fal-ai",
            parameters={
                "num_inference_steps": 50,
                "guidance_scale": 7.5,
                "width": 512,
                "height": 512
            }
        )
        
        bio = BytesIO()
        image.save(bio, 'PNG')
        bio.seek(0)
        
        bot.send_photo(message.chat.id, bio)
    except Exception as e:
        bot.reply_to(message, f"Lỗi: {str(e)}. Hãy thử prompt khác hoặc kiểm tra token.")

# Webhook endpoint
app = Flask(__name__)

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)

@app.route('/')
def index():
    return "Bot is running!"

if __name__ == '__main__':
    bot.remove_webhook()
    app.run(host='0.0.0.0', port=8000)
