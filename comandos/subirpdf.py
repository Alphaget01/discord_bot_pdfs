import discord
from discord import app_commands
from discord.ext import commands
from google.cloud import firestore
import os
from utils.subir_a_drive import eliminar_pdfs_output
import asyncio
import logging
from utils.subir_a_drive import subir_a_drive  # Importar la función para subir a Google Drive
from utils.anuncio_discord import AnuncioDiscord  # Importar la clase para hacer anuncios en Discord

# Configuración del registro de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_logs.log"),
        logging.StreamHandler()
    ]
)

class SubirPDF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = firestore.Client()
        self.anuncio_discord = AnuncioDiscord(bot)

    # Método para obtener las opciones de autocompletado desde Firestore
    async def serie_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            series_ref = self.db.collection(os.getenv("FIRESTORE_COLLECTION"))
            series_docs = series_ref.stream()
            
            # Recopilar todas las series
            series = [doc.to_dict().get('serie') for doc in series_docs if doc.to_dict().get('serie')]
            
            # Filtrar las series basadas en el texto ingresado por el usuario (current)
            series_filtradas = [serie for serie in series if current.lower() in serie.lower()]
            
            # Limitar el número de resultados a 25 (el máximo permitido por Discord)
            series_limitadas = series_filtradas[:25]
            
            # Retornar las opciones para el autocompletado
            return [app_commands.Choice(name=serie, value=serie) for serie in series_limitadas]
        
        except Exception as e:
            logging.error(f"Error al obtener series para autocompletado: {str(e)}")
            return []

    async def ejecutar_script_node(self, zip_path, serie, chapter):
        proceso = await asyncio.create_subprocess_exec(
            'node', './utils_js/convertir_las_imágenes_a_pdf.js', zip_path, serie, str(chapter),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proceso.communicate()

        if proceso.returncode != 0:
            raise Exception(f"Error en la conversión: {stderr.decode()}")
        return stdout.decode()

    @app_commands.command(name="subirpdf", description="Subir un archivo ZIP para convertir a PDF y subir a Google Drive")
    @app_commands.describe(zip_file="Archivo ZIP para convertir a PDF", serie="Nombre de la serie", chapter="Número de capítulo")
    @app_commands.autocomplete(serie=serie_autocomplete)  # Habilitar autocompletado para "serie"
    @app_commands.checks.has_role(int(os.getenv("ROL_AUTORIZADO")))  # Verificar que el usuario tenga el rol autorizado
    async def subir_pdf(self, interaction: discord.Interaction, zip_file: discord.Attachment, serie: str, chapter: int):
        logging.info(f"Iniciando proceso para la serie {serie}, capítulo {chapter}.")

        # Validar que el archivo sea un ZIP
        if not zip_file.filename.endswith(".zip"):
            await interaction.response.send_message("Por favor adjunta un archivo ZIP válido.", ephemeral=True)
            logging.error(f"El archivo {zip_file.filename} no es un archivo ZIP.")
            return

        # Crear el directorio "temp" si no existe
        temp_dir = "./temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            logging.info(f"Directorio '{temp_dir}' creado.")

        # Descargar el archivo ZIP adjunto
        await interaction.response.send_message("Descargando archivo ZIP...", ephemeral=True)
        zip_path = f"{temp_dir}/{zip_file.filename}"  # Ruta temporal para guardar el ZIP

        try:
            await zip_file.save(zip_path)
            logging.info(f"Archivo ZIP guardado en {zip_path}")
            await interaction.followup.send(f"Archivo ZIP {zip_file.filename} guardado.", ephemeral=True)
        except Exception as e:
            logging.error(f"Error al guardar el archivo ZIP: {str(e)}")
            await interaction.followup.send(f"Error al guardar el archivo ZIP: {str(e)}", ephemeral=True)
            return

        # Convertir el ZIP a PDF usando el script de Node.js
        await interaction.followup.send("Convirtiendo imágenes a PDF...", ephemeral=True)

        try:
            # Asegúrate de pasar los tres argumentos a ejecutar_script_node
            resultado = await self.ejecutar_script_node(zip_path, serie, chapter)
            logging.info(f"Imágenes convertidas a PDF para la serie {serie}, capítulo {chapter}.")
            await interaction.followup.send(f"Imágenes convertidas a PDF para la serie {serie}, capítulo {chapter}.", ephemeral=True)
        except Exception as e:
            logging.error(f"Error al convertir imágenes a PDF: {str(e)}")
            await interaction.followup.send(f"Error al convertir imágenes a PDF: {str(e)}", ephemeral=True)
            return

        # Subir el PDF a Google Drive
        pdf_path = os.path.join("./temp/output_pdfs", f"{serie}_{chapter}.pdf")
        await interaction.followup.send("Subiendo PDF a Google Drive...", ephemeral=True)
        logging.info(f"Subiendo el archivo {pdf_path} a Google Drive.")

        try:
            id_dragon, id_fenix = subir_a_drive(pdf_path, serie, chapter)
            logging.info(f"PDF subido con éxito a Google Drive para la serie {serie}, capítulo {chapter}.")
            await interaction.followup.send(f"PDF subido a Google Drive para la serie {serie}, capítulo {chapter}.", ephemeral=True)
        except Exception as e:
            logging.error(f"Error al subir el PDF a Google Drive: {str(e)}")
            await interaction.followup.send("Error al subir el PDF a Google Drive.", ephemeral=True)
            return

        # Hacer el anuncio en Discord
        link_drive_dragon = f"https://drive.google.com/drive/folders/{id_dragon}"
        link_drive_fenix = f"https://drive.google.com/drive/folders/{id_fenix}"
        await self.anuncio_discord.hacer_anuncio(serie, chapter, link_drive_dragon, link_drive_fenix, interaction)

        logging.info(f"PDF de la serie {serie}, capítulo {chapter} subido y anunciado correctamente.")

        # Eliminar los archivos PDF de la carpeta
        eliminar_pdfs_output()
        logging.info(f"Los archivos PDF de {serie}, capítulo {chapter} han sido eliminados.")

async def setup(bot):
    await bot.add_cog(SubirPDF(bot))
