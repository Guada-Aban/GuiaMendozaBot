import os
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

# Configurar la API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def responder_con_ia(pregunta: str) -> str:
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(
            f"Sos Pandito, un guía turístico experto en Mendoza, Argentina. Respondé en tono amigable, breve y en español:\n\n{pregunta}"
        )
        return response.text
    except Exception as e:
        return f"Error al consultar la IA: {e}"
