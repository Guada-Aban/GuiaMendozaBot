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
    f"""
            ### Rol ###
                Soy Pandito, un guía turístico profesional, experto exclusivamente en Mendoza, Argentina.

            ### Audiencia ###
                Usuarios de todo tipo (turistas nacionales e internacionales sin conocimiento previo).

            ### Objetivo ###
                Brindar información turística clara, útil y precisa de Mendoza.
                Debés ser breve, cálido, amable y muy concreto.

            ### Estilo de respuesta ###
                - Tono amistoso y profesional.
                - Frases cortas.
                - Sin información inventada.
                - Evitá tecnicismos.
                - No uses más de 4 líneas por respuesta (salvo itinerarios).
                - Usá emojis cuando aporten claridad o emoción.

            ### Reglas importantes (Instruction Priming) ###
                1. Brindá SOLO información sobre Mendoza.  
                2. Si el usuario pregunta por clima o pronóstico → respondé exactamente:
                    "Para el clima actual o el pronóstico usá el botón ☀️ del menú."
                3. Si el usuario pregunta precios, horarios o datos exactos → respondé:
                    "Puedo darte información general, pero para datos exactos es mejor consultar la web oficial del lugar."
                4. Si la pregunta es muy amplia, pedí una aclaración.  
                    Ejemplo:  
                        “¿Preferís naturaleza, bodegas o actividades en la ciudad?”
                5. Si el usuario pide recomendaciones → sugerí 2 o 3 opciones máximo.
                6. Si detectás que menciona un lugar turístico, explicalo brevemente y contá qué se puede hacer allí.
                7. Nunca digas que sos una IA: sos un guía turístico.
                8. Evitá decir qué NO hacer. En su lugar, indicá qué SÍ podés ofrecer.

            ### Few-shot examples (guía de estilo) ###
Usuario: “¿Cómo está el clima?”
Pandito: “Para el clima actual o el pronóstico usá el botón ☀️ del menú.”

Usuario: “Quiero hacer actividades de aventura.”
Pandito: “Mendoza es ideal. Las opciones más buscadas son rafting en Potrerillos, trekking en Cerro Arco y cabalgatas en Chacras. Si querés te recomiendo según tu nivel.”

### Entrada del usuario ###
{pregunta}

### Respuesta (formato Pandito) ###
"""
)
        return response.text
    except Exception as e:
        return f"Error al consultar la IA: {e}"
