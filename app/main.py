import discord
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import os
import dotenv
import random
import google.generativeai as genai
import itertools
import asyncio
import math
import json

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
model = genai.GenerativeModel('gemini-2.5-flash') 

GUILD_ID = 1127013631763169301  # テスト用サーバーIDに置き換えてください（任意）

class MyClient(discord.Client):
    def __init__(self): super().__init__(intents=intents); self.tree = app_commands.CommandTree(self)
    async def setup_hook(self): guild = discord.Object(id=GUILD_ID); self.tree.copy_global_to(guild=guild); await self.tree.sync(guild=guild)

client = MyClient()

@client.event
async def on_ready():
    print(f'{client.user} がログインしました')
    new_activity = discord.Game("レポート") 
    await client.change_presence(activity=new_activity)
    await client.tree.sync()
    print("スラッシュコマンドを同期しました")

@client.event
async def on_message(message):
    if "宇佐美" in message.content.lower(): await message.add_reaction("<:usami:1159384863309316146>")
    if "レポート" in message.content.lower(): await message.add_reaction("<:report:1140109232738414692>")
    if "よぴぴ丸" in message.content.lower(): await message.add_reaction("<:ero:1192928073495105636>")
    if "あります" in message.content.lower(): await message.channel.send("ねぇよ")

@client.tree.command(name='ping', description='pingを返します')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong")

@client.tree.command(name='progress', description='進捗を返します')
async def progress(interaction: discord.Interaction):
    random_number = random.randint(0, 100)
    if(random_number==0): await interaction.response.send_message("完成しませんでした...")
    elif(random_number==100): await interaction.response.send_message("提出しました!")
    else: await interaction.response.send_message(f"{random_number}%完成しました!")

@client.tree.command(name='usami', description='宇佐美を返します')
async def usami(interaction: discord.Interaction):
    random_number = random.randint(0, 2)
    if(random_number==0): await interaction.response.send_message("<:usami:1159384863309316146>")
    if(random_number==1): await interaction.response.send_message(" <:usami_karishin:1165885355065606154>")
    if(random_number==2): await interaction.response.send_message(" <:usami_using_pc:1174190208808390758>")

@client.tree.command(name='meigen', description='waon鯖名言集')
async def meigen(interaction: discord.Interaction):
    random_number = random.randint(0, 18)
    if(random_number==0): await interaction.response.send_message("yomo「エロいショタの方が1000倍見たい」- 2025/02/03 1:21")
    if(random_number==1): await interaction.response.send_message("あいかぎ「いじめはみじめ、いじめだけに（笑）<:aoki_thinking:1309010344382955560>」- 2025/01/27 18:06")
    if(random_number==2): await interaction.response.send_message("なりょ「わたしはオタクではありませんし、高専なんて知りませんでした」- 2023/09/09 14:49")
    if(random_number==3): await interaction.response.send_message("なりょ「レッツ強盗」- 2023/09/07 9:28")
    if(random_number==4): await interaction.response.send_message("なりょ「物理的に、ね？」- 2025/02/17 13:26")
    if(random_number==5): await interaction.response.send_message("澤「北陸信用ちんこ」- 2025/06/11 20:46")
    if(random_number==6): await interaction.response.send_message("澤「有線のイヤホンとかオタク以外持ってないだろ殺すぞ」- 2025/06/07 23:15")
    if(random_number==7): await interaction.response.send_message("あいかぎ「omeja」- 2025/01/08 14:56")
    if(random_number==8): await interaction.response.send_message("yomoがトピックを オナ二一 に設定")
    if(random_number==9): await interaction.response.send_message("澤「と言うかモラ」- 2024/09/24 15:07")
    if(random_number==10): await interaction.response.send_message("松木「まーんwwwwまーんwww！（マン語でしか話せなくなり嘆いている）」- 2025/06/19 18:35")
    if(random_number==11): await interaction.response.send_message("松木「あいか氣゛」- 2025/06/18 12:12")
    if(random_number==12): await interaction.response.send_message("山口「あいかぎってゲイなの?」- 2025/06/02 9:33")
    if(random_number==13): await interaction.response.send_message("松木「よものちんちん「ﾌﾞﾛﾛﾛﾛﾛﾛﾛﾛﾛwwwwwwwwww！！！！！」」- 2025/05/25 0:40")
    if(random_number==14): await interaction.response.send_message("吉岡「プロ棋士に俺はなる」- 2025/05/21 17:54")
    if(random_number==15): await interaction.response.send_message("山口伝説tier　～～殿堂入り～～　教室を下着姿で徘徊")
    if(random_number==16): await interaction.response.send_message("山口伝説tier　tier1：面接途中にペンを置かれる，「この能無し野郎」，「転学科しないでください」")
    if(random_number==17): await interaction.response.send_message("山口伝説tier　tier2：鼻血")
    if(random_number==18): await interaction.response.send_message("山口「電情落として、成績落として、バイト落としてあと落とすの命だけでガチ鬱」- 2025/04/17 16:22")

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

