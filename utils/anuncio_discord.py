import discord
import logging
from google.cloud import firestore

class AnuncioDiscord:
    def __init__(self, bot):
        self.bot = bot
        self.db = firestore.Client()

    # Función para obtener los datos de la serie desde Firestore (incluye ID Dragon, ID Fenix y URL)
    def obtener_datos_serie(self, serie_parcial):
        logging.info(f"Buscando datos de la serie en Firestore: {serie_parcial}")
        docs = self.db.collection('donadores').stream()

        for doc in docs:
            data = doc.to_dict()
            serie_en_firestore = data.get('serie', '').lower()
            logging.info(f"Comparando {serie_parcial.lower()} con {serie_en_firestore}")

            if serie_parcial.lower() in serie_en_firestore:
                id_dragon = data.get('id_dragon')
                id_fenix = data.get('id_fenix')
                url = data.get('url', None)  # Obtener el URL si existe
                logging.info(f"Datos encontrados para la serie: ID Dragon: {id_dragon}, ID Fenix: {id_fenix}, URL: {url}")
                return id_dragon, id_fenix, url

        raise Exception(f"No se encontraron los datos para la serie: {serie_parcial}")

    async def hacer_anuncio(self, serie, chapter, link_drive_dragon, link_drive_fenix, interaction):

        try:
            # Obtener los datos de la serie (ID Dragon, ID Fenix y URL)
            id_dragon, id_fenix, url = self.obtener_datos_serie(serie)

            if not id_dragon:
                raise Exception(f"No se encontró el ID de la carpeta Dragon para la serie: {serie}")

            if not id_fenix:
                raise Exception(f"No se encontró el ID de la carpeta Fenix para la serie: {serie}")

            # Construir los enlaces con los IDs de las carpetas Dragon y Fenix
            link_drive_dragon = f"https://drive.google.com/drive/folders/{id_dragon}"
            link_drive_fenix = f"https://drive.google.com/drive/folders/{id_fenix}"

            # IDs de los canales y roles
            canal_1_id = 1233183267323117618  # ID del primer canal
            canal_2_id = 1233183106282819594  # ID del segundo canal
            rol_1_id = 1233180174649131070    # ID del rol del primer canal
            rol_2_id = 1233179974270455939    # ID del rol del segundo canal

            # Mensaje de anuncio para el canal de Dragon
            embed_dragon = discord.Embed(
                title="# ¡Nuevo capítulo disponible!",
                description=(
                    f':loudspeaker: Buenas, nuevo capítulo de **{serie}** :rotating_light:\n'
                    f':newspaper2: Ya están los caps en el drive al día con las raws\n'
                    f':newspaper2: **Último cap - Capítulo {chapter}**\n'
                    f'# :link: [Link de la carpeta PDF (Dragon)]({link_drive_dragon})'
                ),
                color=discord.Color.blue()
            )

            # Mensaje de anuncio para el canal de Fenix
            embed_fenix = discord.Embed(
                title="# ¡Nuevo capítulo disponible!",
                description=( 
                    f':loudspeaker: Buenas, nuevo capítulo de **{serie}** :rotating_light:\n'
                    f':newspaper2: Ya están los caps en el drive al día con las raws\n'
                    f':newspaper2: **Último cap - Capítulo {chapter}**\n'
                    f'# :link: [Link de la carpeta PDF (Fenix)]({link_drive_fenix})'
                ),
                color=discord.Color.blue()
            )

            # Si se obtuvo una URL de la imagen, agregarla a los embeds
            if url:
                embed_dragon.set_image(url=url)
                embed_fenix.set_image(url=url)

            # Hacer el anuncio en el primer canal (solo el enlace de Dragon)
            canal_1 = self.bot.get_channel(canal_1_id)
            if canal_1:
                await canal_1.send(content=f"<@&{rol_1_id}>", embed=embed_dragon)
                logging.info(f"Anuncio enviado correctamente en el canal 1 (ID: {canal_1_id})")
            else:
                logging.error(f"Error: No se pudo encontrar el canal con ID {canal_1_id}")

            # Hacer el anuncio en el segundo canal (solo el enlace de Fenix)
            canal_2 = self.bot.get_channel(canal_2_id)
            if canal_2:
                await canal_2.send(content=f"<@&{rol_2_id}>", embed=embed_fenix)
                logging.info(f"Anuncio enviado correctamente en el canal 2 (ID: {canal_2_id})")
            else:
                logging.error(f"Error: No se pudo encontrar el canal con ID {canal_2_id}")

            # Mensaje de confirmación en el canal de origen del comando
            embed_confirmacion = discord.Embed(
                title="Proceso completado",
                description="PDF subido a las carpetas Dragon y Fenix, y los anuncios se realizaron en Discord.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed_confirmacion)
            logging.info("Mensaje de confirmación enviado correctamente.")

        except Exception as e:
            logging.error(f"Error al hacer el anuncio: {str(e)}")
            await interaction.followup.send(f"Error al hacer el anuncio: {str(e)}")
