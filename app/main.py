import discord
from discord import app_commands
import os
import dotenv
import random
import google.generativeai as genai

from server import server_thread

dotenv.load_dotenv()

TOKEN = os.environ.get("TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = discord.Client(intents=intents)

# 環境変数からAPIキーを取得
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-Flash') # 使用するモデルを指定

GUILD_ID = 1127013631763169301  # テスト用サーバーIDに置き換えてください（任意）

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
    if "あります" in message.content.lower():
        await message.channel.send("ねぇよ")

# スラッシュコマンドの定義
@client.tree.command(name='ping', description='pingを返します')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong")

@client.tree.command(name='progress', description='進捗を返します')
async def progress(interaction: discord.Interaction):
    random_number = random.randint(0, 100)
    if(random_number==0):
        await interaction.response.send_message("完成しませんでした...")
    elif(random_number==100):
        await interaction.response.send_message("提出しました!")
    else:
        await interaction.response.send_message("{}%完成しました!".format(random_number))

@client.tree.command(name='usami', description='宇佐美を返します')
async def usami(interaction: discord.Interaction):
    random_number = random.randint(0, 2)
    if(random_number==0):
        await interaction.response.send_message("<:usami:1159384863309316146>")
    if(random_number==1):
        await interaction.response.send_message(" <:usami_karishin:1165885355065606154>")
    if(random_number==2):
        await interaction.response.send_message(" <:usami_using_pc:1174190208808390758>")

@client.tree.command(name='meigen', description='waon鯖名言集')
async def meigen(interaction: discord.Interaction):
    random_number = random.randint(0, 18)
    if(random_number==0):
        await interaction.response.send_message("yomo「エロいショタの方が1000倍見たい」- 2025/02/03 1:21")
    if(random_number==1):
        await interaction.response.send_message("あいかぎ「いじめはみじめ、いじめだけに（笑）<:aoki_thinking:1309010344382955560>」- 2025/01/27 18:06")
    if(random_number==2):
        await interaction.response.send_message("なりょ「わたしはオタクではありませんし、高専なんて知りませんでした」- 2023/09/09 14:49")
    if(random_number==3):
        await interaction.response.send_message("なりょ「レッツ強盗」- 2023/09/07 9:28")
    if(random_number==4):
        await interaction.response.send_message("なりょ「物理的に、ね？」- 2025/02/17 13:26")
    if(random_number==5):
        await interaction.response.send_message("澤「北陸信用ちんこ」- 2025/06/11 20:46")
    if(random_number==6):
        await interaction.response.send_message("澤「有線のイヤホンとかオタク以外持ってないだろ殺すぞ」- 2025/06/07 23:15")
    if(random_number==7):
        await interaction.response.send_message("あいかぎ「omeja」- 2025/01/08 14:56")
    if(random_number==8):
        await interaction.response.send_message("yomoがトピックを オナ二一 に設定")
    if(random_number==9):
        await interaction.response.send_message("澤「と言うかモラ」- 2024/09/24 15:07")
    if(random_number==10):
        await interaction.response.send_message("松木「まーんwwwwまーんwww！（マン語でしか話せなくなり嘆いている）」- 2025/06/19 18:35")
    if(random_number==11):
        await interaction.response.send_message("松木「あいか氣゛」- 2025/06/18 12:12")
    if(random_number==12):
        await interaction.response.send_message("山口「あいかぎってゲイなの?」- 2025/06/02 9:33")
    if(random_number==13):
        await interaction.response.send_message("松木「よものちんちん「ﾌﾞﾛﾛﾛﾛﾛﾛﾛﾛﾛwwwwwwwwww！！！！！」」- 2025/05/25 0:40")
    if(random_number==14):
        await interaction.response.send_message("吉岡「プロ棋士に俺はなる」- 2025/05/21 17:54")
    if(random_number==15):
        await interaction.response.send_message("山口伝説tier　～～殿堂入り～～　教室を下着姿で徘徊")
    if(random_number==16):
        await interaction.response.send_message("山口伝説tier　tier1：面接途中にペンを置かれる，「この能無し野郎」，「転学科しないでください」")
    if(random_number==17):
        await interaction.response.send_message("山口伝説tier　tier2：鼻血")
    if(random_number==18):
        await interaction.response.send_message("山口「電情落として、成績落として、バイト落としてあと落とすの命だけでガチ鬱」- 2025/04/17 16:22")
    
@client.tree.command(name='gemini', description='API使いすぎたら殺す(無料枠分使い果たすなカスども)')
@app_commands.describe(message="プロンプト")
async def gemini(interaction: discord.Interaction,message: str):
    prompt = message
    try:
            response = model.generate_content(prompt)
            await interaction.response.send_message(response.text)
    except Exception as e:
            await interaction.response.send_message(f"エラーが発生しました: {e}")


# Botの起動
# Koyeb用 サーバー立ち上げ
server_thread()
client.run(TOKEN)
