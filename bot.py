# bot.py
import os
import json
import difflib
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)
import requests
from telegram.error import BadRequest

# funciones IA y clima/progn vienen de archivos auxiliares
from ia_client import responder_con_ia, enriquecer_con_ia # noqa: F401

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_KEY = os.getenv("WEATHER_API_KEY")

# Cargar JSON de lugares
DATA_FILE = "lugares.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        LUGARES_DATA = json.load(f)
else:
    LUGARES_DATA = {}

# --- UTIL: buscar lugar en JSON (coincidencia parcial y fuzzy) ---
def buscar_lugar_en_json(texto: str):
    texto = texto.lower().strip()
    # búsqueda directa por clave
    for clave, info in LUGARES_DATA.items():
        if clave in texto or info.get("nombre", "").lower() in texto:
            return clave, info
    # fuzzy: buscar coincidencias cercanas en keys y nombres
    claves = list(LUGARES_DATA.keys())
    matches = difflib.get_close_matches(texto, claves, n=1, cutoff=0.6)
    if matches:
        return matches[0], LUGARES_DATA[matches[0]]
    # buscar por palabras contiguas (ej: "parque san martin")
    for clave in claves:
        if all(pal in texto for pal in clave.split()):
            return clave, LUGARES_DATA[clave]
    return None, None

# --- FUNCIONES DE CLIMA/PRONÓSTICO (si las querías inline en bot.py) ---
def consultar_clima():
    if not WEATHER_KEY:
        return "Servicio de clima no configurado."
    ciudad = "Mendoza,AR"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={WEATHER_KEY}&units=metric&lang=es"
    try:
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("cod") == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"].capitalize()
            humedad = data["main"].get("humidity")
            viento = data["wind"].get("speed")
            return f"🌤️ Clima actual en Mendoza:\nTemperatura: {temp}°C\nDescripción: {desc}\nHumedad: {humedad}%\nViento: {viento} m/s"
        else:
            return "No pude obtener el clima actual 😕"
    except Exception as e:
        return f"Error al consultar el clima: {e}"

def consultar_pronostico():
    if not WEATHER_KEY:
        return "Servicio de pronóstico no configurado."
    lat, lon = -32.889, -68.845
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric&lang=es"
    try:
        r = requests.get(url, timeout=8)
        data = r.json()
        lst = data.get("list", [])[:8]
        if not lst:
            return "No pude obtener el pronóstico."
        temps = [it["main"]["temp"] for it in lst]
        min_t, max_t = min(temps), max(temps)
        pop = max([it.get("pop", 0) for it in lst]) * 100
        desc = lst[0]["weather"][0]["description"].capitalize()
        return (
            f"📅 Pronóstico para hoy en Mendoza:\n"
            f"🌡️ Mínima: {min_t:.1f}°C | Máxima: {max_t:.1f}°C\n"
            f"🌧️ Probabilidad de lluvia: {pop:.0f}%\n"
            f"☀️ Cielo: {desc}"
        )
    except Exception as e:
        return f"Error al consultar el pronóstico: {e}"

# --- MENÚ y helpers ---
def build_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("🏔 Lugares", callback_data="lugares")
        ],
        [
            InlineKeyboardButton("☀️ Clima", callback_data="clima"),
            InlineKeyboardButton("📅 Pronóstico", callback_data="pronostico")
        ],
        [
            InlineKeyboardButton("ℹ️ Ayuda", callback_data="ayuda")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def enviar_menu_principal(message):
    await message.reply_text(
        "👋 ¡Hola! Soy *Pandito*, tu guía virtual de Mendoza. Elegí una opción:",
        parse_mode="Markdown",
        reply_markup=build_main_menu()
    )

async def mostrar_menu_rapido(update_or_query):
    # update_or_query puede ser Update (con message) o CallbackQuery
    if hasattr(update_or_query, "message"):
        target = update_or_query.message
    else:
        target = update_or_query
    keyboard = [[InlineKeyboardButton("🏠 Volver al menú", callback_data="menu_principal")]]
    await target.reply_text("¿Te puedo ayudar con algo más? 🤔", reply_markup=InlineKeyboardMarkup(keyboard))

async def mostrar_menu_rapido_from_query(query):
    keyboard = [[InlineKeyboardButton("🏠 Volver al menú", callback_data="menu_principal")]]
    await query.message.reply_text("¿Querés ver otra categoría? 😊", reply_markup=InlineKeyboardMarkup(keyboard))


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Podés pedirme recomendaciones, preguntar por clima o pedir itinerarios. Probá tocar los botones del menú."
    )
    await mostrar_menu_rapido(update.message)

