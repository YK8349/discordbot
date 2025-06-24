import discord
import os
import random
from dotenv import load_dotenv
from os.path import join, dirname

# .envファイルの読み込み
load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# インテント設定
intents = discord.Intents.default()
intents.message_content = True

# PycordのBotクラス（スラッシュコマンドに対応）
bot = discord.Bot(intents=intents)

# 起動時処理
@bot.event
async def on_ready():
    print(f'{bot.user} がログインしました')
    new_activity = discord.Game("レポート")
    await bot.change_presence(activity=new_activity)
    await bot.sync_commands()  # スラッシュコマンド同期
    print("スラッシュコマンドを同期しました")

# メッセージリアクション処理
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if "宇佐美" in message.content.lower():
        await message.add_reaction("<:usami:1159384863309316146>")
    if "レポート" in message.content.lower():
        await message.add_reaction("<:report:1140109232738414692>")
    if "よぴぴ丸" in message.content.lower():
        await message.add_reaction("<:ero:1192928073495105636>")
    if message.content == "あります":
        await message.channel.send("ねぇよ")

# スラッシュコマンド定義
@bot.slash_command(name="ping", description="pingを返します")
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond("pong")

@bot.slash_command(name="progress", description="進捗を返します")
async def progress(ctx: discord.ApplicationContext):
    r = random.randint(0, 100)
    if r == 0:
        await ctx.respond("完成しませんでした...")
    elif r == 100:
        await ctx.respond("提出しました!")
    else:
        await ctx.respond(f"{r}%完成しました!")

@bot.slash_command(name="usami", description="宇佐美を返します")
async def usami(ctx: discord.ApplicationContext):
    r = random.randint(0, 2)
    if r == 0:
        await ctx.respond("<:usami:1159384863309316146>")
    elif r == 1:
        await ctx.respond("<:usami_karishin:1165885355065606154>")
    elif r == 2:
        await ctx.respond("<:usami_using_pc:1174190208808390758>")

# Botトークンで起動
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Tokenが見つかりませんでした")