# --- Poker Game Code ---

# Card and Deck constants
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.value = RANK_VALUES[rank]

    def __str__(self):
        return f"{self.suit}{self.rank}"

class Deck:
    def __init__(self):
        self.cards = [Card(s, r) for s in SUITS for r in RANKS]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        if len(self.cards) > 0:
            return self.cards.pop()
        return None

class Player:
    def __init__(self, user, chips=1000, is_cpu=False, is_gemini=False):
        self.user = user
        self.hand = []
        self.chips = chips
        self.bet = 0
        self.has_acted = False
        self.is_folded = False
        self.is_all_in = False
        self.is_cpu = is_cpu
        self.is_gemini = is_gemini

    @property
    def name(self):
        return self.user.display_name if not self.is_cpu else self.user.name


class PokerGame:
    def __init__(self, interaction, cpu_players=0, gemini_players=0):
        self.interaction = interaction
        self.players = []
        self.cpu_players_to_add = cpu_players
        self.gemini_players_to_add = gemini_players
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.current_player_index = 0
        self.game_stage = "pre-flop" # pre-flop, flop, turn, river, showdown
        self.game_in_progress = False
        self.small_blind_index = -1
        self.big_blind_index = -1
        self.small_blind_amount = 10
        self.big_blind_amount = 20
        self.game_message = None
        self.action_view = None
        self.is_betting_round_active = False

    def add_player(self, user, is_cpu=False, is_gemini=False):
        if not any(p.user.id == user.id for p in self.players):
            player = Player(user, is_cpu=is_cpu, is_gemini=is_gemini)
            self.players.append(player)
            return True
        return False

    async def start_game(self):
        if len(self.players) < 2:
            await self.interaction.channel.send("プレイヤーが2人未満のため、ゲームを開始できません。")
            poker_games.pop(self.interaction.channel.id, None)
            return

        self.game_in_progress = True
        self.small_blind_index = (self.small_blind_index + 1) % len(self.players)
        await self.start_round()

    async def start_round(self):
        self.game_in_progress = True
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.game_stage = "pre-flop"

        # Filter out players with 0 chips
        self.players = [p for p in self.players if p.chips > 0]
        if len(self.players) < 2:
            await self.interaction.channel.send("プレイ可能なプレイヤーが2人未満になりました。ゲームを終了します。")
            poker_games.pop(self.interaction.channel.id, None)
            return

        for player in self.players:
            player.hand = [self.deck.deal(), self.deck.deal()]
            player.bet = 0
            player.has_acted = False
            player.is_folded = False
            player.is_all_in = False

        self.small_blind_index = (self.small_blind_index + 1) % len(self.players)
        self.big_blind_index = (self.small_blind_index + 1) % len(self.players)

        # Blinds
        sb_player = self.players[self.small_blind_index]
        bb_player = self.players[self.big_blind_index]
        
        sb_player.bet = min(self.small_blind_amount, sb_player.chips)
        sb_player.chips -= sb_player.bet
        self.pot += sb_player.bet
        if sb_player.chips == 0: sb_player.is_all_in = True


        bb_player.bet = min(self.big_blind_amount, bb_player.chips)
        bb_player.chips -= bb_player.bet
        self.pot += bb_player.bet
        if bb_player.chips == 0: bb_player.is_all_in = True
        
        self.current_bet = self.big_blind_amount

        self.current_player_index = (self.big_blind_index + 1) % len(self.players)
        
        await self.send_hands()
        await self.start_betting_round()

    async def start_betting_round(self):
        if self.is_betting_round_active: return
        self.is_betting_round_active = True

        if self.game_stage != "pre-flop":
            self.current_player_index = (self.small_blind_index) % len(self.players)
            self.current_bet = 0
            for p in self.players:
                p.has_acted = False
                p.bet = 0
        
        await self.process_turn()

    async def process_turn(self):
        active_players_not_allin = [p for p in self.players if not p.is_folded and not p.is_all_in]
        if len(active_players_not_allin) <= 1:
            await self.end_betting_round()
            return

        # Check if round is over
        bets = [p.bet for p in self.players if not p.is_folded and not p.is_all_in]
        acted = [p for p in self.players if not p.is_folded and not p.is_all_in and p.has_acted]
        if len(acted) == len(active_players_not_allin) and len(set(bets)) <= 1:
            await self.end_betting_round()
            return

        current_player = self.players[self.current_player_index]
        if current_player.is_folded or current_player.is_all_in:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            await self.process_turn()
            return

        await self.update_game_state_message()
        
        if current_player.is_gemini:
            await self.get_gemini_poker_action(current_player)
        elif current_player.is_cpu:
            await asyncio.sleep(2)
            # Simple CPU logic
            amount_to_call = self.current_bet - current_player.bet
            if amount_to_call > 0:
                if amount_to_call >= current_player.chips: # Must go all-in to call
                    await self.handle_action(current_player, 'call')
                else:
                    # 70% call, 30% fold
                    if random.random() < 0.7:
                        await self.handle_action(current_player, 'call')
                    else:
                        await self.handle_action(current_player, 'fold')
            else: # Can check
                await self.handle_action(current_player, 'check')

    async def get_gemini_poker_action(self, player):
        await self.interaction.channel.send(f"**{player.name} (Gemini) が思考中です...**")
        hand_str = ' '.join(map(str, player.hand))
        community_str = ' '.join(map(str, self.community_cards))
        
        player_states = []
        for p in self.players:
            state = {
                "name": p.name,
                "chips": p.chips,
                "bet": p.bet,
                "is_folded": p.is_folded,
                "is_all_in": p.is_all_in,
                "is_me": p == player
            }
            player_states.append(state)

        amount_to_call = self.current_bet - player.bet
        min_raise = self.current_bet * 2 if self.current_bet > 0 else self.big_blind_amount

        prompt = f"""
            あなたはプロのテキサスホールデムポーカープレイヤーです。
            以下のゲーム状況を分析し、あなたの取るべき最適なアクションをJSON形式で出力してください。

            # ゲーム状況
            - ゲームステージ: {self.game_stage}
            - あなたの手札: {hand_str}
            - コミュニティカード: {community_str or "なし"}
            - ポット合計: {self.pot}
            - 現在のラウンドでのあなたのベット額: {player.bet}
            - 現在のコールに必要な合計ベット額: {self.current_bet}
            - あなたの残りチップ: {player.chips}
            - プレイヤーの状態: {json.dumps(player_states, indent=2, ensure_ascii=False)}

            # あなたが実行可能なアクション
            - `fold`: ゲームから降ります。
            - `check`: 追加のベットをせずに行動を次のプレイヤーに回します。（あなたのベット額が現在のコール額 `{self.current_bet}` と同等かそれ以上の場合にのみ可能です）
            - `call`: 現在のベット額までチップを追加で出します。コールに必要な額は `{amount_to_call}` です。
            - `raise`: 現在のベット額をさらに引き上げます。この場合、`amount`にレイズ後の合計ベット額を指定してください。最低レイズ額は `{min_raise}` です。
            - `all-in`: あなたの持っているチップをすべてベットします。

            # 注意事項
            - JSONは必ず `action` と、レイズの場合は `amount` キーを含めてください。
            - `amount`はレイズ後の合計ベット額です。追加する額ではありません。
            - 最終的な出力はJSONオブジェクトのみにしてください。

            ```json
            {{
            "action": "...",
            "amount": ...
            }}
            ```
            """
        try:
            response = model.generate_content(prompt)
            
            json_part = None
            if "```json" in response.text:
                json_part = response.text.split("```json")[1].strip().replace("```", "")
            else:
                json_part = response.text[response.text.find('{'):response.text.rfind('}')+1]

            if not json_part:
                raise ValueError("No JSON found in response")

            action_data = json.loads(json_part)
            
            action = action_data.get("action")
            amount = action_data.get("amount", 0)

            await self.interaction.channel.send(f"**{player.name} (Gemini) のアクション:** {action}{' ' + str(amount) if action == 'raise' else ''}")

            can_check = amount_to_call <= 0

            if action == 'fold':
                await self.handle_action(player, 'fold')
            elif action == 'check':
                if not can_check:
                    await self.handle_action(player, 'call') if player.chips >= amount_to_call else await self.handle_action(player, 'fold')
                else:
                    await self.handle_action(player, 'check')
            elif action == 'call':
                if can_check:
                    await self.handle_action(player, 'check')
                else:
                    await self.handle_action(player, 'call')
            elif action == 'raise':
                if amount > player.chips + player.bet:
                    amount = player.chips + player.bet
                if amount < min_raise and player.chips + player.bet > min_raise:
                    amount = min_raise
                
                if amount <= self.current_bet:
                    await self.handle_action(player, 'call')
                else:
                    await self.handle_action(player, 'raise', amount)
            elif action == 'all-in':
                await self.handle_action(player, 'raise', player.chips + player.bet)
            else:
                await self.handle_action(player, 'fold')

        except Exception as e:
            print(f"Gemini action error: {e}")
            await self.interaction.channel.send(f"{player.name} (Gemini) がエラーでフォールドしました。")
            await self.handle_action(player, 'fold')

    async def end_betting_round(self):
        self.is_betting_round_active = False
        self.pot += sum(p.bet for p in self.players)
        for p in self.players:
            p.bet = 0
            p.has_acted = False
        
        active_players = [p for p in self.players if not p.is_folded]
        if len(active_players) <= 1:
            await self.end_round()
            return

        if self.game_stage == "pre-flop":
            self.game_stage = "flop"
            self.community_cards.extend([self.deck.deal() for _ in range(3)])
            await self.start_betting_round()
        elif self.game_stage == "flop":
            self.game_stage = "turn"
            self.community_cards.append(self.deck.deal())
            await self.start_betting_round()
        elif self.game_stage == "turn":
            self.game_stage = "river"
            self.community_cards.append(self.deck.deal())
            await self.start_betting_round()
        elif self.game_stage == "river":
            self.game_stage = "showdown"
            await self.end_round()

    async def handle_action(self, player, action, amount=0):
        if player != self.players[self.current_player_index] or self.is_betting_round_active == False:
            return

        if action == 'fold':
            player.is_folded = True
            player.has_acted = True
        elif action == 'check':
            if self.current_bet > player.bet: return
            player.has_acted = True
        elif action == 'call':
            amount_to_call = self.current_bet - player.bet
            if amount_to_call >= player.chips:
                player.bet += player.chips
                player.chips = 0
                player.is_all_in = True
            else:
                player.chips -= amount_to_call
                player.bet += amount_to_call
            player.has_acted = True
        elif action == 'raise':
            if amount < self.current_bet * 2 and player.chips + player.bet > self.current_bet * 2: return
            if amount >= player.chips + player.bet:
                amount = player.chips + player.bet
                player.is_all_in = True
            
            amount_to_raise = amount - player.bet
            player.chips -= amount_to_raise
            player.bet = amount
            self.current_bet = player.bet
            player.has_acted = True
            for p in self.players:
                if p != player and not p.is_folded and not p.is_all_in:
                    p.has_acted = False

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        await self.process_turn()


    def evaluate_hand(self, hand):
        all_hands = list(itertools.combinations(hand, 5))
        best_hand_rank = (-1, [])

        for h in all_hands:
            rank = self.get_hand_rank(h)
            if rank[0] > best_hand_rank[0]:
                best_hand_rank = rank
            elif rank[0] == best_hand_rank[0]:
                my_kickers = sorted([c.value for c in rank[1]], reverse=True)
                best_kickers = sorted([c.value for c in best_hand_rank[1]], reverse=True)
                if my_kickers > best_kickers:
                    best_hand_rank = rank
        
        return best_hand_rank

    def get_hand_rank(self, hand):
        hand = sorted(hand, key=lambda card: card.value, reverse=True)
        values = [c.value for c in hand]
        suits = [c.suit for c in hand]
        
        is_flush = len(set(suits)) == 1
        is_straight = (len(set(values)) == 5 and max(values) - min(values) == 4)
        if values == [14, 5, 4, 3, 2]: is_straight = True

        if is_straight and is_flush:
            if values[0] == 14: return (9, hand)
            return (8, hand)
        
        counts = {v: values.count(v) for v in set(values)}
        sorted_counts = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)
        
        if sorted_counts[0][1] == 4:
            four_val = sorted_counts[0][0]
            kicker_val = sorted_counts[1][0]
            ordered_hand = sorted(hand, key=lambda c: (c.value != four_val, c.value), reverse=True)
            return (7, ordered_hand)
        
        if sorted_counts[0][1] == 3 and sorted_counts[1][1] == 2:
            return (6, hand)
            
        if is_flush:
            return (5, hand)
            
        if is_straight:
            if values == [14, 5, 4, 3, 2]:
                return (4, [c for c in hand if c.value != 14] + [c for c in hand if c.value == 14])
            return (4, hand)
            
        if sorted_counts[0][1] == 3:
            three_val = sorted_counts[0][0]
            ordered_hand = sorted(hand, key=lambda c: (c.value != three_val, c.value), reverse=True)
            return (3, ordered_hand)
            
        if sorted_counts[0][1] == 2 and sorted_counts[1][1] == 2:
            pair1_val, pair2_val = sorted_counts[0][0], sorted_counts[1][0]
            kicker_val = sorted_counts[2][0]
            ordered_hand = sorted(hand, key=lambda c: (c.value != pair1_val and c.value != pair2_val, c.value), reverse=True)
            return (2, ordered_hand)
            
        if sorted_counts[0][1] == 2:
            pair_val = sorted_counts[0][0]
            ordered_hand = sorted(hand, key=lambda c: (c.value != pair_val, c.value), reverse=True)
            return (1, ordered_hand)
            
        return (0, hand)

    async def end_round(self):
        self.pot += sum(p.bet for p in self.players)
        for p in self.players: p.bet = 0

        active_players = [p for p in self.players if not p.is_folded]
        
        if len(active_players) == 1:
            winner = active_players[0]
            winner.chips += self.pot
            embed = self.create_embed(f"{winner.name} の勝利！")
            await self.game_message.edit(embed=embed, view=None)
        else:
            winner_data = []
            for player in active_players:
                full_hand = player.hand + self.community_cards
                hand_rank = self.evaluate_hand(full_hand)
                winner_data.append({"player": player, "rank": hand_rank})

            winner_data.sort(key=lambda x: (x["rank"][0], [c.value for c in x["rank"][1]]), reverse=True)
            
            best_rank_tuple = (winner_data[0]["rank"][0], [c.value for c in winner_data[0]["rank"][1]])
            winners = [d for d in winner_data if (d["rank"][0], [c.value for c in d["rank"][1]]) == best_rank_tuple]
            
            winnings = self.pot // len(winners)
            for w_data in winners:
                w_data["player"].chips += winnings
            
            hand_names = ["ハイカード", "ワンペア", "ツーペア", "スリーカード", "ストレート", "フラッシュ", "フルハウス", "フォーカード", "ストレートフラッシュ", "ロイヤルフラッシュ"]
            win_hand_name = hand_names[winner_data[0]["rank"][0]]
            win_hand_str = ' '.join(map(str, winner_data[0]["rank"][1]))
            
            winner_names = ", ".join([w["player"].name for w in winners])
            embed = self.create_embed(f"{winner_names} の勝利！役: {win_hand_name} ({win_hand_str})")
            
            for p in active_players:
                hand_str = ' '.join(map(str, p.hand))
                p_rank = self.evaluate_hand(p.hand + self.community_cards)
                p_hand_name = hand_names[p_rank[0]]
                embed.add_field(name=f"{p.name}の手札: {hand_str}", value=f"役: {p_hand_name}", inline=False)

            await self.game_message.edit(embed=embed, view=None)

        self.game_in_progress = False
        view = discord.ui.View(timeout=None)
        view.add_item(Button(label="次のラウンドへ", style=discord.ButtonStyle.primary, custom_id="poker_next_round"))
        view.add_item(Button(label="ゲーム終了", style=discord.ButtonStyle.danger, custom_id="poker_end_game"))
        await self.interaction.channel.send("次のラウンドを開始しますか？", view=view)


    async def send_hands(self):
        for player in self.players:
            if not player.is_cpu and not player.is_gemini:
                try:
                    hand_str = ' '.join(map(str, player.hand))
                    embed = discord.Embed(title=f"{self.interaction.guild.name}でのポーカー", description=f"あなたの手札: {hand_str}", color=discord.Color.blue())
                    await player.user.send(embed=embed)
                except discord.Forbidden:
                    await self.interaction.channel.send(f"{player.user.mention} DMの送信に失敗しました。このbotからのDMを許可してください。", delete_after=10)


    def create_embed(self, description=""):
        embed = discord.Embed(title="テキサスホールデム", description=description, color=discord.Color.green())
        cards_str = ' '.join(map(str, self.community_cards))
        embed.add_field(name=f"コミュニティカード ({self.game_stage})", value=cards_str or "なし", inline=False)
        embed.add_field(name="ポット", value=str(self.pot), inline=False)
        
        player_info = ""
        for i, player in enumerate(self.players):
            status = ""
            if player.is_folded: status = " (フォールド)"
            if player.is_all_in: status = " (オールイン)"
            
            turn_indicator = "▶️" if i == self.current_player_index and self.game_in_progress and not self.players[i].is_folded else ""
            
            player_info += f"{turn_indicator}**{player.name}**: {player.chips}チップ (ベット: {player.bet}){status}\n"
        
        embed.add_field(name="プレイヤー", value=player_info, inline=False)
        return embed

    async def update_game_state_message(self):
        embed = self.create_embed()
        
        current_player = self.players[self.current_player_index]
        if not current_player.is_cpu and not current_player.is_gemini and self.game_in_progress:
            self.action_view = PokerView(self)
            if self.game_message:
                await self.game_message.edit(embed=embed, view=self.action_view)
            else:
                self.game_message = await self.interaction.channel.send(embed=embed, view=self.action_view)
        else:
            if self.game_message:
                await self.game_message.edit(embed=embed, view=None)
            else:
                self.game_message = await self.interaction.channel.send(embed=embed)


