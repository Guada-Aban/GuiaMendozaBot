import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import requests

from ia_client import responder_con_ia, consultar_clima, consultar_pronostico

# Cargo el token
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# --- FUNCIONES DE COMANDOS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Creamos los botones que aparecerán DENTRO del mensaje
    keyboard = [
        [
            InlineKeyboardButton("🏔 Lugares", callback_data="lugares"),
            InlineKeyboardButton("🍷 Comidas", callback_data="comidas")
        ],
        [
            InlineKeyboardButton("☀️ Clima", callback_data="clima"),
            InlineKeyboardButton("📅 Pronóstico", callback_data="pronostico")
        ],
        [
            InlineKeyboardButton("ℹ️ Ayuda", callback_data="ayuda")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = (
        "👋 ¡Hola! Soy *Pandito*, tu guía virtual de Mendoza. 🐼\n\n"
        "Elegí una opción para comenzar:"
    )

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)
    
async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Podés preguntarme cosas como:\n"
        "- Qué lugares visitar en Mendoza\n"
        "- Qué comer típico\n"
        "- Cómo está el clima hoy\n"
        "- Qué puedo hacer en Mendoza un fin de semana"
    )
    await mostrar_menu_rapido(update)



async def lugares(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏞️ Algunos lugares imperdibles en Mendoza:\n"
        "- Parque General San Martín\n"
        "- Cerro de la Gloria\n"
        "- Bodegas en Maipú y Luján de Cuyo\n"
        "- Alta Montaña y Puente del Inca\n"
        "- Embalse Potrerillos"
    )
    
    await mostrar_menu_rapido(update)



async def comidas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍷 Comidas típicas mendocinas:\n"
        "- Asado con vino local 🍖\n"
        "- Empanadas mendocinas 🥟\n"
        "- Locro y humita\n"
        "- Dulce de membrillo y tortitas"
    )
    
    await mostrar_menu_rapido(update)



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
    
    await mostrar_menu_rapido(update)



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

#funcion para responder texto 
async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text.lower().strip()

    # Palabras clave para volver al menú principal
    palabras_menu = ["menu", "menú", "inicio", "volver", "empezar", "principal"]

    # Palabras clave para clima actual
    palabras_clima = [
        "tiempo", "frio", "calor", "lluvia", "nieve",
        "clima", "soleado", "nuboso", "temperatura", "hoy"
    ]
    
    # Palabras clave para pronóstico (a futuro)
    palabras_pronostico = [
        "pronóstico", "previsión", "mañana", "tarde", "noche",
        "tormenta", "semana", "fin de semana", "va a llover", "lloverá"
    ]

    # --- Si el usuario pide volver al menú ---
    if any(palabra in pregunta for palabra in palabras_menu):
        keyboard = [
            [
                InlineKeyboardButton("🏔 Lugares", callback_data="lugares"),
                InlineKeyboardButton("🍷 Comidas", callback_data="comidas")
            ],
            [
                InlineKeyboardButton("☀️ Clima", callback_data="clima"),
                InlineKeyboardButton("📅 Pronóstico", callback_data="pronostico")
            ],
            [
                InlineKeyboardButton("ℹ️ Ayuda", callback_data="ayuda")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        msg = (
            "🏠 Volviste al *menú principal*.\n\n"
            "Elegí una opción para continuar:"
        )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)
        return  # corta la función acá

    # --- Si pregunta por el pronóstico ---
    if any(palabra in pregunta for palabra in palabras_pronostico):
        respuesta = consultar_pronostico()

    # --- Si pregunta por el clima actual ---
    elif any(palabra in pregunta for palabra in palabras_clima):
        respuesta = consultar_clima()

    # --- Si no coincide con nada, responde la IA ---
    else:
        respuesta = responder_con_ia(pregunta)

    await update.message.reply_text(respuesta)
    
    await mostrar_menu_rapido(update)

    
    
# --- FUNCIÓN PARA MANEJAR LOS BOTONES INLINE ---
async def manejar_botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Confirma que se tocó el botón

    data = query.data

    if data == "lugares":
        await query.message.reply_text(
            "🏞️ Algunos lugares imperdibles en Mendoza:\n"
            "- Parque General San Martín\n"
            "- Cerro de la Gloria\n"
            "- Bodegas en Maipú y Luján de Cuyo\n"
            "- Alta Montaña y Puente del Inca\n"
            "- Embalse Potrerillos"
        )

    elif data == "comidas":
        await query.message.reply_text(
            "🍷 Comidas típicas mendocinas:\n"
            "- Asado con vino local 🍖\n"
            "- Empanadas mendocinas 🥟\n"
            "- Locro y humita\n"
            "- Dulce de membrillo y tortitas"
        )

    elif data == "clima":
        respuesta = consultar_clima()
        await query.message.reply_text(respuesta)

    elif data == "pronostico":
        respuesta = consultar_pronostico()
        await query.message.reply_text(respuesta)

    elif data == "ayuda":
        await query.message.reply_text(
            "Podés pedirme cosas como:\n"
            "- Qué lugares visitar en Mendoza\n"
            "- Qué comer típico\n"
            "- Cómo está el clima hoy\n"
            "- Qué bodegas visitar 🍇"
        )

    # 👇 NUEVO BLOQUE: cuando se toca el botón “Volver al menú”
    elif data == "menu_principal":
        keyboard = [
            [
                InlineKeyboardButton("🏔 Lugares", callback_data="lugares"),
                InlineKeyboardButton("🍷 Comidas", callback_data="comidas")
            ],
            [
                InlineKeyboardButton("☀️ Clima", callback_data="clima"),
                InlineKeyboardButton("📅 Pronóstico", callback_data="pronostico")
            ],
            [
                InlineKeyboardButton("ℹ️ Ayuda", callback_data="ayuda")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "🏠 Estás de nuevo en el *menú principal*. Elegí una opción:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    else:
        await query.message.reply_text("Opción no reconocida, probá otra 🙂")


async def mostrar_menu_rapido(update: Update):
    keyboard = [
        [InlineKeyboardButton("🏠 Volver al menú", callback_data="menu_principal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("¿Te puedo ayudar con algo más? 🤔", reply_markup=reply_markup)



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
    app.add_handler(CallbackQueryHandler(manejar_botones))
    app.add_handler(CallbackQueryHandler(manejar_botones))



    # Mensajes sin comando → IA
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))

    print("🌍 Guía Mendoza (Pandito) corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()
