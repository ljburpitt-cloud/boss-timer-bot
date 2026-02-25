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
    "behe": {"name": "Behemoth", "cooldown": 4*60*60, "image": "https://cdn.ares.reforgix.com/strapi/medium_behe_32ab46b655.png"},
    "manti": {"name": "Manticore", "cooldown": 26*60*60, "image": "https://cdn.ares.reforgix.com/strapi/small_Manticore_enhanced_26c4679ff1.png"},
    "ogre": {"name": "Ogre Master", "cooldown": 26*60*60, "image": "https://cdn.ares.reforgix.com/strapi/medium_OM_2c4fd15921.png"},
    "bd": {"name": "Bone Drake", "cooldown": 26*60*60, "image": "https://cdn.ares.reforgix.com/strapi/large_Bone_Drake_Enhanced_7c3fa99afa.png"},
    "bapho": {"name": "Baphomet", "cooldown": 26*60*60, "image": "https://cdn.ares.reforgix.com/strapi/large_Baphomet_Enhanced_c9fbac3c9e.png"},
    "od": {"name": "Ocean Dragon", "cooldown": 26*60*60, "image": "https://cdn.ares.reforgix.com/strapi/large_OD_Enhanced_1603fd7734.png"},
    "ds": {"name": "Demon Servant", "cooldown": 26*60*60, "image": "https://cdn.ares.reforgix.com/strapi/small_ds_side_8207186008.png"},
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
# TIMER TASK WITH LIVE COUNTDOWN
# ======================
async def run_timer(channel, boss_key, end_time):
    embed = discord.Embed(
        title=f"{BOSSES[boss_key]['name']} Killed!",
        description="Calculating next spawn...",
        color=0xff0000
    )
    if BOSSES[boss_key].get("image"):
        embed.set_image(url=BOSSES[boss_key]["image"])

    msg = await channel.send(embed=embed)

    while True:
        remaining_seconds = int(end_time - time.time())
        if remaining_seconds <= 0:
            break

        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        embed.description = f"Next spawn in **{hours}h {minutes}m**"
        await msg.edit(embed=embed)

        await asyncio.sleep(60)

    finished_embed = discord.Embed(
        title=f"{BOSSES[boss_key]['name']} is READY!",
        description=PING_ROLE,
        color=0x00ff00
    )
    if BOSSES[boss_key].get("image"):
        finished_embed.set_image(url=BOSSES[boss_key]["image"])

    await msg.edit(embed=finished_embed)
    timers.pop(boss_key, None)
    save_timers(timers)

# ======================
# READY
# ======================
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    for guild in client.guilds:
        output_channel = discord.utils.get(guild.text_channels, name=OUTPUT_CHANNEL)
        if output_channel:
            for boss_key, end_time in timers.items():
                client.loop.create_task(run_timer(output_channel, boss_key, end_time))

# ======================
# MESSAGE HANDLER
# ======================
@client.event
async def on_message(message):
    if message.author.bot:
        return

    # ===== RESET COMMAND =====
    if message.content.lower().startswith("!reset"):
        if message.author.id != message.guild.owner_id:
            await message.channel.send("❌ Only the server owner can reset timers.")
            return

        parts = message.content.lower().split()
        if len(parts) != 2:
            await message.channel.send("⚠ Usage: !reset <boss>")
            return

        boss_key = parts[1]
        if boss_key not in timers:
            await message.channel.send(f"⏹ No active timer for {boss_key}.")
            return

        timers.pop(boss_key)
        save_timers(timers)

        output_channel = discord.utils.get(message.guild.text_channels, name=OUTPUT_CHANNEL)
        if output_channel:
            await output_channel.send(f"🔄 **{BOSSES[boss_key]['name']} timer has been reset by the owner.**")
        return

    # ===== BOSS INPUT =====
    if message.channel.name != INPUT_CHANNEL:
        return

    key = message.content.lower()
    if key not in BOSSES:
        return

    output_channel = discord.utils.get(message.guild.text_channels, name=OUTPUT_CHANNEL)
    if not output_channel:
        return

    # ===== BLOCK REPOST IF TIMER ACTIVE =====
    if key in timers:
        # Delete user message to prevent reposting
        try:
            await message.delete()
        except discord.Forbidden:
            pass  # If bot can't delete messages, ignore

        remaining_seconds = int(timers[key] - time.time())
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60

        # Notify output channel
        await output_channel.send(
            f"⏳ **{BOSSES[key]['name']} timer already running** ({hours}h {minutes}m remaining)"
        )
        return

    # Timer not active, start it
    end_time = time.time() + BOSSES[key]["cooldown"]
    timers[key] = end_time
    save_timers(timers)

    client.loop.create_task(run_timer(output_channel, key, end_time))

# ======================
# START BOT
# ======================
client.run(TOKEN)