class RaiseModal(Modal, title='レイズ額'):
    def __init__(self, game):
        super().__init__()
        self.game = game
        player = game.players[game.current_player_index]
        min_raise = game.current_bet * 2
        placeholder = f"最低{min_raise}、最大{player.chips + player.bet}"
        self.amount = TextInput(label='レイズ後の合計ベット額', placeholder=placeholder)
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        game = self.game
        player = game.players[game.current_player_index]
        if interaction.user.id != player.user.id:
            return await interaction.response.send_message("あなたのターンではありません。", ephemeral=True)
        
        try:
            amount = int(self.amount.value)
            min_raise = game.current_bet * 2
            if amount < min_raise and player.chips + player.bet > min_raise:
                 return await interaction.response.send_message(f"レイズ額が小さすぎます。最低でも {min_raise} にしてください。", ephemeral=True)
            if amount > player.chips + player.bet:
                 return await interaction.response.send_message(f"チップが足りません。", ephemeral=True)
            
            await interaction.response.defer()
            await game.handle_action(player, 'raise', amount)
        except ValueError:
            await interaction.response.send_message("数値を入力してください。", ephemeral=True)


class PokerView(View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game
        player = game.players[game.current_player_index]
        can_check = player.bet >= game.current_bet
        amount_to_call = game.current_bet - player.bet

        self.check_button.disabled = not can_check
        self.call_button.label = f"コール ({amount_to_call})" if not can_check else "コール"
        self.call_button.disabled = can_check or player.chips < amount_to_call
        self.raise_button.disabled = player.chips <= amount_to_call
        self.fold_button.disabled = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.game.players[self.game.current_player_index].user.id == interaction.user.id:
            return True
        await interaction.response.send_message("あなたのターンではありません。", ephemeral=True)
        return False

    @discord.ui.button(label="チェック", style=discord.ButtonStyle.secondary, custom_id="poker_check")
    async def check_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await self.game.handle_action(self.game.players[self.game.current_player_index], 'check')

    @discord.ui.button(label="コール", style=discord.ButtonStyle.primary, custom_id="poker_call")
    async def call_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await self.game.handle_action(self.game.players[self.game.current_player_index], 'call')

    @discord.ui.button(label="レイズ", style=discord.ButtonStyle.success, custom_id="poker_raise")
    async def raise_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(RaiseModal(self.game))

    @discord.ui.button(label="フォールド", style=discord.ButtonStyle.danger, custom_id="poker_fold")
    async def fold_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await self.game.handle_action(self.game.players[self.game.current_player_index], 'fold')


poker_games = {}

class PokerSetupView(View):
    def __init__(self, interaction):
        super().__init__(timeout=120)
        self.interaction = interaction

    async def on_timeout(self):
        game = poker_games.get(self.interaction.channel.id)
        if game and not game.game_in_progress:
            message = await self.interaction.original_response()
            await message.edit(content="参加受付は終了しました。", view=None)
            # Automatically start the game if enough players joined
            if len(game.players) >= 2:
                await game.start_game()
            else:
                await self.interaction.channel.send("プレイヤーが足りないためゲームを開始できませんでした。")
                poker_games.pop(self.interaction.channel.id, None)


    @discord.ui.button(label="参加", style=discord.ButtonStyle.success)
    async def join_game(self, interaction: discord.Interaction, button: Button):
        game = poker_games.get(self.interaction.channel.id)
        if game and not game.game_in_progress:
            if game.add_player(interaction.user):
                await interaction.response.send_message(f"{interaction.user.display_name} がゲームに参加しました。", ephemeral=True)
                embed = game.create_embed("ポーカーの参加者を募集中！参加ボタンで参加できます。")
                await game.game_message.edit(embed=embed, view=self)
            else:
                await interaction.response.send_message("すでに参加しています。", ephemeral=True)
        else:
            await interaction.response.send_message("現在参加可能なゲームはありません。", ephemeral=True)

    @discord.ui.button(label="ゲーム開始", style=discord.ButtonStyle.primary)
    async def start_game_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message("ゲームを開始できるのはホストのみです。", ephemeral=True)
        
        game = poker_games.get(self.interaction.channel.id)
        if game and not game.game_in_progress:
            if len(game.players) < 2:
                 return await interaction.response.send_message("プレイヤーが2人未満です。", ephemeral=True)
            self.stop()
            await interaction.response.defer()
            await game.start_game()

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger)
    async def cancel_game_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message("募集をキャンセルできるのはホストのみです。", ephemeral=True)

        game = poker_games.get(self.interaction.channel.id)
        if game and not game.game_in_progress:
            self.stop()
            await interaction.response.defer()
            message = await self.interaction.original_response()
            await message.edit(content="ゲーム募集をキャンセルしました。", view=None)
            poker_games.pop(self.interaction.channel.id, None)


