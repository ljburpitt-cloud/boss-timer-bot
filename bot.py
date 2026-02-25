import discord
import asyncio
import json
import time
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_NAME = "bosses"
PING_ROLE = "@BossTeam"
DATA_FILE = "timers.json"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

BOSSES = {
    "behe": {"name": "Behemoth", "cooldown": 4 * 60 * 60},
    "manti": {"name": "Manticore", "cooldown": 26 * 60 * 60},
    "ogre": {"name": "Ogre Master", "cooldown": 26 * 60 * 60},
    "bd": {"name": "Bone Drake", "cooldown": 26 * 60 * 60},
    "bapho": {"name": "Baphomet", "cooldown": 26 * 60 * 60},
    "od": {"name": "Ocean Dragon", "cooldown": 26 * 60 * 60},
    "ds": {"name": "Demon Servant", "cooldown": 26 * 60 * 60},
}

def load_timers():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_timers(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

timers = load_timers()

async def run_timer(channel, boss_key, end_time):
    remaining = end_time - time.time()
    if remaining > 0:
        await asyncio.sleep(remaining)

    await channel.send(
        f"🔥 **{BOSSES[boss_key]['name']} is ready to spawn!** {PING_ROLE}"
    )

    timers.pop(boss_key, None)
    save_timers(timers)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name == CHANNEL_NAME:
                for boss_key, end_time in timers.items():
                    client.loop.create_task(
                        run_timer(channel, boss_key, end_time)
                    )

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.name != CHANNEL_NAME:
        return

    key = message.content.lower()

    if key in BOSSES:
        if key in timers:
            remaining = int((timers[key] - time.time()) / 60)
            await message.channel.send(
                f"⏳ **{BOSSES[key]['name']} timer already running** "
                f"({remaining} minutes left)"
            )
            return

        end_time = time.time() + BOSSES[key]["cooldown"]
        timers[key] = end_time
        save_timers(timers)

        hours = BOSSES[key]["cooldown"] // 3600

        await message.channel.send(
            f"🕒 **{BOSSES[key]['name']} killed!**\n"
            f"Next spawn in **{hours} hours**."
        )

        client.loop.create_task(
            run_timer(message.channel, key, end_time)
        )

client.run(TOKEN)