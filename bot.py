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
    "behe": {"name": "Behemoth", "min": 4*60*60, "max": 4*60*60, "image": "https://cdn.ares.reforgix.com/strapi/medium_behe_32ab46b655.png"},
    "manti": {"name": "Manticore", "min": 25*60*60, "max": 25*60*60, "image": "https://cdn.ares.reforgix.com/strapi/small_Manticore_enhanced_26c4679ff1.png"},
    "ogre": {"name": "Ogre Master", "min": 25*60*60, "max": 25*60*60, "image": "https://cdn.ares.reforgix.com/strapi/medium_OM_2c4fd15921.png"},
    "bd": {"name": "Bone Drake", "min": 25*60*60, "max": 25*60*60, "image": "https://cdn.ares.reforgix.com/strapi/large_Bone_Drake_Enhanced_7c3fa99afa.png"},
    "bapho": {"name": "Baphomet", "min": 25*60*60, "max": 25*60*60, "image": "https://cdn.ares.reforgix.com/strapi/large_Baphomet_Enhanced_c9fbac3c9e.png"},
    "od": {"name": "Ocean Dragon", "min": 25*60*60, "max": 25*60*60, "image": "https://cdn.ares.reforgix.com/strapi/large_OD_Enhanced_1603fd7734.png"},
    "ds": {"name": "Demon Servant", "min": 25*60*60, "max": 25*60*60, "image": "https://cdn.ares.reforgix.com/strapi/small_ds_side_8207186008.png"},

    # 26 hour bosses
    "eragon": {"name": "Eragon", "min": 26*60*60, "max": 26*60*60, "image": "https://cdn.ares.reforgix.com/strapi/large_Eragon_Enhanced_d643b8781e.png"},
    "mm": {"name": "Minotaur Master", "min": 26*60*60, "max": 26*60*60, "image": "https://cdn.ares.reforgix.com/strapi/small_mino_8a7d50b220.png"},

    # 14 hour fixed
    "caveman": {"name": "Underwater Caveman", "min": 14*60*60, "max": 14*60*60, "image": "https://cdn.ares.reforgix.com/strapi/large_Caveman_Enhanced_444659f071.png"},
    "mandragora": {"name": "Mandragora", "min": 14*60*60, "max": 14*60*60, "image": "https://cdn.ares.reforgix.com/strapi/large_Mandragora_Enhanced_85f92fe9dc.png"},

    # 14–16 window bosses (SAFE at 14h)
    "mantrap": {"name": "Mantrap Plant", "min": 14*60*60, "max": 16*60*60, "image": "https://cdn.ares.reforgix.com/strapi/large_Mantrap_Plant_Enhanced_cd2343cf53.png"},
    "beelzebub": {"name": "Beelzebub", "min": 14*60*60, "max": 16*60*60, "image": "https://cdn.ares.reforgix.com/strapi/large_Beezlebub_Enhanced_68ef8a2ef2.png"},
    "minotaur": {"name": "Minotaur", "min": 14*60*60, "max": 16*60*60, "image": "https://cdn.ares.reforgix.com/strapi/small_mino_8a7d50b220.png"},
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
# TIMER TASK WITH WINDOW TRACKING
# ======================
async def run_timer(channel, boss_key, data):
    boss = BOSSES[boss_key]
    start_time = data["start"]
    end_time = data["max_end"]

    embed = discord.Embed(
        title=f"{boss['name']} Killed!",
        description="Calculating next spawn...",
        color=0xff0000
    )
    if boss.get("image"):
        embed.set_image(url=boss["image"])

    msg = await channel.send(embed=embed)

    min_alert_sent = False
    mid_alert_sent = False

    while True:
        now = time.time()
        remaining_seconds = int(end_time - now)

        if remaining_seconds <= 0:
            break

        elapsed = now - start_time

        # SPAWN WINDOW OPEN
        if not min_alert_sent and elapsed >= boss["min"]:
            await channel.send(f"🔥 **{boss['name']} SPAWN WINDOW OPEN!**")
            min_alert_sent = True

        # MID WINDOW ALERT (only for window bosses)
        if boss["max"] != boss["min"]:
            mid_point = (boss["min"] + boss["max"]) / 2
            if not mid_alert_sent and elapsed >= mid_point:
                await channel.send(f"⚠ **{boss['name']} mid spawn window reached!**")
                mid_alert_sent = True

        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        embed.description = f"Spawn window closes in **{hours}h {minutes}m**"
        await msg.edit(embed=embed)

        await asyncio.sleep(60)

    finished_embed = discord.Embed(
        title=f"{boss['name']} FINAL WINDOW!",
        description=PING_ROLE,
        color=0x00ff00
    )
    if boss.get("image"):
        finished_embed.set_image(url=boss["image"])

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
            for boss_key, data in timers.items():
                client.loop.create_task(run_timer(output_channel, boss_key, data))

# ======================
# MESSAGE HANDLER
# ======================
@client.event
async def on_message(message):
    if message.author.bot:
        return

    # ===== RESET =====
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
            await output_channel.send(f"🔄 **{BOSSES[boss_key]['name']} timer reset.**")
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

    # BLOCK REPOST
    if key in timers:
        try:
            await message.delete()
        except:
            pass
        await message.channel.send(f"⏳ **{BOSSES[key]['name']} timer already running!**")
        return

    now = time.time()

    timers[key] = {
        "start": now,
        "min_end": now + BOSSES[key]["min"],
        "max_end": now + BOSSES[key]["max"]
    }

    save_timers(timers)

    client.loop.create_task(run_timer(output_channel, key, timers[key]))

# ======================
# START
# ======================
client.run(TOKEN)