import os
import requests
import time
from telegram import Bot
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from telegram.error import TelegramError

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN no configurada")
if not REPLICATE_API_KEY:
    raise ValueError("REPLICATE_API_KEY no configurada")

print("✅ Tokens encontrados. Bot iniciando...")
bot = Bot(token=TELEGRAM_TOKEN)

def start(update, context):
    update.message.reply_text(
        "🎨 ¡Hola! Soy Creativo_ImageBot\n\n"
        "Envíame una descripción y generaré imágenes para ti."
    )

def generate_image(prompt):
    try:
        headers = {
            "Authorization": f"Token {REPLICATE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "version": "e1441f0f3b4e50df741b37d4bc1a67a410a3088ba1a249907e23302f9eebad9",
            "input": {
                "prompt": prompt,
                "height": 768,
                "width": 768,
                "num_outputs": 1,
                "num_inference_steps": 20
            }
        }
        
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            json=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 201:
            return None
        
        prediction_id = response.json()["id"]
        max_attempts = 60
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(2)
            check_response = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers=headers,
                timeout=10
            )
            
            prediction = check_response.json()
            
            if prediction["status"] == "succeeded":
                image_url = prediction["output"][0]
                return image_url
            
            elif prediction["status"] == "failed":
                return None
            
            attempt += 1
        
        return None
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def handle_message(update, context):
    try:
        prompt = update.message.text.strip()
        
        if not prompt or len(prompt) < 3:
            update.message.reply_text("❌ El prompt es muy corto.")
            return
        
        wait_msg = update.message.reply_text("🎨 Generando tu imagen, espera...")
        image_url = generate_image(prompt)
        
        if image_url:
            try:
                update.message.reply_photo(photo=image_url)
                try:
                    wait_msg.delete()
                except:
                    pass
                update.message.reply_text("✅ ¡Imagen lista!")
            except TelegramError as e:
                update.message.reply_text("❌ Error al enviar la imagen.")
        else:
            try:
                wait_msg.delete()
            except:
                pass
            update.message.reply_text("❌ No pude generar la imagen. Intenta de nuevo.")
    
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    try:
        updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        print("🚀 Bot iniciado. Esperando mensajes...")
        updater.start_polling(poll_interval=1.0, timeout=10)
        updater.idle()
        
    except Exception as e:
        print(f"❌ Error fatal: {str(e)}")

if __name__ == "__main__":
    main()
