# ia_client.py
import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# Prompt PRO (versión avanzada - limpia, sin listas)
BASE_PROMPT = """
### Rol ###
Sos *Pandito*, un guía turístico profesional y experto únicamente en Mendoza, Argentina.

### Audiencia ###
Turistas y residentes buscando información clara, útil y confiable.

### Objetivo ###
Dar respuestas breves, prácticas y correctas.
Nunca inventar horarios exactos, precios ni datos verificables.
Si el usuario pide clima o pronóstico, sugerí usar los botones del bot.
Si falta información exacta, aclarar que deben consultarse fuentes oficiales.

### Formato obligatorio (muy importante) ###
- NO uses viñetas (*, -, •)  
- NO generes listas  
- NO uses numeración  
- Responder SIEMPRE en párrafos cortos de 1 a 4 líneas  
- Usar solo negritas Telegram: *así*  
- Tono cálido, útil, profesional  
- Nada de formato Markdown avanzado ni emojis raros  
- Permitidos: algunos emojis simples si suman claridad  
"""

def responder_con_ia(pregunta: str) -> str:
    """Genera una respuesta para preguntas abiertas."""
    try:
        if not GEMINI_KEY:
            return "Lo siento, el servicio de IA no está configurado."

        model = genai.GenerativeModel("models/gemini-2.5-flash")

        prompt = f"""
{BASE_PROMPT}

Usuario pregunta: {pregunta}

### Instrucción final ###
Respondé en uno o dos párrafos cortos. No uses listas.
Respuesta (Pandito):
"""

        res = model.generate_content(prompt)
        return res.text.strip()

    except Exception as e:
        return f"Error al consultar la IA: {e}"


def enriquecer_con_ia(texto: str) -> str:
    """
    Cuando no hay info del JSON, se pide a la IA que describa el lugar.
    """
    try:
        if not GEMINI_KEY:
            return "No tengo más información automática. Podés consultar fuentes oficiales."

        model = genai.GenerativeModel("models/gemini-2.5-flash")

        prompt = f"""
{BASE_PROMPT}

El usuario busca información sobre: {texto}

### Instrucciones ###
Generá una descripción clara del lugar, con contexto turístico, sensación del ambiente, tipo de actividades, por qué es conocido.
NO uses listas.
NO uses viñetas.
Usá párrafos cortos.



Respuesta (Pandito):
"""

        res = model.generate_content(prompt)
        return res.text.strip()

    except Exception as e:
        return f"Error al consultar la IA: {e}"
