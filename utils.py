import pypdf

def extract_text_from_pdf(uploaded_file):
    """
    Extrae el texto de un archivo PDF subido a través de Streamlit.
    """
    try:
        pdf_reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error al leer el PDF: {e}"
