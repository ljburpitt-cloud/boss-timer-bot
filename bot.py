import discord
import asyncio
import json
import time
import os

TOKEN = os.getenv("TOKEN")

INPUT_CHANNEL = "boss-input"
OUTPUT_CHANNEL = "boss-timers"
PING_ROLE = "@BossTeam"
DATA_FILE = "timers.json"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ======================
# BOSS CONFIG
# ======================
BOSSES = {
    "behe": {
        "name": "Behemoth",
        "cooldown": 4 * 60 * 60,
        "image": "https://discord.com/channels/677548971073339409/1476331499082088649/1476331565259821087"
    },
    "manti": {
        "name": "Manticore",
        "cooldown": 26 * 60 * 60,
        "image": "IMAGE_URL_HERE"
    },
    "ogre": {
        "name": "Ogre Master",
        "cooldown": 26 * 60 * 60,
        "image": "IMAGE_URL_HERE"
    },
    "bd": {
        "name": "Bone Drake",
        "cooldown": 26 * 60 * 60,
        "image": "IMAGE_URL_HERE"
    },
    "bapho": {
        "name": "Baphomet",
        "cooldown": 26 * 60 * 60,
        "image": "IMAGE_URL_HERE"
    },
    "od": {
        "name": "Ocean Dragon",
        "cooldown": 26 * 60 * 60,
        "image": "IMAGE_URL_HERE"
    },
    "ds": {
        "name": "Demon Servant",
        "cooldown": 26 * 60 * 60,
        "image": "IMAGE_URL_HERE"
    },
}

# ======================
# SAVE / LOAD
# ======================
def load_timers():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_timers(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

timers = load_timers()

# ======================
# TIMER TASK
# ======================
async def run_timer(channel, boss_key, end_time):
    remaining = end_time - time.time()
    if remaining > 0:
        await asyncio.sleep(remaining)

    embed = discord.Embed(
        title=f"{BOSSES[boss_key]['name']} is READY!",
        description=PING_ROLE,
        color=0x00ff00
    )
    embed.set_image(url=BOSSES[boss_key]["image"])

    await channel.send(embed=embed)

    timers.pop(boss_key, None)
    save_timers(timers)

# ======================
# READY
# ======================
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    for guild in client.guilds:
        output_channel = discord.utils.get(
            guild.text_channels, name=OUTPUT_CHANNEL
        )
        if output_channel:
            for boss_key, end_time in timers.items():
                client.loop.create_task(
                    run_timer(output_channel, boss_key, end_time)
                )

# ======================
# MESSAGE HANDLER
# ======================
@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.name != INPUT_CHANNEL:
        return

    key = message.content.lower()

    if key not in BOSSES:
        return

    output_channel = discord.utils.get(
        message.guild.text_channels, name=OUTPUT_CHANNEL
    )
    if not output_channel:
        return

    if key in timers:
        remaining = int((timers[key] - time.time()) / 60)
        await output_channel.send(
            f"⏳ **{BOSSES[key]['name']} timer already running** "
            f"({remaining} minutes left)"
        )
        return

    end_time = time.time() + BOSSES[key]["cooldown"]
    timers[key] = end_time
    save_timers(timers)

    hours = BOSSES[key]["cooldown"] // 3600

    embed = discord.Embed(
        title=f"{BOSSES[key]['name']} Killed!",
        description=f"Next spawn in **{hours} hours**.",
        color=0xff0000
    )
    embed.set_image(url=BOSSES[key]["image"])

    await output_channel.send(embed=embed)

    client.loop.create_task(
        run_timer(output_channel, key, end_time)
    )

client.run(TOKEN)