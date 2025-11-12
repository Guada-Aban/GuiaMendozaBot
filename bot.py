import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import requests

from ia_client import responder_con_ia

# Cargo el token
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- FUNCIONES DE COMANDOS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 ¡Hola! Soy *Pandito*, tu asistente de viajes inteligente 🇦🇷\n\n"
        "Puedo recomendarte lugares, comidas típicas o decirte el clima actual.\n"
        "Usá alguno de estos comandos:\n"
        "🏔 /lugares - lugares turísticos\n"
        "🍷 /comidas - comidas y restaurantes\n"
        "☀️ /clima - clima actual\n"
        "🤖 /preguntar - hacer una consulta con IA\n"
        "ℹ️ /ayuda - más información"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Podés preguntarme cosas como:\n"
        "- Qué lugares visitar en Mendoza\n"
        "- Qué comer típico\n"
        "- Cómo está el clima hoy\n"
        "- Qué puedo hacer en Mendoza un fin de semana"
    )


async def lugares(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏞️ Algunos lugares imperdibles en Mendoza:\n"
        "- Parque General San Martín\n"
        "- Cerro de la Gloria\n"
        "- Bodegas en Maipú y Luján de Cuyo\n"
        "- Alta Montaña y Puente del Inca\n"
        "- Embalse Potrerillos"
    )


async def comidas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍷 Comidas típicas mendocinas:\n"
        "- Asado con vino local 🍖\n"
        "- Empanadas mendocinas 🥟\n"
        "- Locro y humita\n"
        "- Dulce de membrillo y tortitas"
    )


async def clima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = os.getenv("WEATHER_API_KEY")
    ciudad = "Mendoza,AR"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={api_key}&units=metric&lang=es"

    try:
        response = requests.get(url)
        data = response.json()

        if data["cod"] == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"].capitalize()

            mensaje = (
                f"🌤️ Clima actual en Mendoza:\n"
                f"Temperatura: {temp}°C\n"
                f"Descripción: {desc}\n"
            )
        else:
            mensaje = "No pude obtener el clima en este momento 😕"

    except Exception as e:
        mensaje = f"Error al consultar el clima: {e}"

    await update.message.reply_text(mensaje)


async def preguntar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        pregunta = " ".join(context.args)
        respuesta = responder_con_ia(pregunta)
        await update.message.reply_text(respuesta)
    else:
        await update.message.reply_text(
            "Por favor escribí una pregunta. Ejemplo:\n"
            "`/preguntar Qué puedo visitar en Mendoza en 3 días`",
            parse_mode="Markdown"
        )


# --- FUNCIÓN PARA RESPONDER MENSAJES DE TEXTO ---
async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text
    respuesta = responder_con_ia(pregunta)
    await update.message.reply_text(respuesta)


# --- CONFIGURACIÓN DEL BOT ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("lugares", lugares))
    app.add_handler(CommandHandler("comidas", comidas))
    app.add_handler(CommandHandler("clima", clima))
    app.add_handler(CommandHandler("preguntar", preguntar))

    # Mensajes sin comando → IA
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))

    print("🌍 Guía Mendoza (Pandito) corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()
