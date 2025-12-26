import google.generativeai as genai
import os
import json
import time

def configure_genai(api_key):
    genai.configure(api_key=api_key)

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

def generate_with_fallback(prompt):
    """
    Intenta generar contenido usando una lista de modelos disponibles.
    Si el primero falla (ej. 404 Not Found), intenta el siguiente.
    Retorna el objeto response o lanza la última excepción.
    """
    # Lista de modelos a probar en orden de preferencia
    models_to_try = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-001',
        'gemini-1.5-flash-latest',
        'gemini-pro',
        'gemini-1.5-pro'
    ]
    
    last_exception = None
    
    for model_name in models_to_try:
        try:
            print(f"Intentando generar con modelo: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response
        except Exception as e:
            print(f"Fallo con modelo {model_name}: {e}")
            last_exception = e
            time.sleep(1) # Breve pausa antes del siguiente intento
            
    # Si todos fallan, lanzamos la última excepción
    if last_exception:
        raise last_exception

def generate_questions_from_report(report_text):
    """
    Analiza el texto del boletín y genera 5 preguntas personalizadas.
    Retorna una lista de strings.
    """
    prompt = f"""
    Actúa como un orientador vocacional experto. He analizado el siguiente boletín de notas de un estudiante:
    
    '''
    {report_text}
    '''
    
    Basado en su desempeño académico (sus fortalezas y debilidades), genera una lista de 5 preguntas clave para entender mejor sus intereses, personalidad y preferencias laborales. 
    Las preguntas deben ser abiertas pero específicas.
    
    IMPORTANTE: Tu respuesta debe ser ESTRICTAMENTE una lista JSON de strings válida. 
    Ejemplo:
    ["¿Pregunta 1?", "¿Pregunta 2?", ...]
    
    No añadas markdown ni texto extra antes o después del JSON.
    """
    
    try:
        response = generate_with_fallback(prompt)
        text_response = clean_json_string(response.text)
            
        questions = json.loads(text_response)
        return questions
    except Exception as e:
        print(f"Error generando preguntas (todos los modelos fallaron): {e}")
        # Preguntas por defecto en caso de error
        return [
            "¿Qué asignaturas disfrutas más estudiar y por qué?",
            "¿Prefieres trabajar solo o en equipo?",
            "¿Te ves trabajando en una oficina o al aire libre?",
            "¿Qué problemas del mundo te gustaría ayudar a resolver?",
            "¿Tienes algún hobby relacionado con la tecnología, el arte o la ciencia?"
        ]

def get_career_recommendations(report_text, questions, answers):
    """
    Genera recomendaciones de carrera basadas en el boletín y las respuestas.
    Retorna una lista de diccionarios: [{'carrera': 'Nombre', 'porcentaje': 85, 'razon': '...'}]
    Si hay error, retorna una lista vacía y el mensaje de error en print.
    """
    qa_text = ""
    for q, a in zip(questions, answers):
        qa_text += f"P: {q}\nR: {a}\n\n"
        
    prompt = f"""
    Actúa como un orientador vocacional experto. 
    
    Información del estudiante:
    1. Boletín de notas completo:
    '''
    {report_text}
    '''
    
    2. Entrevista personal:
    {qa_text}
    
    TAREA:
    Sugiere las 5 mejores carreras universitarias para este estudiante. 
    Para cada carrera, asigna un porcentaje de afinidad (0-100) basado en sus notas y respuestas.
    
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
        response = generate_with_fallback(prompt)
        text_response = clean_json_string(response.text)
            
        recommendations = json.loads(text_response)
        return recommendations
    except Exception as e:
        print(f"Error generando recomendaciones (todos los modelos fallaron): {e}")
        # Devolvemos un objeto de error especial para que la UI lo muestre
        raw_resp = 'No response'
        if 'response' in locals():
            try:
                raw_resp = response.text
            except:
                pass
        return [{"error": str(e), "raw_response": raw_resp}]
