import google.generativeai as genai
import os
import json

def configure_genai(api_key):
    genai.configure(api_key=api_key)

def generate_questions_from_report(report_text):
    """
    Analiza el texto del boletín y genera 5 preguntas personalizadas.
    Retorna una lista de strings.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Actúa como un orientador vocacional experto. He analizado el siguiente boletín de notas de un estudiante:
    
    '''
    {report_text[:4000]}  # Limitamos el texto para evitar tokens excesivos si es muy largo
    '''
    
    Basado en su desempeño académico (sus fortalezas y debilidades), genera una lista de 5 preguntas clave para entender mejor sus intereses, personalidad y preferencias laborales. 
    Las preguntas deben ser abiertas pero específicas.
    
    IMPORTANTE: Tu respuesta debe ser ESTRICTAMENTE una lista JSON de strings. Ejemplo:
    ["¿Pregunta 1?", "¿Pregunta 2?", ...]
    No añadas markdown ```json ... ``` ni texto extra. Solo el array crudo.
    """
    
    try:
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        # Limpieza básica por si el modelo incluye backticks
        if text_response.startswith("```json"):
            text_response = text_response[7:-3]
        elif text_response.startswith("```"):
            text_response = text_response[3:-3]
            
        questions = json.loads(text_response)
        return questions
    except Exception as e:
        print(f"Error generando preguntas: {e}")
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
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    qa_text = ""
    for q, a in zip(questions, answers):
        qa_text += f"P: {q}\nR: {a}\n\n"
        
    prompt = f"""
    Actúa como un orientador vocacional experto. 
    
    Información del estudiante:
    1. Boletín de notas (extracto):
    '''
    {report_text[:2000]}
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
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        
        if text_response.startswith("```json"):
            text_response = text_response[7:-3]
        elif text_response.startswith("```"):
            text_response = text_response[3:-3]
            
        recommendations = json.loads(text_response)
        return recommendations
    except Exception as e:
        print(f"Error generando recomendaciones: {e}")
        return []