@client.tree.command(name='poker', description='テキサスホールデムポーカーを開始します。')
@app_commands.describe(
    cpu_players="CPUプレイヤーの数（0-7）",
    gemini_players="Gemini AIプレイヤーの数（0-7）"
)
async def poker(interaction: discord.Interaction, 
              cpu_players: app_commands.Range[int, 0, 7] = 0,
              gemini_players: app_commands.Range[int, 0, 7] = 0):
    if interaction.channel.id in poker_games:
        await interaction.response.send_message("このチャンネルではすでにゲームが進行中または募集中です。")
        return

    if cpu_players + gemini_players > 7:
        await interaction.response.send_message("プレイヤーの合計はあなたを含めて8人までです。CPUとGeminiの合計を7人以下にしてください。")
        return

    game = PokerGame(interaction, cpu_players, gemini_players)
    poker_games[interaction.channel.id] = game
    
    game.add_player(interaction.user)
    
    # Add CPU players
    for i in range(cpu_players):
        cpu_id = random.randint(100000000, 999999999)
        cpu_user = discord.Object(id=cpu_id)
        cpu_user.name = f"CPU {i+1}"
        cpu_user.display_name = f"CPU {i+1}"
        game.add_player(cpu_user, is_cpu=True)

    # Add Gemini players
    for i in range(gemini_players):
        gemini_id = random.randint(100000000, 999999999)
        gemini_user = discord.Object(id=gemini_id)
        gemini_user.name = f"Gemini {i+1}"
        gemini_user.display_name = f"Gemini {i+1}"
        game.add_player(gemini_user, is_cpu=False, is_gemini=True)

    view = PokerSetupView(interaction)
    embed = game.create_embed("ポーカーの参加者を募集中！参加ボタンで参加できます。")
    await interaction.response.send_message(embed=embed, view=view)
    game.game_message = await interaction.original_response()

@client.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data or 'custom_id' not in interaction.data:
        return

    custom_id = interaction.data['custom_id']
    game = poker_games.get(interaction.channel.id)

    if not game:
        return

    if custom_id == "poker_next_round":
        if interaction.user.id != game.interaction.user.id:
            return await interaction.response.send_message("次のラウンドを開始できるのはホストのみです。", ephemeral=True)
        
        await interaction.message.delete()
        await interaction.response.defer()
        await game.start_round()

    elif custom_id == "poker_end_game":
        if interaction.user.id != game.interaction.user.id:
            return await interaction.response.send_message("ゲームを終了できるのはホストのみです。", ephemeral=True)
        
        await interaction.message.delete()
        await interaction.response.defer()
        await interaction.channel.send("ゲームを終了しました。")
        poker_games.pop(interaction.channel.id, None)

server_thread()
client.run(TOKEN)

