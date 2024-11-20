import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
import logging
from pathlib import Path

# Configuración del registro de logs
logging.basicConfig(
    level=logging.INFO,  # Nivel de log: INFO, puedes cambiarlo a DEBUG para más detalles
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato del log
    handlers=[
        logging.FileHandler("bot_logs.log"),  # Guardar en archivo
        logging.StreamHandler()  # Mostrar en consola
    ]
)

# Cargar el archivo .env desde la ruta específica
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Intents necesarios para el bot
intents = discord.Intents.default()
intents.message_content = True  # Permitir leer contenido de los mensajes
intents.guilds = True  # Habilitar eventos relacionados con servidores

# Configuración del bot
bot = commands.Bot(command_prefix="/", intents=intents)

# Verificar que DISCORD_GUILD_ID esté cargado
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
logging.info(f"DISCORD_GUILD_ID: {GUILD_ID}")  # Log para depuración
logging.info(f"DISCORD_TOKEN: {os.getenv('DISCORD_TOKEN')}")  # Log para depuración

# Comando de prueba
@bot.tree.command(name="saludo", description="Un comando de prueba que saluda")
async def saludo(interaction: discord.Interaction):
    logging.info("El comando /saludo fue ejecutado.")
    await interaction.response.send_message("¡Hola, este es un comando de prueba!", ephemeral=True)

@bot.event
async def on_ready():
    logging.info(f'{bot.user.name} ha iniciado sesión en Discord')

    # Cargar extensiones (comandos)
    try:
        await bot.load_extension("comandos.registrodonadores")
        logging.info("Comando 'registrodonadores' cargado correctamente.")
    except commands.ExtensionAlreadyLoaded as e:
        logging.warning(f"La extensión {e.name} ya estaba cargada.")  # Cambiado para manejar ExtensionAlreadyLoaded
    except commands.ExtensionError as e:
        logging.error(f"Error al cargar la extensión {e.name}: {str(e)}")
    except Exception as e:
        logging.error(f"Error inesperado al cargar comandos: {e}")

    try:
        await bot.load_extension("comandos.subirpdf")
        logging.info("Comando 'subirpdf' cargado correctamente.")
    except commands.ExtensionAlreadyLoaded as e:
        logging.warning(f"La extensión {e.name} ya estaba cargada.")
    except commands.ExtensionError as e:
        logging.error(f"Error al cargar la extensión {e.name}: {str(e)}")
    except Exception as e:
        logging.error(f"Error inesperado al cargar comandos: {e}")
    
    try:
        await bot.load_extension("comandos.dameellink")
        logging.info("Comando 'dameellink' cargado correctamente.")
    except commands.ExtensionAlreadyLoaded as e:
        logging.warning(f"La extensión {e.name} ya estaba cargada.")
    except commands.ExtensionError as e:
        logging.error(f"Error al cargar la extensión {e.name}: {str(e)}")
    except Exception as e:
        logging.error(f"Error inesperado al cargar comandos: {e}")

    # Sincronización de comandos slash global
    try:
        synced = await bot.tree.sync()  # Sincronizar todos los comandos globalmente
        logging.info(f"Comandos slash globales sincronizados correctamente: {len(synced)} comandos.")
        for command in synced:
            logging.info(f"Comando sincronizado: {command.name}")
    except discord.errors.HTTPException as e:
        logging.error(f"Error HTTP al sincronizar comandos slash: {e.status} - {e.text}")
    except Exception as e:
        logging.error(f"Error al sincronizar comandos slash: {e}")

# Ejecutar el bot con el token de Discord desde el archivo .env
bot.run(os.getenv("DISCORD_TOKEN"))
