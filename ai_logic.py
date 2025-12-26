import google.generativeai as genai
import os
import json
import time

def configure_genai(api_key):
    genai.configure(api_key=api_key)

def upload_file_to_gemini(file_path, mime_type="application/pdf"):
    """
    Sube un archivo a la API de archivos de Gemini para ser usado en los prompts.
    Retorna el objeto File de la API.
    """
    try:
        print(f"Subiendo archivo {file_path} a Gemini...")
        file_obj = genai.upload_file(file_path, mime_type=mime_type)
        print(f"Archivo subido: {file_obj.uri}")
        
        # Esperar a que el archivo esté activo (procesado)
        while file_obj.state.name == "PROCESSING":
            print("Procesando archivo en Gemini...")
            time.sleep(2)
            file_obj = genai.get_file(file_obj.name)
            
        if file_obj.state.name == "FAILED":
            raise Exception("El procesamiento del archivo en Gemini falló.")
            
        return file_obj
    except Exception as e:
        print(f"Error subiendo archivo a Gemini: {e}")
        raise e

def clean_json_string(text_response):
    """Limpia el string de respuesta para obtener solo el JSON."""
    text_response = text_response.strip()
    if text_response.startswith("```json"):
        text_response = text_response[7:]
    if text_response.startswith("```"):
        text_response = text_response[3:]
    if text_response.endswith("```"):
        text_response = text_response[:-3]
    return text_response.strip()

def generate_with_fallback(contents):
    """
    Intenta generar contenido usando una lista de modelos disponibles.
    Accepta 'contents' que puede ser una lista [prompt, file_obj].
    Si el primero falla (ej. 404 Not Found), intenta el siguiente.
    Retorna el objeto response o lanza la última excepción.
    """
    # Lista de modelos MULTIMODALES (que aceptan archivos/PDF)
    models_to_try = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-1.5-flash-001',
        'gemini-1.5-pro',
        'gemini-1.5-pro-latest'
    ]
    
    last_exception = None
    
    for model_name in models_to_try:
        try:
            print(f"Intentando generar con modelo: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(contents)
            return response
        except Exception as e:
            print(f"Fallo con modelo {model_name}: {e}")
            last_exception = e
            time.sleep(1) # Breve pausa antes del siguiente intento
            
    # Si todos fallan, lanzamos la última excepción
    if last_exception:
        raise last_exception

def generate_questions_from_report(gemini_file):
    """
    Analiza el boletín (objeto archivo Gemini) y genera 5 preguntas personalizadas.
    Retorna una lista de strings.
    """
    prompt = """
    Actúa como un orientador vocacional experto. Analiza este boletín de notas (PDF).
    
    Basado en el desempeño académico visible (notas, materias, comentarios si los hay), genera una lista de 5 preguntas clave para entender mejor los intereses, personalidad y preferencias laborales del estudiante.
    Las preguntas deben ser abiertas pero específicas.
    
    IMPORTANTE: Tu respuesta debe ser ESTRICTAMENTE una lista JSON de strings válida. 
    Ejemplo:
    ["¿Pregunta 1?", "¿Pregunta 2?", ...]
    
    No añadas markdown ni texto extra antes o después del JSON.
    """
    
    try:
        # Enviamos el prompt y el archivo
        response = generate_with_fallback([prompt, gemini_file])
        text_response = clean_json_string(response.text)
            
        questions = json.loads(text_response)
        return questions
    except Exception as e:
        print(f"Error generando preguntas (todos los modelos fallaron): {e}")
        # Retornamos error explicito para la UI si es posible, o fallback questions
        return [
            "¿Qué asignaturas disfrutas más estudiar y por qué?",
            "¿Prefieres trabajar solo o en equipo?",
            "¿Te ves trabajando en una oficina o al aire libre?",
            "¿Qué problemas del mundo te gustaría ayudar a resolver?",
            "¿Tienes algún hobby relacionado con la tecnología, el arte o la ciencia?"
        ]

def get_career_recommendations(gemini_file, questions, answers):
    """
    Genera recomendaciones de carrera basadas en el boletín (archivo Gemini) y las respuestas.
    Retorna una lista de diccionarios.
    """
    qa_text = ""
    for q, a in zip(questions, answers):
        qa_text += f"P: {q}\nR: {a}\n\n"
        
    prompt = f"""
    Actúa como un orientador vocacional experto. 
    
    Tienes acceso al boletín de notas (archivo adjunto) y a la siguiente entrevista personal:
    
    {qa_text}
    
    TAREA:
    Sugiere las 5 mejores carreras universitarias para este estudiante. 
    Para cada carrera, asigna un porcentaje de afinidad (0-100) basado en sus notas (del PDF) y sus respuestas.
    
    IMPORTANTE: Tu respuesta debe ser ESTRICTAMENTE una lista JSON de objetos con las claves: "carrera", "porcentaje" (entero), y "razon" (breve explicación).
    Ordena las carreras de mayor a menor porcentaje.
    
    Ejemplo de formato:
    [
        {{"carrera": "Ingeniería Civil", "porcentaje": 89, "razon": "Excelentes notas en física y matemáticas, interés en construcción."}},
        {{"carrera": "Medicina", "porcentaje": 60, "razon": "..."}}
    ]
    
    No añadas markdown ni texto extra. Solo el JSON.
    """
    
    try:
        response = generate_with_fallback([prompt, gemini_file])
        text_response = clean_json_string(response.text)
            
        recommendations = json.loads(text_response)
        return recommendations
    except Exception as e:
        print(f"Error generando recomendaciones: {e}")
        raw_resp = 'No response'
        if 'response' in locals():
            try:
                raw_resp = response.text
            except:
                pass
        return [{"error": str(e), "raw_response": raw_resp}]