async def lugares_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # comando /lugares -> abre submenú
    await manejar_botones_fake("lugares", update.message)

# función auxiliar para simular callback desde comandos
async def manejar_botones_fake(data, message):
    # Reutilizamos la misma lógica que el callback handler pero con message en lugar de query
    if data == "lugares":
        keyboard = [
            [InlineKeyboardButton("🌿 Naturaleza", callback_data="lug_naturaleza")],
            [InlineKeyboardButton("🍇 Bodegas", callback_data="lug_bodegas")],
            [InlineKeyboardButton("🛍 Compras", callback_data="lug_compras")],
            [InlineKeyboardButton("🏛 Cultura", callback_data="lug_cultura")],
            [InlineKeyboardButton("⛰ Alta montaña", callback_data="lug_montana")],
            [InlineKeyboardButton("🎢 Aventura", callback_data="lug_aventura")]
        ]
        await message.reply_text("Elegí una categoría de lugares:", reply_markup=InlineKeyboardMarkup(keyboard))

async def preguntar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        pregunta = " ".join(context.args)
        respuesta = responder_con_ia(pregunta)
        await update.message.reply_text(respuesta)
        await mostrar_menu_rapido(update.message)
    else:
        await update.message.reply_text("Usá: /preguntar <tu pregunta>", parse_mode="Markdown")

# responde texto libre (incluye saludo, menus, búsqueda de lugar)
async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text.lower().strip()

    # saludos
    saludos = ["hola", "buenas", "buen día", "buen dia", "buenas tardes", "buenas noches", "qué tal", "hey", "hi", "holis"]

    if any(s in pregunta for s in saludos):
        await enviar_menu_principal(update.message)
        return

    # detectar si el usuario escribió un lugar que está en JSON
    clave, info = buscar_lugar_en_json(pregunta)
    if info:
        # Formatear respuesta con info del JSON
        texto = f"📍 *{info.get('nombre', clave.title())}*\n{info.get('descripcion','')}\n\n"
        if info.get("como_llegar"):
            texto += f"🚗 *Cómo llegar:* [Abrir en Google Maps]({info['como_llegar']})\n"

        if info.get("horarios"):
            texto += f"🕘 *Horarios:* {info.get('horarios')}\n"
        if info.get("actividades"):
            actividades = ', '.join(info.get("actividades"))
            texto += f"🎯 *Actividades:* {actividades}\n"
        await update.message.reply_text(texto, parse_mode="Markdown")
        await mostrar_menu_rapido(update.message)
        return

    # palabras clave para clima/pronóstico/menu
    palabras_menu = ["menu", "menú", "inicio", "volver", "empezar", "principal"]
    palabras_clima = ["tiempo", "frio", "calor", "lluvia", "nieve", "clima", "temperatura", "hoy"]
    palabras_pronostico = ["pronóstico", "previsión", "mañana", "tarde", "noche", "va a llover", "lloverá", "tormenta"]

    if any(p in pregunta for p in palabras_pronostico):
        await update.message.reply_text(consultar_pronostico())
        await mostrar_menu_rapido(update.message)
        return
    if any(p in pregunta for p in palabras_clima):
        await update.message.reply_text(consultar_clima())
        await mostrar_menu_rapido(update.message)
        return
    if any(p in pregunta for p in palabras_menu):
        await enviar_menu_principal(update.message)
        return

    # Si no encontramos en JSON, pedimos a la IA que describa y aclaramos origen
    descripcion = enriquecer_con_ia(pregunta)
    respuesta = f"{descripcion}\n\nNota: esta descripción es orientativa. Para datos exactos consultá fuentes oficiales."
    await update.message.reply_text(respuesta)
    await mostrar_menu_rapido(update.message)

