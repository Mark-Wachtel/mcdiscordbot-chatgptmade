import os
import subprocess
import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
import asyncio
import json
from datetime import datetime

TOKEN = "DISCORD TOKEN"
MC_SERVER_IP = "MINECRAFT SERVER ID"
MC_SERVER_PORT = 32565  # Ändere dies, falls dein Query-Port anders ist

GUILD_ID = DISCORD SERVER ID  # Setze die ID deines Servers
STATUS_CHANNEL_ID = DISCORD CHANNEL ID  # Setze die ID des Channels

backup_time = "Noch kein Backup gesetzt"
last_update_time = "Noch kein Update gesetzt"
last_update_link = "Kein Link gesetzt"
maintenance_mode = False

backup_file = "backup_time.json"
update_file = "last_update.json"

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- Daten Laden -----------------
def load_data():
    global backup_time, last_update_time, last_update_link
    if os.path.exists(backup_file):
        with open(backup_file, "r") as f:
            backup_time = json.load(f).get("backup_time", "Noch kein Backup gesetzt")

    if os.path.exists(update_file):
        with open(update_file, "r") as f:
            data = json.load(f)
            last_update_time = data.get("last_update_time", "Noch kein Update gesetzt")
            last_update_link = data.get("last_update_link", "Kein Link gesetzt")

def save_backup_time():
    with open(backup_file, "w") as f:
        json.dump({"backup_time": backup_time}, f)

def save_update_time():
    with open(update_file, "w") as f:
        json.dump({"last_update_time": last_update_time, "last_update_link": last_update_link}, f)

# ----------------- Bot Events -----------------
@bot.event
async def on_ready():
    print(f"{bot.user} ist online!")
    load_data()
    update_status.start()
    send_daily_backup.start()
    send_daily_update.start()

# ----------------- Minecraft Server Status -----------------
def get_mc_status():
    try:
        server = JavaServer.lookup(f"{MC_SERVER_IP}:{MC_SERVER_PORT}")
        status = server.status()
        return True, status.players.online
    except:
        return False, 0

last_status = None  # Speichert den letzten Status

@tasks.loop(seconds=10)  # Prüft alle 10 Sekunden auf Änderungen
async def update_status():
    global maintenance_mode, last_status
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return
    channel = guild.get_channel(STATUS_CHANNEL_ID)
    if not channel:
        return

    online, players = get_mc_status()
    new_status = ("maintenance" if maintenance_mode else 
                  ("online", players) if online else 
                  "offline")

    # Prüfen, ob sich der Status geändert hat
    if new_status != last_status:
        last_status = new_status  # Status aktualisieren

        if maintenance_mode:
            new_name = "🟠Minecraft:_Wartung"
            status_message = "🔧 Der Server ist im Wartungsmodus."
        elif online:
            new_name = f"🟢Minecraft:_{players}_Spieler"
            status_message = f"🟢 Der Server ist online, {players} Spieler sind auf dem Server."
        else:
            new_name = "🔴Minecraft:_Offline"
            status_message = "🔴 Der Server ist offline."

        # Channel-Name aktualisieren
        await channel.edit(name=new_name)
        await channel.send(status_message)  # Nachricht nur bei Änderung senden

# ----------------- Tägliche Backup- & Update-Erinnerung -----------------
@tasks.loop(hours=24)
async def send_daily_backup():
    now = datetime.now()
    if now.hour == 12:
        await announce_backup_time()

@tasks.loop(hours=24)
async def send_daily_update():
    now = datetime.now()
    if now.hour == 12:
        await announce_last_update_time()

async def announce_backup_time():
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if channel:
        await channel.send(f"📁 Letztes Backup: {backup_time}")

async def announce_last_update_time():
    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if channel:
        await channel.send(f"🛠️ Letztes Update: {last_update_time}\n🔗 Link: {last_update_link}")

# ----------------- Discord Befehle -----------------
@bot.command()
async def server_status(ctx):
    online, players = get_mc_status()
    status_msg = "🟢 Online" if online else "🔴 Offline"
    await ctx.send(f"Server Status: {status_msg}, Spieler Online: {players}")

@bot.command()
async def player_online(ctx):
    _, players = get_mc_status()
    await ctx.send(f"Es sind {players} Spieler online.")

@bot.command()
async def bot_status(ctx):
    await ctx.send("✅ Bot is running!")

@bot.command()
async def backup(ctx):
    await ctx.send(f"📁 Letztes Backup: {backup_time}")

@bot.command()
async def update(ctx):
    await ctx.send(f"🛠️ Letztes Update: {last_update_time}\n🔗 Link: {last_update_link}")

@bot.command()
async def about(ctx):
    await ctx.send("MinecraftServerStatusDisc - 0.0.1 - DopeMathers - ChatGPT")

@bot.command()
async def set_backup(ctx, *, time: str):
    global backup_time
    backup_time = time
    save_backup_time()
    await ctx.send(f"✅ Backup-Zeit aktualisiert: {backup_time}")

@bot.command()
async def set_update(ctx, time: str, link: str):
    global last_update_time, last_update_link
    last_update_time = time
    last_update_link = link
    save_update_time()
    await ctx.send(f"✅ Update-Zeit aktualisiert: {last_update_time}\n🔗 {last_update_link}")

@bot.command()
async def toggle_maintenance(ctx):
    global maintenance_mode
    maintenance_mode = not maintenance_mode
    await ctx.send("🔧 Wartungsmodus aktiviert!" if maintenance_mode else "✅ Wartungsmodus deaktiviert!")

@bot.command()
async def help_mcs(ctx):
    help_message = """
    **📜 Verfügbare Befehle:**
    
    🔹 **!server_status** – Zeigt den aktuellen Status des Minecraft-Servers an.
    🔹 **!player_online** – Zeigt an, wie viele Spieler online sind.
    🔹 **!bot_status** – Prüft, ob der Bot läuft.
    🔹 **!backup** – Zeigt das letzte Backup-Datum.
    🔹 **!update** – Zeigt das letzte Update-Datum und den Link.
    🔹 **!about** – Zeigt Informationen über diesen Bot.
    
    """
    await ctx.send(help_message)

# ----------------- Bot Starten -----------------
bot.run(TOKEN)