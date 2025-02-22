import discord
from discord import app_commands
from discord.ext import commands
from google.cloud import firestore
import os
import logging

class ActualizarPDF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = firestore.Client()

    # Método para el autocompletado del nombre de la serie
    async def serie_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            series_ref = self.db.collection(os.getenv("FIRESTORE_COLLECTION"))
            series_docs = series_ref.stream()
            
            # Recopilar todas las series y filtrar según el texto ingresado
            series = [doc.to_dict().get('serie') for doc in series_docs if doc.to_dict().get('serie')]
            series_filtradas = [serie for serie in series if current.lower() in serie.lower()]
            series_limitadas = series_filtradas[:25]  # Limitar a 25 resultados
            
            return [app_commands.Choice(name=serie, value=serie) for serie in series_limitadas]
        except Exception as e:
            logging.error(f"Error en autocompletado de serie: {str(e)}")
            return []

    @app_commands.command(name="actualizarpdf", description="Actualiza la URL de la imagen para una serie")
    @app_commands.describe(serie="Nombre de la serie", url="Nueva URL de la imagen")
    @app_commands.autocomplete(serie=serie_autocomplete)  # Habilitar autocompletado para "serie"
    async def actualizar_pdf(self, interaction: discord.Interaction, serie: str, url: str):
        try:
            # Buscar la serie en Firestore
            series_ref = self.db.collection(os.getenv("FIRESTORE_COLLECTION"))
            query = series_ref.where("serie", "==", serie).limit(1).stream()

            # Procesar el documento encontrado
            serie_doc = next(query, None)
            if not serie_doc:
                await interaction.response.send_message("La serie no fue encontrada en la base de datos sonso.", ephemeral=True)
                return
            
            # Actualizar la URL en Firestore
            serie_ref = self.db.collection(os.getenv("FIRESTORE_COLLECTION")).document(serie_doc.id)
            serie_ref.update({"url": url})

            # Confirmación de la actualización
            await interaction.response.send_message(f"La URL de la serie '{serie}' ha sido actualizada correctamente.", ephemeral=True)

        except Exception as e:
            logging.error(f"Error al actualizar el PDF para la serie '{serie}': {str(e)}")
            await interaction.response.send_message("Ocurrió un error al actualizar la URL del PDF.", ephemeral=True)

# Configuración para agregar el comando a tu bot
async def setup(bot):
    await bot.add_cog(ActualizarPDF(bot))
