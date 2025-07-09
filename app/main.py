import discord
from discord import app_commands
from discord.ui import View, Button
import os
import dotenv
import random
import google.generativeai as genai
import itertools
import asyncio

from server import server_thread

dotenv.load_dotenv()

TOKEN = os.environ.get("TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True


# 環境変数からAPIキーを取得
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# 使用するモデルを指定
model = genai.GenerativeModel('gemini-pro') 

GUILD_ID = 1127013631763169301  # テスト用サーバーIDに置き換えてください（任意）

# --- Poker Game Implementation ---

# Dictionary to store poker games per channel
poker_games = {}

# Card definitions
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

def get_poker_hand_rank(hand):
    # hand is a list of 5 cards, where each card is a tuple (rank, suit)
    ranks = sorted([card[0] for card in hand], key=lambda r: '23456789TJQKA'.index(r), reverse=True)
    suits = [card[1] for card in hand]
    rank_counts = {r: ranks.count(r) for r in ranks}
    is_flush = len(set(suits)) == 1
    
    # Check for straight
    unique_ranks = sorted(list(set(ranks)), key=lambda r: '23456789TJQKA'.index(r))
    is_straight = False
    if len(unique_ranks) == 5:
        # Ace-high straight
        if '23456789TJQKA'.find(''.join(unique_ranks)) != -1:
            is_straight = True
        # Ace-low straight (A, 2, 3, 4, 5)
        elif set(unique_ranks) == {'A', '2', '3', '4', '5'}:
            is_straight = True
            ranks = ['5', '4', '3', '2', 'A'] # Reorder for correct display

    # Hand ranking logic
    if is_straight and is_flush:
        if set(ranks) == {'A', 'K', 'Q', 'J', 'T'}:
            return "ロイヤルフラッシュ", ranks
        return "ストレートフラッシュ", ranks
    if 4 in rank_counts.values():
        four_kind_rank = [r for r, c in rank_counts.items() if c == 4][0]
        other_cards = sorted([r for r in ranks if r != four_kind_rank], key=lambda r: '23456789TJQKA'.index(r), reverse=True)
        return "フォーカード", [four_kind_rank] * 4 + other_cards
    if sorted(rank_counts.values()) == [2, 3]:
        three_kind_rank = [r for r, c in rank_counts.items() if c == 3][0]
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        return "フルハウス", [three_kind_rank] * 3 + [pair_rank] * 2
    if is_flush:
        return "フラッシュ", ranks
    if is_straight:
        return "ストレート", ranks
    if 3 in rank_counts.values():
        three_kind_rank = [r for r, c in rank_counts.items() if c == 3][0]
        other_cards = sorted([r for r in ranks if r != three_kind_rank], key=lambda r: '23456789TJQKA'.index(r), reverse=True)
        return "スリーカード", [three_kind_rank] * 3 + other_cards
    if list(rank_counts.values()).count(2) == 2:
        pairs = [r for r, c in rank_counts.items() if c == 2]
        pairs.sort(key=lambda r: '23456789TJQKA'.index(r), reverse=True)
        other_card = [r for r, c in rank_counts.items() if c == 1][0]
        return "ツーペア", [pairs[0]]*2 + [pairs[1]]*2 + [other_card]
    if 2 in rank_counts.values():
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        other_cards = sorted([r for r in ranks if r != pair_rank], key=lambda r: '23456789TJQKA'.index(r), reverse=True)
        return "ワンペア", [pair_rank] * 2 + other_cards
    
    return "ハイカード", ranks

def get_best_hand(seven_cards):
    best_rank_name = "ハイカード"
    best_hand_cards = []
    best_rank_score = -1
    
    hand_ranks_order = {
        "ロイヤルフラッシュ": 9, "ストレートフラッシュ": 8, "フォーカード": 7,
        "フルハウス": 6, "フラッシュ": 5, "ストレート": 4,
        "スリーカード": 3, "ツーペア": 2, "ワンペア": 1, "ハイカード": 0
    }

    for hand_combination in itertools.combinations(seven_cards, 5):
        rank_name, hand_cards = get_poker_hand_rank(list(hand_combination))
        rank_score = hand_ranks_order[rank_name]

        if rank_score > best_rank_score:
            best_rank_score = rank_score
            best_rank_name = rank_name
            best_hand_cards = hand_cards
        elif rank_score == best_rank_score:
            # Compare kickers if ranks are the same
            current_best_values = ['23456789TJQKA'.index(r) for r in best_hand_cards]
            new_hand_values = ['23456789TJQKA'.index(r) for r in hand_cards]
            if new_hand_values > current_best_values:
                best_hand_cards = hand_cards

    return best_rank_name, best_hand_cards

class PokerGame:
    def __init__(self, interaction: discord.Interaction):
        self.guild = interaction.guild
        self.channel = interaction.channel
        self.starter = interaction.user
        self.players = []
        self.deck = []
        self.community_cards = []
        self.player_hands = {}
        self.game_active = False

    def add_player(self, user: discord.User):
        if user not in self.players:
            self.players.append(user)
            return True
        return False

    def start_game(self):
        if len(self.players) < 2:
            return False, "プレイヤーが2人未満です。"
        self.game_active = True
        self.deck = list(itertools.product(RANKS, SUITS))
        random.shuffle(self.deck)
        self.deal_cards()
        return True, "ゲームを開始しました。"

    def deal_cards(self):
        for player in self.players:
            self.player_hands[player.id] = [self.deck.pop(), self.deck.pop()]
        self.community_cards = [self.deck.pop() for _ in range(5)]

class PokerJoinView(View):
    def __init__(self, game: PokerGame):
        super().__init__(timeout=300) # 5 minutes to join
        self.game = game

    @discord.ui.button(label="参加する", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: Button):
        if self.game.add_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} がゲームに参加しました。", ephemeral=True)
            
            # Update the list of players in the main message
            player_list = "\n".join([p.mention for p in self.game.players])
            embed = interaction.message.embeds[0]
            embed.set_field_at(0, name="参加者", value=player_list, inline=False)
            await interaction.message.edit(embed=embed)
        else:
            await interaction.response.send_message("既に参加しています。", ephemeral=True)

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

