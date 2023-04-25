import discord
import asyncio
from datetime import datetime
intents = discord.Intents.all()
intents.members = True
from discord.ext import commands

client = commands.Bot(command_prefix='!', intents=intents)

# Replace with your own token
TOKEN = 'MTA2NzQ4NjUzNjQwNjQwOTI2Nw.GEzaVB.gJDyB-UUDwGkEye-dqyN6Z06aPQmXdtB3YLK64'

# Replace with the file path of your sound file
SOUND_FILE = 'D:\EXTERMINATION\meow.mp3'

# Replace with the IDs of your admin users
ADMINS = [515648621669122157]

is_stopped = False


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

# Function to play sound file at specific intervals
async def play_sound():
    global is_stopped
    await client.wait_until_ready()
    while not client.is_closed():
        if is_stopped:
            await asyncio.sleep(1)
            continue
        now = datetime.now()
        if now.minute == 0 or now.minute == 14 or now.minute == 44 or now.minute == 59:
            vc = client.voice_clients[0]
            source = discord.FFmpegPCMAudio(SOUND_FILE)
            vc.play(source, after=lambda e: print('Error:', e) if e else None)
        await asyncio.sleep(60)
@client.event
async def on_message(message):
    global is_stopped
    if message.author.id in ADMINS:
        if message.content.startswith('!join'):
            channel = message.author.voice.channel
            vc = await channel.connect()
            asyncio.ensure_future(play_sound())
        elif message.content.startswith('!leave'):
            vc = client.voice_clients[0]
            await vc.disconnect()
        elif message.content.startswith('!stop'):
            is_stopped = True
        elif message.content.startswith('!start'):
            is_stopped = False

client.run('MTA2NzQ4NjUzNjQwNjQwOTI2Nw.GEzaVB.gJDyB-UUDwGkEye-dqyN6Z06aPQmXdtB3YLK64')