# --- FUNCIÓN PARA MANEJAR LOS BOTONES INLINE ---
async def manejar_botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        # botón expirado o inválido -> reenviamos menú principal
        await query.message.reply_text("⏳ Ese botón expiró. Te muestro el menú de nuevo:")
        await enviar_menu_principal(query.message)
        return

    data = query.data

    # CATEGORÍAS
    if data == "lugares":
        keyboard = [
            [InlineKeyboardButton("🌿 Naturaleza", callback_data="lug_naturaleza")],
            [InlineKeyboardButton("🍇 Bodegas", callback_data="lug_bodegas")],
            [InlineKeyboardButton("🛍 Compras", callback_data="lug_compras")],
            [InlineKeyboardButton("🏛 Cultura", callback_data="lug_cultura")],
            [InlineKeyboardButton("⛰ Alta montaña", callback_data="lug_montana")],
            [InlineKeyboardButton("🎢 Aventura", callback_data="lug_aventura")],
            [InlineKeyboardButton("🏠 Menú principal", callback_data="menu_principal")]
        ]
        await query.message.reply_text("Elegí una categoría de lugares:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

   # --- CATEGORÍAS ---
    if data == "lug_naturaleza":
        await query.message.reply_text(
        "🌿 *Naturaleza en Mendoza:*\n"
        "- Parque General San Martín\n"
        "- Reserva Divisadero Largo\n"
        "- Chacras de Coria\n"
        "- Lago del Parque Central\n\n"
        "✏️ *Escribí el nombre del lugar para darte información detallada.*",
        parse_mode="Markdown"
    )
        return

    if data == "lug_bodegas":
        await query.message.reply_text(
        "🍇 *Bodegas recomendadas:*\n"
        "- Catena Zapata\n"
        "- Zuccardi\n"
        "- Trapiche\n"
        "- Norton\n"
        "- Séptima\n\n"
        "✏️ *Escribí el nombre de la bodega para darte más información.*",
        parse_mode="Markdown"
    )
        return


    if data == "lug_compras":
        await query.message.reply_text(
        "🛍 *Compras y paseos:*\n"
        "- Palmares Open Mall\n"
        "- Mendoza Plaza Shopping\n"
        "- Paseo Arístides\n"
        "- Calle Las Heras\n\n"
        "✏️ *Escribí el lugar para darte más información.*",
        parse_mode="Markdown"
    )
        return

    if data == "lug_cultura":
        await query.message.reply_text(
        "🏛 *Cultura e historia:*\n"
        "- Museo del Área Fundacional\n"
        "- Ruinas de San Francisco\n"
        "- Teatro Independencia\n"
        "- Plaza Independencia\n\n"
        "✏️ *Escribí el lugar para darte más información.*",
        parse_mode="Markdown"
    )
        return

    if data == "lug_montana":
        await query.message.reply_text(
        "⛰ *Alta montaña:*\n"
        "- Potrerillos\n"
        "- Uspallata\n"
        "- Penitentes\n"
        "- Puente del Inca\n"
        "- Mirador del Aconcagua\n\n"
        "✏️ *Escribí el lugar para darte más información.*",
        parse_mode="Markdown"
    )
        return

    if data == "lug_aventura":
        await query.message.reply_text(
        "🎢 *Aventura en Mendoza:*\n"
        "- Rafting en Potrerillos\n"
        "- Trekking en Uspallata\n"
        "- Parapente en Cerro Arco\n"
        "- Cabalgatas en montaña\n\n"
        "✏️ *Escribí el lugar para darte más información.*",
        parse_mode="Markdown"
    )
        return


    # Otros botones

    if data == "clima":
        await query.message.reply_text(consultar_clima())
        return await mostrar_menu_rapido_from_query(query)

    if data == "pronostico":
        await query.message.reply_text(consultar_pronostico())
        return await mostrar_menu_rapido_from_query(query)

    if data == "ayuda":
        await query.message.reply_text(
            "Podés pedirme cosas como:\n- Qué lugares visitar\n- Qué comer típico\n- Cómo está el clima\n- Recomendaciones de bodegas"
        )
        return await mostrar_menu_rapido_from_query(query)

    if data == "menu_principal":
        await enviar_menu_principal(query.message)
        return

    await query.message.reply_text("Opción no reconocida 🙂")

# --- ERROR HANDLER ---
async def manejar_errores(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    print(f"Error capturado en handler: {err}")
    # no hacemos crash del bot, solo logueamos
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Ocurrió un error, intentá de nuevo.")
    except Exception:
        pass

# --- CONFIG ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

   
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("lugares", lugares_cmd))
    app.add_handler(CommandHandler("clima", lambda u, c: u.message.reply_text(consultar_clima())))
    app.add_handler(CommandHandler("preguntar", preguntar))

    # callbacks y mensajes
    app.add_handler(CallbackQueryHandler(manejar_botones))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))

    # errores
    app.add_error_handler(manejar_errores)

    print("🌍 Guía Mendoza (Pandito) corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
