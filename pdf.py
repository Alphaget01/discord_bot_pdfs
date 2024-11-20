import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurar intents del bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Obtener el ID del servidor desde las variables de entorno
GUILD_ID = os.getenv("DISCORD_GUILD_ID")

@bot.event
async def on_ready():
    logging.info(f"{bot.user.name} ha iniciado sesión en Discord")

    # Lista de extensiones a cargar
    extensiones = [
        "comandos.registrodonadores",
        "comandos.subirpdf",
        "comandos.dameellink"
    ]

    # Cargar las extensiones
    for extension in extensiones:
        try:
            await bot.load_extension(extension)
            logging.info(f"Extensión '{extension}' cargada correctamente.")
        except commands.ExtensionAlreadyLoaded:
            logging.warning(f"La extensión '{extension}' ya estaba cargada.")
        except commands.ExtensionError as e:
            logging.error(f"Error al cargar la extensión '{extension}': {e}")
        except Exception as e:
            logging.error(f"Error inesperado al cargar '{extension}': {e}")

    # Sincronizar comandos slash (por servidor específico o global)
    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            synced = await bot.tree.sync(guild=guild)  # Sincronización específica por servidor
            logging.info(f"Comandos slash sincronizados para el servidor {GUILD_ID}: {len(synced)} comandos.")
        else:
            synced = await bot.tree.sync()  # Sincronización global
            logging.info(f"Comandos slash globales sincronizados: {len(synced)} comandos.")
        
        for command in synced:
            logging.info(f"Comando registrado: {command.name}")
    except discord.errors.HTTPException as e:
        logging.error(f"Error HTTP al sincronizar comandos slash: {e.status} - {e.text}")
    except Exception as e:
        logging.error(f"Error al sincronizar comandos slash: {e}")

# Ejemplo de comando de prueba
@bot.tree.command(name="saludo", description="Un comando de prueba que saluda")
async def saludo(interaction: discord.Interaction):
    logging.info("El comando /saludo fue ejecutado.")
    await interaction.response.send_message("¡Hola! Este es un saludo de prueba.", ephemeral=True)

# Ejecutar el bot con el token de Discord
bot.run(os.getenv("DISCORD_TOKEN"))
