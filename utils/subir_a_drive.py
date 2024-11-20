import os
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from google.cloud import firestore

# Configurar el logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar credenciales desde la cuenta de servicio
def cargar_credenciales():
    try:
        creds = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        return creds
    except Exception as e:
        logging.error(f"Error al cargar las credenciales de la cuenta de servicio: {str(e)}")
        raise

# Obtener el ID de la carpeta de Dragon usando coincidencia parcial de nombre en Firestore
def obtener_id_dragon(serie_parcial):
    try:
        db = firestore.Client()
        docs = db.collection('donadores').stream()
        for doc in docs:
            data = doc.to_dict()
            if serie_parcial.lower() in data.get('serie', '').lower():
                return data.get('id_dragon')
        raise Exception(f"No se encontró el ID de la carpeta Dragon para la serie que contiene: {serie_parcial}")
    except Exception as e:
        logging.error(f"Error al obtener el ID de Dragon para la serie {serie_parcial}: {str(e)}")
        raise

# Obtener el ID de la carpeta de Fenix usando coincidencia parcial de nombre en Firestore
def obtener_id_fenix(serie_parcial):
    try:
        db = firestore.Client()
        docs = db.collection('donadores').stream()
        for doc in docs:
            data = doc.to_dict()
            if serie_parcial.lower() in data.get('serie', '').lower():
                return data.get('id_fenix')
        raise Exception(f"No se encontró el ID de la carpeta Fenix para la serie que contiene: {serie_parcial}")
    except Exception as e:
        logging.error(f"Error al obtener el ID de Fenix para la serie {serie_parcial}: {str(e)}")
        raise

# Subir el archivo PDF a Google Drive (Unidades Compartidas)
def subir_a_drive(pdf_path, serie, chapter):
    try:
        creds = cargar_credenciales()
        service = build('drive', 'v3', credentials=creds)

        # Verificar que el archivo existe antes de intentar subirlo
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"El archivo no existe: {pdf_path}")

        # Subir a la carpeta de Dragon usando coincidencia parcial de nombre
        id_dragon = obtener_id_dragon(serie)
        media = MediaFileUpload(pdf_path, mimetype='application/pdf')
        file_metadata_dragon = {
            'name': f"{serie}_{chapter}.pdf",
            'parents': [id_dragon]
        }
        archivo_subido_dragon = service.files().create(
            body=file_metadata_dragon,
            media_body=media,
            supportsAllDrives=True,
            fields='id'
        ).execute()

        if not archivo_subido_dragon.get('id'):
            raise Exception(f"Error al subir a la carpeta Dragon: No se obtuvo un ID válido para {pdf_path}")

        logging.info(f"Archivo subido a la carpeta Dragon (ID: {id_dragon}) con éxito, ID del archivo: {archivo_subido_dragon.get('id')}")

        # Subir a la carpeta de Fenix usando coincidencia parcial de nombre
        id_fenix = obtener_id_fenix(serie)
        file_metadata_fenix = {
            'name': f"{serie}_{chapter}.pdf",
            'parents': [id_fenix]
        }
        archivo_subido_fenix = service.files().create(
            body=file_metadata_fenix,
            media_body=media,
            supportsAllDrives=True,
            fields='id'
        ).execute()

        if not archivo_subido_fenix.get('id'):
            raise Exception(f"Error al subir a la carpeta Fenix: No se obtuvo un ID válido para {pdf_path}")

        logging.info(f"Archivo subido a la carpeta Fenix con éxito, ID del archivo: {archivo_subido_fenix.get('id')}")

        return archivo_subido_dragon.get('id'), archivo_subido_fenix.get('id')

    except Exception as e:
        logging.error(f"Error al subir el archivo {pdf_path}: {str(e)}")
        raise

# Función para recorrer la carpeta 'temp/output_pdfs' y subir todos los PDFs
def procesar_archivos_temp():
    temp_dir = './temp/output_pdfs'  # Asegúrate de que este sea el directorio correcto
    logging.info(f"Procesando archivos en: {temp_dir}")

    if not os.path.exists(temp_dir):
        logging.error(f"Directorio {temp_dir} no existe.")
        return

    for file_name in os.listdir(temp_dir):
        if file_name.endswith('.pdf'):
            try:
                pdf_path = os.path.join(temp_dir, file_name)
                
                if not os.path.exists(pdf_path):
                    logging.error(f"El archivo {pdf_path} no existe.")
                    continue

                # Extraer la serie y capítulo del nombre del archivo (formato: serie_capitulo.pdf)
                serie, chapter = file_name.replace('.pdf', '').rsplit('_', 1)

                logging.info(f"Subiendo {file_name} a Drive...")
                subir_a_drive(pdf_path, serie, chapter)
            except ValueError:
                logging.error(f"El archivo {file_name} no tiene el formato esperado. Debe ser 'serie_capitulo.pdf'.")
            except Exception as e:
                logging.error(f"Error al procesar {file_name}: {str(e)}")

# Función para eliminar los archivos PDF de la carpeta después de subirlos
def eliminar_pdfs_output():
    temp_output_dir = r'D:\ZApng ENEDEA\meme\PDF\discord_bot_project\temp\output_pdfs'
    
    if not os.path.exists(temp_output_dir):
        logging.warning(f"El directorio {temp_output_dir} no existe.")
        return
    
    try:
        for file_name in os.listdir(temp_output_dir):
            file_path = os.path.join(temp_output_dir, file_name)
            
            if os.path.exists(file_path) and file_name.endswith('.pdf'):
                os.remove(file_path)
                logging.info(f"Archivo eliminado: {file_path}")
    except Exception as e:
        logging.error(f"Error al eliminar los archivos PDF: {str(e)}")

if __name__ == "__main__":
    try:
        procesar_archivos_temp()
        eliminar_pdfs_output()
    except Exception as e:
        logging.error(f"Error general durante el proceso: {str(e)}")
