import discord
import os
from os.path import join, dirname
from dotenv import load_dotenv

from keep_alive import keep_alive

client = discord.Client(intents=discord.Intents.default())

load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

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
    

keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    client.run(TOKEN)
else:
    print("Tokenが見つかりませんでした")
