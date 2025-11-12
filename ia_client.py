import os
import google.generativeai as genai
from dotenv import load_dotenv

import requests

#cargo variables de entorno
load_dotenv()

#configuro la api de gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

#funcion consulta clima ACTUAL 
def consultar_clima():
    api_key = os.getenv("WEATHER_API_KEY")
    ciudad = "Mendoza,AR"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={api_key}&units=metric&lang=es"

    try:
        response = requests.get(url)
        data = response.json()
        
        if data["cod"] == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"].capitalize()
            return f"🌤️ Clima actual en Mendoza:\nTemperatura: {temp}°C\nDescripción: {desc}\n"
        else:
            return "No pude obtener el clima en este momento 😕"
        
    except Exception as e:
            return f"Error al consultar el clima: {e}"
        
        
#pronostico del día
def consultar_pronostico():
    api_key = os.getenv("WEATHER_API_KEY")
    lat, lon = -32.8895, -68.8458  # Coordenadas de Mendoza
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=es"
    
    try:
        response = requests.get(url)
        data = response.json()
        
          # Tomamos los primeros 8 períodos de 3 horas = ~24 hs
        hoy = data["list"][:8]

        temps = [item["main"]["temp"] for item in hoy]
        min_temp = min(temps)
        max_temp = max(temps)

        # Probabilidad de lluvia (si existe el campo 'pop')
        pop = max([item.get("pop", 0) for item in hoy]) * 100  # porcentaje

        desc = hoy[0]["weather"][0]["description"].capitalize()

        return (
            f"📅 Pronóstico para hoy en Mendoza:\n"
            f"🌡️ Mínima: {min_temp:.1f}°C | Máxima: {max_temp:.1f}°C\n"
            f"🌧️ Probabilidad de lluvia: {pop:.0f}%\n"
            f"☀️ Cielo: {desc}"
        )

    except Exception as e:
        return f"Error al consultar el pronóstico: {e}"


#función principal de ia
def responder_con_ia(pregunta: str) -> str:
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(
            f"Sos Pandito, un guía turístico experto en Mendoza, Argentina. Respondé en tono amigable, breve y en español:\n\n{pregunta}"
        )
        return response.text
    except Exception as e:
        return f"Error al consultar la IA: {e}"
