import discord
import os
from os.path import join, dirname
from dotenv import load_dotenv

from keep_alive import keep_alive

client = discord.Client(intents=discord.Intents.default())

load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

@client.event
async def on_ready():
    print('ログインしました')

keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    client.run(TOKEN)
else:
    print("Tokenが見つかりませんでした")
