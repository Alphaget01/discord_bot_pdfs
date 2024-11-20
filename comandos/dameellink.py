import discord
from discord import app_commands
from discord.ext import commands
from google.cloud import firestore
import os
import logging

class DameElLink(commands.Cog):
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

    @app_commands.command(name="dameellink", description="Obtén los enlaces de donadores para Dragon y Fenix de una serie")
    @app_commands.describe(serie="Nombre de la serie para obtener los enlaces")
    @app_commands.autocomplete(serie=serie_autocomplete)  # Habilitar autocompletado para "serie"
    async def dame_el_link(self, interaction: discord.Interaction, serie: str):
        try:
            # Buscar la serie en Firestore
            series_ref = self.db.collection(os.getenv("FIRESTORE_COLLECTION"))
            query = series_ref.where("serie", "==", serie).limit(1).stream()

            # Procesar el documento encontrado
            serie_doc = next(query, None)
            if not serie_doc:
                await interaction.response.send_message("La serie no fue encontrada en la base de datos.", ephemeral=True)
                return
            
            # Extraer los datos necesarios
            data = serie_doc.to_dict()
            id_dragon = data.get("id_dragon")
            id_fenix = data.get("id_fenix")
            url = data.get("url")

            # Crear los enlaces completos
            link_dragon = f":link: [Link de la carpeta PDF (Dragon)](https://drive.google.com/drive/folders/{id_dragon})"
            link_fenix = f":link: [Link de la carpeta PDF (Fenix)](https://drive.google.com/drive/folders/{id_fenix})"

            # Crear el embed con los enlaces y la URL de imagen
            embed = discord.Embed(title=f"Enlaces para la serie: {serie}", color=discord.Color.blue())
            embed.add_field(name="Link de Dragon", value=link_dragon, inline=False)
            embed.add_field(name="Link de Fenix", value=link_fenix, inline=False)
            embed.set_image(url=url)
            embed.set_footer(text="Enlaces generados por el bot")

            # Enviar el embed
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logging.error(f"Error al obtener los enlaces para la serie '{serie}': {str(e)}")
            await interaction.response.send_message("Ocurrió un error al obtener los enlaces.", ephemeral=True)

# Configuración para agregar el comando a tu bot
async def setup(bot):
    await bot.add_cog(DameElLink(bot))