client = MyClient()
poker_group = app_commands.Group(name="poker", description="ポーカーゲームを管理します。")

@poker_group.command(name="start", description="ポーカーゲームを開始します。")
async def poker_start(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id in poker_games:
        await interaction.response.send_message("このチャンネルでは既にゲームが進行中です。")
        return

    game = PokerGame(interaction)
    poker_games[channel_id] = game
    game.add_player(interaction.user)

    view = PokerJoinView(game)
    
    embed = discord.Embed(title="ポーカーゲーム募集中！", description=f"{interaction.user.mention} がゲームを開始しました。\n`/poker deal` でゲームをスタートします。", color=discord.Color.blue())
    embed.add_field(name="参加者", value=interaction.user.mention, inline=False)
    
    await interaction.response.send_message(embed=embed, view=view)

@poker_group.command(name="deal", description="カードを配り、ゲームを開始します。")
async def poker_deal(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id not in poker_games:
        await interaction.response.send_message("このチャンネルではゲームが開始されていません。")
        return

    game = poker_games[channel_id]
    if interaction.user != game.starter:
        await interaction.response.send_message("ゲームの開始者のみがディールできます。", ephemeral=True)
        return
    
    if len(game.players) < 2:
        await interaction.response.send_message("プレイヤーが2人未満です。ゲームを開始できません。", ephemeral=True)
        return

    game.start_game()

    # Send hands to players via DM
    for player in game.players:
        hand_str = ' '.join([f"{r}{s}" for r, s in game.player_hands[player.id]])
        try:
            await player.send(f"あなたの手札: **{hand_str}**")
        except discord.Forbidden:
            await interaction.channel.send(f"{player.mention} にDMを送信できませんでした。DMの受信を許可してください。")

    # Determine winner
    results = []
    for player in game.players:
        player_hand = game.player_hands[player.id]
        all_cards = player_hand + game.community_cards
        best_rank, best_cards = get_best_hand(all_cards)
        results.append((player, best_rank, best_cards))

    # Sort results to find the winner
    hand_ranks_order = {
        "ロイヤルフラッシュ": 9, "ストレートフラッシュ": 8, "フォーカード": 7,
        "フルハウス": 6, "フラッシュ": 5, "ストレート": 4,
        "スリーカード": 3, "ツーペア": 2, "ワンペア": 1, "ハイカード": 0
    }
    
    def get_sort_key(result):
        player, rank, cards = result
        rank_score = hand_ranks_order[rank]
        card_values = ['23456789TJQKA'.index(r) for r in cards]
        return (rank_score, card_values)

    results.sort(key=get_sort_key, reverse=True)
    
    winner, winner_rank, winner_cards = results[0]

    # Display results in the channel
    community_cards_str = ' '.join([f"{r}{s}" for r, s in game.community_cards])
    
    embed = discord.Embed(title="ポーカー結果", color=discord.Color.gold())
    embed.add_field(name="場のカード", value=f"**{community_cards_str}**", inline=False)

    result_text = ""
    for player, rank, cards in results:
        hand_str = ' '.join([f"{r}{s}" for r, s in game.player_hands[player.id]])
        result_text += f"{player.mention}: {rank} ({hand_str})\n"
    
    embed.add_field(name="各プレイヤーの手札と役", value=result_text, inline=False)
    
    winner_hand_str = ' '.join([f"{r}{s}" for r, s in game.player_hands[winner.id]])
    embed.add_field(name="勝者", value=f"**{winner.mention}** が **{winner_rank}** で勝利！\n(手札: {winner_hand_str})", inline=False)

    await interaction.response.send_message(embed=embed)
    
    # Clean up the game
    del poker_games[channel_id]

@poker_group.command(name="end", description="現在のポーカーゲームを終了します。")
async def poker_end(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id in poker_games:
        game = poker_games[channel_id]
        # Allow starter or user with manage_channels permission to end the game
        if interaction.user == game.starter or interaction.user.guild_permissions.manage_channels:
            del poker_games[channel_id]
            await interaction.response.send_message("ゲームを終了しました。")
        else:
            await interaction.response.send_message("ゲームの開始者または管理者のみがゲームを終了できます。", ephemeral=True)
    else:
        await interaction.response.send_message("このチャンネルではゲームが開始されていません。")

client.tree.add_command(poker_group)

@client.event
async def on_ready():
    print(f'{client.user} がログインしました')
    new_activity = discord.Game("レポート") 
    await client.change_presence(activity=new_activity)
    await client.tree.sync()
    print("スラッシュコマンドを同期しました")

@client.event
async def on_message(message):
    if "宇佐美" in message.content.lower():
        await message.add_reaction("<:usami:1159384863309316146>")
    if "レポート" in message.content.lower():
        await message.add_reaction("<:report:1140109232738414692>")
    if "よぴぴ丸" in message.content.lower():
        await message.add_reaction("<:ero:1192928073495105636>")
    if "あります" in message.content.lower():
        await message.channel.send("ねぇよ")

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
        await interaction.response.send_message(f"{random_number}%完成しました!")

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
async def gemini(interaction: discord.Interaction, message: str):
    await interaction.response.defer()
    try:
        response = model.generate_content(message)
        if not response.candidates or not response.candidates[0].content.parts:
            await interaction.followup.send("内容が生成されませんでした。もう少し詳しく聞いてください。")
        else:
            await interaction.followup.send(response.text[:2000])
    except Exception as e:
        await interaction.followup.send(f"エラーが発生しました: {e}")

server_thread()
client.run(TOKEN)
