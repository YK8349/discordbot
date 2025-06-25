import discord
from discord import app_commands
import os
import dotenv
import random

from server import server_thread

dotenv.load_dotenv()

TOKEN = os.environ.get("TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = discord.Client(intents=intents)

GUILD_ID = 123456789012345678  # テスト用サーバーIDに置き換えてください（任意）

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # テストサーバーにコマンドを登録（すぐ反映される）
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

client = MyClient()

# bot起動時
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print(f'{client.user} がログインしました')

    # アクティビティを設定 
    new_activity = discord.Game("レポート") 
    await client.change_presence(activity=new_activity)

    # スラッシュコマンドを同期 
    # グローバルコマンドの同期を行う
    await client.tree.sync()
    print("スラッシュコマンドを同期しました")

# スラッシュコマンドの登録
@client.tree.command(name="ping", description="pingpong")
async def ping(ctx):
    await ctx.send(content="pong!")

@client.event
async def on_message(message):
    # if message.author.bot:
    #     return
    if "宇佐美" in message.content.lower():
        await message.add_reaction("<:usami:1159384863309316146>")
    if "レポート" in message.content.lower():
        await message.add_reaction("<:report:1140109232738414692>")
    if "よぴぴ丸" in message.content.lower():
        await message.add_reaction("<:ero:1192928073495105636>")
    if message.content == "あります" :
        await message.channel.send("ねぇよ")

# スラッシュコマンドの定義
@client.tree.command(name='ping', description='pingを返します')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong")

@client.tree.command(name='progress', description='進捗を返します')
async def ping(interaction: discord.Interaction):
    random_number = random.randint(0, 100)
    if(random_number==0):
        await interaction.response.send_message("完成しませんでした...")
    elif(random_number==100):
        await interaction.response.send_message("提出しました!")
    else:
        await interaction.response.send_message("{}%完成しました!".format(random_number))

@client.tree.command(name='usami', description='宇佐美を返します')
async def ping(interaction: discord.Interaction):
    random_number = random.randint(0, 2)
    if(random_number==0):
        await interaction.response.send_message("<:usami:1159384863309316146>")
    if(random_number==1):
        await interaction.response.send_message(" <:usami_karishin:1165885355065606154>")
    if(random_number==2):
        await interaction.response.send_message(" <:usami_using_pc:1174190208808390758>")


# Botの起動
# Koyeb用 サーバー立ち上げ
server_thread()
client.run(TOKEN)
