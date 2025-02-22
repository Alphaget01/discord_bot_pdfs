import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
import base64
import logging
from pathlib import Path

# Configuración de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot_logs.log"),  # Log en archivo
        logging.StreamHandler(),  # Log en consola
    ],
)

# Cargar el archivo .env
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# Decodificar el contenido base64 del servicio y guardar en un archivo temporal
def setup_google_credentials():
    try:
        base64_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not base64_credentials:
            raise ValueError("No se encontró GOOGLE_APPLICATION_CREDENTIALS en el archivo .env")

        temp_path = "./data/service_account.json"  # Ruta donde se creará temporalmente
        with open(temp_path, "w") as temp_file:
            temp_file.write(base64.b64decode(base64_credentials).decode("utf-8"))
        
        logging.info(f"Credenciales de Google guardadas en: {temp_path}")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path
    except Exception as e:
        logging.error(f"Error al configurar las credenciales de Google: {e}")
        raise

# Configurar los intents del bot
intents = discord.Intents.default()
intents.message_content = True  # Necesario para leer contenido de mensajes
intents.guilds = True

# Inicializar el bot
bot = commands.Bot(command_prefix="/", intents=intents)

# Variables de entorno
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
if not GUILD_ID:
    logging.error("No se encontró DISCORD_GUILD_ID en el archivo .env")
    exit(1)

logging.info(f"DISCORD_GUILD_ID: {GUILD_ID}")

@bot.tree.command(name="saludo", description="Un comando de prueba que saluda")
async def saludo(interaction: discord.Interaction):
    logging.info("El comando /saludo fue ejecutado.")
    await interaction.response.send_message("¡Hola, este es un comando de prueba!", ephemeral=True)

@bot.event
async def on_ready():
    logging.info(f"{bot.user.name} ha iniciado sesión en Discord")

    # Configurar Google Application Credentials
    setup_google_credentials()

    # Cargar extensiones (comandos)
    extensions = [
        "comandos.registrodonadores",
        "comandos.subirpdf",
        "comandos.dameellink",
        "comandos.actualizarpdf",
    ]
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            logging.info(f"Extensión '{extension}' cargada correctamente.")
        except commands.ExtensionAlreadyLoaded:
            logging.warning(f"La extensión '{extension}' ya estaba cargada.")
        except commands.ExtensionError as e:
            logging.error(f"Error al cargar la extensión '{extension}': {e}")
        except Exception as e:
            logging.error(f"Error inesperado al cargar '{extension}': {e}")

    # Sincronización de comandos slash global
    try:
        synced = await bot.tree.sync()
        logging.info(f"Comandos slash globales sincronizados correctamente: {len(synced)} comandos.")
        for command in synced:
            logging.info(f"Comando sincronizado: {command.name}")
    except discord.errors.HTTPException as e:
        logging.error(f"Error HTTP al sincronizar comandos slash: {e.status} - {e.text}")
    except Exception as e:
        logging.error(f"Error al sincronizar comandos slash: {e}")

# Ejecutar el bot con el token de Discord desde el archivo .env
if __name__ == "__main__":
    try:
        bot.run(os.getenv("DISCORD_TOKEN"))
    except Exception as e:
        logging.error(f"Error al iniciar el bot: {e}")
