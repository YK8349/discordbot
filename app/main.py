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
model = genai.GenerativeModel('gemini-pro') 

GUILD_ID = 1127013631763169301  # テスト用サーバーIDに置き換えてください（任意）

# --- Poker Game Implementation ---

poker_games = {}
CHIPS_FILE = "chips.json"

# --- Chip Management Functions ---
def load_chips():
    try:
        with open(CHIPS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_chips(data):
    with open(CHIPS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

def get_poker_hand_rank(hand):
    ranks = sorted([card[0] for card in hand], key=lambda r: '23456789TJQKA'.index(r), reverse=True)
    suits = [card[1] for card in hand]
    rank_counts = {r: ranks.count(r) for r in ranks}
    is_flush = len(set(suits)) == 1
    
    unique_ranks = sorted(list(set(ranks)), key=lambda r: '23456789TJQKA'.index(r))
    is_straight = False
    if len(unique_ranks) == 5:
        if '23456789TJQKA'.find(''.join(unique_ranks)) != -1:
            is_straight = True
        elif set(unique_ranks) == {'A', '2', '3', '4', '5'}:
            is_straight = True
            ranks = ['5', '4', '3', '2', 'A']

    if is_straight and is_flush:
        if set(ranks) == {'A', 'K', 'Q', 'J', 'T'}: return "ロイヤルフラッシュ", ranks
        return "ストレートフラッシュ", ranks
    if 4 in rank_counts.values():
        four_kind_rank = [r for r, c in rank_counts.items() if c == 4][0]
        other_cards = sorted([r for r in ranks if r != four_kind_rank], key=lambda r: '23456789TJQKA'.index(r), reverse=True)
        return "フォーカード", [four_kind_rank] * 4 + other_cards
    if sorted(rank_counts.values()) == [2, 3]:
        three_kind_rank = [r for r, c in rank_counts.items() if c == 3][0]
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        return "フルハウス", [three_kind_rank] * 3 + [pair_rank] * 2
    if is_flush: return "フラッシュ", ranks
    if is_straight: return "ストレート", ranks
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
    best_rank_name, best_hand_cards, best_rank_score = "ハイカード", [], -1
    hand_ranks_order = {"ロイヤルフラッシュ": 9, "ストレートフラッシュ": 8, "フォーカード": 7, "フルハウス": 6, "フラッシュ": 5, "ストレート": 4, "スリーカード": 3, "ツーペア": 2, "ワンペア": 1, "ハイカード": 0}
    for hand_combination in itertools.combinations(seven_cards, 5):
        rank_name, hand_cards = get_poker_hand_rank(list(hand_combination))
        rank_score = hand_ranks_order[rank_name]
        if rank_score > best_rank_score:
            best_rank_score, best_rank_name, best_hand_cards = rank_score, rank_name, hand_cards
        elif rank_score == best_rank_score:
            current_best_values = ['23456789TJQKA'.index(r) for r in best_hand_cards]
            new_hand_values = ['23456789TJQKA'.index(r) for r in hand_cards]
            if new_hand_values > current_best_values:
                best_hand_cards = hand_cards
    return best_rank_name, best_hand_cards, hand_ranks_order[best_rank_name]

class CPUUser:
    def __init__(self, name="CPU Player"):
        self.id = random.randint(10**9, 10**10 - 1)
        self.display_name = name
        self.mention = f"@{name}"

class Player:
    def __init__(self, user: discord.User, chips: int, is_cpu: bool = False):
        self.user, self.chips, self.is_cpu = user, chips, is_cpu
        self.hand, self.current_bet, self.has_acted, self.is_all_in, self.folded = [], 0, False, False, False

class PokerGame:
    def __init__(self, interaction: discord.Interaction):
        self.channel, self.starter = interaction.channel, interaction.user
        self.players, self.deck, self.community_cards, self.log = [], [], [], []
        self.pot, self.current_round_bet = 0, 0
        self.game_phase = 'waiting'
        self.dealer_index = -1
        self.main_message, self.action_view_message = None, None

    def add_player(self, user: discord.User, is_cpu=False):
        if not any(p.user.id == user.id for p in self.players):
            chips_data = load_chips()
            player_chips = chips_data.get(str(user.id), 1000)
            if player_chips <= 0: player_chips = 1000
            self.players.append(Player(user, player_chips, is_cpu))
            return True
        return False

    def get_player(self, user: discord.User):
        return next((p for p in self.players if p.user.id == user.id), None)

    def get_hand_players(self):
        return [p for p in self.players if not p.folded]

    def save_all_player_chips(self):
        chips_data = load_chips()
        for player in self.players:
            if not player.is_cpu:
                chips_data[str(player.user.id)] = player.chips
        save_chips(chips_data)

    async def start_hand(self, interaction: discord.Interaction):
        if len(self.players) < 2:
            await interaction.response.send_message("プレイヤーが2人未満です。", ephemeral=True)
            return
        
        self.game_phase = 'dealing'
        self.deck = list(itertools.product(RANKS, SUITS))
        random.shuffle(self.deck)
        self.community_cards, self.pot, self.current_round_bet = [], 0, 0
        self.dealer_index = (self.dealer_index + 1) % len(self.players)

        for p in self.players:
            p.hand = [self.deck.pop(), self.deck.pop()]
            p.current_bet, p.has_acted, p.folded, p.is_all_in = 0, False, False, False

        await interaction.response.send_message("各プレイヤーは下のボタンを押して手札を確認してください。", view=ViewHandView(self))

    async def begin_betting(self):
        self.game_phase = 'preflop'
        # Blinds
        small_blind_player = self.players[(self.dealer_index + 1) % len(self.players)]
        big_blind_player = self.players[(self.dealer_index + 2) % len(self.players)]
        sb_amount = min(5, small_blind_player.chips)
        bb_amount = min(10, big_blind_player.chips)
        await self.process_action(small_blind_player, 'bet', sb_amount)
        await self.process_action(big_blind_player, 'bet', bb_amount, is_blind=True)
        
        self.log = [f"新しいハンドが始まりました。ディーラーは {self.players[self.dealer_index].user.display_name} です。",
                    f"{small_blind_player.user.display_name} がSB {sb_amount} をベット。",
                    f"{big_blind_player.user.display_name} がBB {bb_amount} をベット。"]

        self.current_player_index = (self.dealer_index + 3) % len(self.players)
        
        await self.update_main_message(self.channel)
        await self.ask_for_action()

    async def ask_for_action(self):
        player = self.players[self.current_player_index]
        if player.folded or player.is_all_in:
            await self.next_turn()
            return

        if player.is_cpu:
            await asyncio.sleep(2)
            await self.cpu_make_decision(player)
        else:
            if self.action_view_message: await self.action_view_message.delete()
            view = PokerActionView(self)
            embed = discord.Embed(title=f"{player.user.display_name} のアクション", description=f"あなたのチップ: {player.chips}\n現在のベット額: {player.current_bet}", color=discord.Color.blue())
            self.action_view_message = await self.channel.send(content=player.user.mention, embed=embed, view=view)

    async def process_action(self, player: Player, action: str, amount: int = 0, is_blind=False):
        if action == 'fold':
            player.folded = True
            self.log.append(f"{player.user.display_name} がフォールドしました。")
        elif action == 'call':
            call_amount = self.current_round_bet - player.current_bet
            if call_amount >= player.chips:
                call_amount = player.chips
                player.is_all_in = True
                self.log.append(f"{player.user.display_name} がオールイン ({call_amount}) しました。")
            else:
                self.log.append(f"{player.user.display_name} がコール ({call_amount}) しました。")
            player.chips -= call_amount
            player.current_bet += call_amount
            self.pot += call_amount
        elif action == 'check':
            self.log.append(f"{player.user.display_name} がチェックしました。")
        elif action == 'raise':
            self.current_round_bet = amount
            bet_amount = amount - player.current_bet
            player.chips -= bet_amount
            player.current_bet += bet_amount
            self.pot += bet_amount
            if player.chips == 0: player.is_all_in = True
            self.log.append(f"{player.user.display_name} が {amount} にレイズしました。")
        elif action == 'bet': # For blinds
            player.chips -= amount
            player.current_bet = amount
            self.pot += amount
            if not is_blind: self.current_round_bet = amount

        if not is_blind: 
            player.has_acted = True
            await self.next_turn()

    async def cpu_make_decision(self, player: Player):
        _, _, hand_score = get_best_hand(player.hand + self.community_cards)
        call_amount = self.current_round_bet - player.current_bet

        if self.current_round_bet == 0: # Can check
            if hand_score > 2 and random.random() < 0.7: # Good hand, bet
                bet_amount = min(player.chips, max(self.big_blind, int(self.pot * 0.5)))
                await self.process_action(player, 'raise', bet_amount)
            else: # Weak hand, check
                await self.process_action(player, 'check')
        else: # Must call, raise or fold
            if call_amount >= player.chips: # All-in to call
                if hand_score > 1: await self.process_action(player, 'call')
                else: await self.process_action(player, 'fold')
                return

            if hand_score > 4 and random.random() < 0.5: # Very good hand, raise
                raise_amount = min(player.chips, call_amount * 2 + self.pot)
                await self.process_action(player, 'raise', self.current_round_bet + raise_amount)
            elif hand_score > 1: # Decent hand, call
                await self.process_action(player, 'call')
            else: # Bad hand, fold
                await self.process_action(player, 'fold')

    async def next_turn(self):
        if len(self.get_hand_players()) <= 1:
            await self.end_hand()
            return

        active_players = [p for p in self.players if not p.folded]
        if all(p.has_acted or p.is_all_in for p in active_players):
            await self.next_phase()
            return

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        await self.update_main_message(self.channel)
        await self.ask_for_action()

    async def next_phase(self):
        self.current_round_bet = 0
        for p in self.players: p.current_bet, p.has_acted = 0, False
        self.current_player_index = (self.dealer_index + 1) % len(self.players)

        if self.game_phase == 'preflop': self.game_phase = 'flop'; self.community_cards.extend([self.deck.pop() for _ in range(3)]); self.log.append("--- フロップ ---")
        elif self.game_phase == 'flop': self.game_phase = 'turn'; self.community_cards.append(self.deck.pop()); self.log.append("--- ターン ---")
        elif self.game_phase == 'turn': self.game_phase = 'river'; self.community_cards.append(self.deck.pop()); self.log.append("--- リバー ---")
        elif self.game_phase == 'river': await self.end_hand(); return
        
        await self.update_main_message(self.channel)
        await self.ask_for_action()

    async def end_hand(self):
        if self.action_view_message: await self.action_view_message.delete()
        hand_players = self.get_hand_players()
        if len(hand_players) == 1:
            winner = hand_players[0]; winner.chips += self.pot
            self.log.append(f"{winner.user.display_name} がポット({self.pot})を獲得しました。")
        else:
            results = []
            for player in hand_players:
                best_rank, best_cards, _ = get_best_hand(player.hand + self.community_cards)
                results.append({'player': player, 'rank': best_rank, 'cards': best_cards})
            
            hand_ranks_order = {"ロイヤルフラッシュ": 9, "ストレートフラッシュ": 8, "フォーカード": 7, "フルハウス": 6, "フラッシュ": 5, "ストレート": 4, "スリーカード": 3, "ツーペア": 2, "ワンペア": 1, "ハイカード": 0}
            def get_sort_key(res):
                card_values = ['23456789TJQKA'.index(r) for r in res['cards']]
                return (hand_ranks_order[res['rank']], card_values)
            results.sort(key=get_sort_key, reverse=True)
            
            winner_data = results[0]; winner = winner_data['player']; winner.chips += self.pot
            self.log.append("--- ショーダウン ---")
            for res in results:
                p = res['player']; hand_str = ' '.join([f"{r}{s}" for r, s in p.hand])
                self.log.append(f"{p.user.display_name}: {res['rank']} (手札: {hand_str})")
            self.log.append(f"勝者: {winner.user.display_name} (役: {winner_data['rank']}) がポット({self.pot})を獲得しました。")

        self.save_all_player_chips()
        await self.update_main_message(self.channel, hand_ended=True)
        self.game_phase = 'waiting'

    async def update_main_message(self, channel, hand_ended=False):
        embed = discord.Embed(title="テキサスホールデム", color=discord.Color.green())
        community_str = ' '.join([f"{r}{s}" for r, s in self.community_cards]) if self.community_cards else "なし"
        embed.add_field(name="場のカード", value=community_str, inline=False).add_field(name="ポット", value=str(self.pot), inline=False)
        player_statuses = []
        for i, p in enumerate(self.players):
            status = "フォールド" if p.folded else f"チップ: {p.chips} | ベット: {p.current_bet}"
            if i == self.dealer_index: status += " (D)"
            player_statuses.append(f"{p.user.display_name}: {status}")
        embed.add_field(name="プレイヤー", value="\n".join(player_statuses), inline=False)
        if self.log: embed.add_field(name="ログ", value="\n".join(self.log[-5:]), inline=False)
        if hand_ended: embed.set_footer(text="ハンド終了。`/poker deal` で次のハンドを開始します。")
        if self.main_message: await self.main_message.edit(embed=embed)
        else: self.main_message = await channel.send(embed=embed)

class PokerActionView(View):
    def __init__(self, game: PokerGame):
        super().__init__(timeout=120)
        self.game = game
        player = game.players[game.current_player_index]
        self.children[0].disabled = player.current_bet < game.current_round_bet
        self.children[1].disabled = player.current_bet >= game.current_round_bet or player.chips <= (game.current_round_bet - player.current_bet)
        self.children[3].disabled = player.chips <= game.current_round_bet

    async def handle_button_press(self, interaction: discord.Interaction, action: str, amount=0):
        player = self.game.get_player(interaction.user)
        if not player or player != self.game.players[self.game.current_player_index]:
            await interaction.response.send_message("あなたのターンではありません。", ephemeral=True); return
        await interaction.response.defer()
        await self.game.process_action(player, action, amount)

    @discord.ui.button(label="チェック", style=discord.ButtonStyle.secondary)
    async def check(self, interaction: discord.Interaction, button: Button): await self.handle_button_press(interaction, 'check')
    @discord.ui.button(label="コール", style=discord.ButtonStyle.primary)
    async def call(self, interaction: discord.Interaction, button: Button): await self.handle_button_press(interaction, 'call')
    @discord.ui.button(label="フォールド", style=discord.ButtonStyle.danger)
    async def fold(self, interaction: discord.Interaction, button: Button): await self.handle_button_press(interaction, 'fold')
    @discord.ui.button(label="レイズ", style=discord.ButtonStyle.success)
    async def raise_btn(self, interaction: discord.Interaction, button: Button): await interaction.response.send_modal(RaiseModal(self.game, self))

class RaiseModal(Modal, title="レイズ額"):
    def __init__(self, game: PokerGame, view: PokerActionView):
        super().__init__()
        self.game, self.original_view = game, view
        player = game.players[game.current_player_index]
        min_raise = game.current_round_bet * 2
        self.amount = TextInput(label=f"レイズ後の合計ベット額 (最小: {min_raise})", placeholder=str(min_raise), required=True)
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount.value)
            player = self.game.players[self.game.current_player_index]
            min_raise = self.game.current_round_bet * 2
            if amount < min_raise: await interaction.response.send_message(f"レイズ額が小さすぎます。最小額は {min_raise} です。", ephemeral=True); return
            if amount > player.chips + player.current_bet: await interaction.response.send_message("チップが足りません。", ephemeral=True); return
            await self.original_view.handle_button_press(interaction, 'raise', amount=amount)
        except ValueError: await interaction.response.send_message("数値を入力してください。", ephemeral=True)

class ViewHandView(View):
    def __init__(self, game: PokerGame):
        super().__init__(timeout=60)
        self.game, self.players_who_viewed = game, set()

    @discord.ui.button(label="手札を見る", style=discord.ButtonStyle.secondary)
    async def view_hand(self, interaction: discord.Interaction, button: Button):
        player = self.game.get_player(interaction.user)
        if not player: await interaction.response.send_message("あなたはゲームに参加していません。", ephemeral=True); return
        if player.user.id in self.players_who_viewed: await interaction.response.send_message("既に手札を確認しています。", ephemeral=True); return
        hand_str = ' '.join([f"{r}{s}" for r, s in player.hand])
        await interaction.response.send_message(f"あなたの手札: **{hand_str}**", ephemeral=True)
        self.players_who_viewed.add(player.user.id)
        if len(self.players_who_viewed) == len(self.game.players): await interaction.message.delete(); await self.game.begin_betting()

class PokerJoinView(View):
    def __init__(self, game: PokerGame):
        super().__init__(timeout=300)
        self.game = game

    @discord.ui.button(label="参加する", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: Button):
        if self.game.add_player(interaction.user):
            await interaction.response.send_message(f"{interaction.user.mention} がゲームに参加しました。", ephemeral=True)
            player_list = "\n".join([f"{p.user.display_name} ({p.chips}チップ)" for p in self.game.players])
            embed = interaction.message.embeds[0]; embed.set_field_at(0, name="参加者", value=player_list, inline=False); await interaction.message.edit(embed=embed)
        else: await interaction.response.send_message("既に参加しています。", ephemeral=True)

class MyClient(discord.Client):
    def __init__(self): super().__init__(intents=intents); self.tree = app_commands.CommandTree(self)
    async def setup_hook(self): guild = discord.Object(id=GUILD_ID); self.tree.copy_global_to(guild=guild); await self.tree.sync(guild=guild)

client = MyClient()
poker_group = app_commands.Group(name="poker", description="ポーカーゲームを管理します。")

@poker_group.command(name="start", description="ポーカーゲームを開始します。")
async def poker_start(interaction: discord.Interaction):
    if interaction.channel_id in poker_games: await interaction.response.send_message("このチャンネルでは既にゲームが進行中です。", ephemeral=True); return
    game = PokerGame(interaction); poker_games[interaction.channel_id] = game; game.add_player(interaction.user)
    player_list = "\n".join([f"{p.user.display_name} ({p.chips}チップ)" for p in game.players])
    embed = discord.Embed(title="ポーカーゲーム募集中！", description=f"{interaction.user.mention} がゲームを開始しました。\n`/poker add_cpu` でCPUを追加できます。\n`/poker deal` で最初のハンドをスタートします。", color=discord.Color.blue())
    embed.add_field(name="参加者", value=player_list, inline=False)
    await interaction.response.send_message(embed=embed, view=PokerJoinView(game))
    game.main_message = await interaction.original_response()

@poker_group.command(name="add_cpu", description="ゲームにCPUプレイヤーを追加します。")
@app_commands.describe(count="追加するCPUの数")
async def add_cpu(interaction: discord.Interaction, count: int = 1):
    game = poker_games.get(interaction.channel_id)
    if not game: await interaction.response.send_message("ゲームが開始されていません。", ephemeral=True); return
    if game.game_phase != 'waiting': await interaction.response.send_message("ゲームの進行中にCPUは追加できません。", ephemeral=True); return
    for i in range(count):
        cpu_user = CPUUser(name=f"CPU {i+1}")
        game.add_player(cpu_user, is_cpu=True)
    player_list = "\n".join([f"{p.user.display_name} ({p.chips}チップ)" for p in game.players])
    embed = game.main_message.embeds[0]; embed.set_field_at(0, name="参加者", value=player_list, inline=False); await game.main_message.edit(embed=embed)
    await interaction.response.send_message(f"{count}人のCPUプレイヤーを追加しました。", ephemeral=True)

@poker_group.command(name="deal", description="カードを配り、ハンドを開始します。")
async def poker_deal(interaction: discord.Interaction):
    game = poker_games.get(interaction.channel_id)
    if not game: await interaction.response.send_message("ゲームが開始されていません。", ephemeral=True); return
    if interaction.user != game.starter: await interaction.response.send_message("ゲームの開始者のみがディールできます。", ephemeral=True); return
    if game.game_phase != 'waiting': await interaction.response.send_message("ハンドの途中です。", ephemeral=True); return
    await game.start_hand(interaction)

@poker_group.command(name="end", description="現在のポーカーゲームを終了します。")
async def poker_end(interaction: discord.Interaction):
    if interaction.channel_id in poker_games:
        game = poker_games[interaction.channel_id]
        if interaction.user == game.starter or interaction.user.guild_permissions.manage_channels:
            game.save_all_player_chips()
            if game.action_view_message: await game.action_view_message.delete()
            del poker_games[interaction.channel_id]
            await interaction.response.send_message("ゲームを終了し、チップを保存しました。")
        else: await interaction.response.send_message("ゲームの開始者または管理者のみがゲームを終了できます。", ephemeral=True)
    else: await interaction.response.send_message("このチャンネルではゲームが開始されていません。")

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

server_thread()
client.run(TOKEN)
