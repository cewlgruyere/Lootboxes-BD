import discord
from discord import app_commands
from discord.ext import commands
from django.db.models import F, FloatField, ExpressionWrapper
from bd_models.models import BallInstance, Player, Ball, Special
from settings.models import settings
from typing import TYPE_CHECKING
import asyncio
import random
from asgiref.sync import sync_to_async
from ..models import Lootbox, LootSettings, PlayerLootbox
from discord.utils import utcnow
from datetime import timedelta

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

class ConfirmationView(discord.ui.LayoutView):
    def __init__(self, box_amount, amount, lbox):
        super().__init__(timeout=30)
        self.amount = amount
        self.lootbox_amount = box_amount
        self.chosen_lootboxes = lbox
        self.ball_list = []
        self.names = ""
    @classmethod
    async def ccv(cls, interaction, box_amount, amount, lbox,):
        self = cls(box_amount, amount, lbox)
        self.ball_list = await get_random(interaction, amount)
        self.names = ", ".join(ball.countryball.country for ball in self.ball_list)
        self.cv()
        return self
    async def p(self, interaction: discord.Interaction):
        player = await Player.objects.aget_or_none(discord_id=interaction.user.id)
        if len(self.ball_list) != self.amount:
            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    content="Thy lacks the necessary funds to purchase a box containing 'Loot'"
                ),
            )
            self.clear_items()
            self.add_item(container)
            await interaction.response.edit_message(view=self)
            return
        
        for i in range(self.lootbox_amount):
            lootbox_obj = await sync_to_async(lambda: Lootbox.objects.filter(name=self.chosen_lootboxes).first())()
            await PlayerLootbox.objects.acreate(player=player, lootbox=lootbox_obj)

        for ball in self.ball_list:
            ball.deleted = True
            await ball.asave(update_fields=("deleted",))
        container = discord.ui.Container(
            discord.ui.TextDisplay(
                content="Thanks for purchasing lootboxes!"
            ),
        )

        self.clear_items()
        self.add_item(container)

        await interaction.response.edit_message(view=self)
    async def c(self, interaction: discord.Interaction):
        container = discord.ui.Container(
            discord.ui.TextDisplay(
                content="Purchase cancelled."
            ),
        )

        self.clear_items()
        self.add_item(container)
        await interaction.response.edit_message(view=self)
    def cv(self):
        
        self.clear_items()
        p = discord.ui.Button(style=discord.ButtonStyle.success, label="Purchase")
        c = discord.ui.Button(style=discord.ButtonStyle.danger, label="Cancel")
        p.callback = self.p
        c.callback = self.c
        container1 = discord.ui.Container(
            discord.ui.TextDisplay(content="# Confirmation"),
            discord.ui.TextDisplay(content=f"Are you sure you want to lose {self.amount} {settings.plural_collectible_name} for {self.lootbox_amount} lootbox(es) **{self.chosen_lootboxes}**"),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(content=f"## These are the balls you will lose:\n{self.names}"),
            discord.ui.ActionRow(p, c),
        )
        self.add_item(container1)
class GiftConfirmationView(discord.ui.LayoutView):
    def __init__(self, box_amount, amount, lbox, player,):
        super().__init__(timeout=30)
        self.amount = amount
        self.lootbox_amount = box_amount
        self.chosen_lootboxes = lbox
        self.player = player
        self.ball_list = []
        self.names = ""
    @classmethod
    async def ccv(cls, interaction, box_amount, amount, lbox, player):
        self = cls(box_amount, amount, lbox, player)
        self.ball_list = await get_random(interaction, amount)
        self.names = ", ".join(ball.countryball.country for ball in self.ball_list)
        self.cv()
        return self
    async def p(self, interaction: discord.Interaction):
        await interaction.response.defer()
        player = await Player.objects.aget_or_none(discord_id=self.player.id)
        if len(self.ball_list) != self.amount:
            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    content="Thy lacks the necessary funds to gift a box containing 'Loot'"
                ),
            )
            self.clear_items()
            self.add_item(container)
            await interaction.response.edit_message(view=self)
            return
        
        for i in range(self.lootbox_amount):
            lootbox_obj = await sync_to_async(lambda: Lootbox.objects.filter(name=self.chosen_lootboxes).first())()
            await PlayerLootbox.objects.acreate(player=player, lootbox=lootbox_obj)

        for ball in self.ball_list:
            ball.deleted = True
            await ball.asave(update_fields=("deleted",))
        container = discord.ui.Container(
            discord.ui.TextDisplay(
                content="Thanks for gifting lootboxes!"
            ),
        )

        self.clear_items()
        self.add_item(container)

        await interaction.edit_original_response(view=self)
        await interaction.followup.send(f"Hey {self.player.mention}! {interaction.user.mention} gave you {self.lootbox_amount}x lootbox(es)\n-# info: lootbox: {self.chosen_lootboxes}, price: {self.amount}")
    async def c(self, interaction: discord.Interaction):
        container = discord.ui.Container(
            discord.ui.TextDisplay(
                content="Purchase cancelled."
            ),
        )

        self.clear_items()
        self.add_item(container)
        await interaction.response.edit_message(view=self)
    def cv(self):
        
        self.clear_items()
        p = discord.ui.Button(style=discord.ButtonStyle.success, label="Purchase")
        c = discord.ui.Button(style=discord.ButtonStyle.danger, label="Cancel")
        p.callback = self.p
        c.callback = self.c
        container1 = discord.ui.Container(
            discord.ui.TextDisplay(content="# Confirmation"),
            discord.ui.TextDisplay(content=f"Are you sure you want to lose {self.amount} {settings.plural_collectible_name} for {self.lootbox_amount} lootbox(es) **{self.chosen_lootboxes}**"),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(content=f"## These are the balls you will lose:\n{self.names}"),
            discord.ui.ActionRow(p, c),
        )
        self.add_item(container1)
class Purchase(discord.ui.LayoutView):    
    def __init__(self, bot, interaction: discord.Interaction, lootboxes, price, economy):
        super().__init__(timeout=60)
        self.user = interaction.user.id
        self.bot = bot
        self.price = price
        self.amount = 1
        self.lootboxes = lootboxes
        self.selected = 0
        self.economy = economy
        self.lbox_view()
    
    async def bm1(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            await interaction.response.send_message("This aint your menu sonion", ephemeral=True)
            return
        self.amount -= 1
        self.lbox_view()
        await interaction.response.edit_message(view=self)
    async def bp1(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            await interaction.response.send_message("This aint your menu sonion", ephemeral=True)
            return
        self.amount += 1
        self.lbox_view()
        await interaction.response.edit_message(view=self)
    async def bpurchase(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            await interaction.response.send_message("This aint your menu sonion", ephemeral=True)
            return
        view = await ConfirmationView.ccv(interaction, self.amount, ((self.price * self.lootboxes[self.selected].price_multiplier) * self.amount), self.lootboxes[self.selected])
        await interaction.response.send_message(view=view, ephemeral=True)
        self.lbox_view(d=True)
        await self.m.edit(view=self)
            
    def lbox_view(self, d=False):
        self.clear_items()
        bm1 = discord.ui.Button(style=discord.ButtonStyle.primary, label="-1", disabled=self.amount < 2 or d==True)
        bp1 = discord.ui.Button(style=discord.ButtonStyle.primary, label="+1", disabled=d==True)
        bpurchase = discord.ui.Button(style=discord.ButtonStyle.success, label="Purchase", disabled=d==True)
        if self.economy == True:
            text = f"## Amount:\n{self.amount} of lootbox **{self.lootboxes[self.selected]}**\n## Total Price:\n{(self.price * self.lootboxes[self.selected].price_multiplier) * self.amount} {settings.currency_name}"
        else:
            text = f"## Amount:\n{self.amount} of lootbox **{self.lootboxes[self.selected]}**\n## Total Price:\n{(self.price * self.lootboxes[self.selected].price_multiplier) * self.amount} Balls"
        bm1.callback = self.bm1
        bp1.callback = self.bp1
        bpurchase.callback = self.bpurchase
        options = []
        for i in self.lootboxes:
            options.append(
                discord.SelectOption(
                    label=i.name,
                    value=str(i.id),
                    emoji=i.emoji
                )
            )
        lbox_s = discord.ui.Select(placeholder="Select the lootbox you want to purchase:", options=options, disabled=d==True)
        lbox_s.callback = self.sc
        container1 = discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay(content="# Purchase lootboxes"),
                discord.ui.TextDisplay(content="-# Made by @unitedstatesoferland/cewlgruyere"),
                accessory=discord.ui.Thumbnail(
                    media=self.bot.user.display_avatar.url,
                ),
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
            discord.ui.ActionRow(lbox_s),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.large),
            discord.ui.TextDisplay(content=text),
            discord.ui.ActionRow(bm1, bp1, bpurchase),
        )
        
        self.add_item(container1)
    async def sc(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            await interaction.response.send_message("This aint your menu sonion", ephemeral=True)
            return
        si = interaction.data["values"][0]

        for i, lootbox in enumerate(self.lootboxes):
            if str(lootbox.id) == si:
                self.selected = i
                break
        self.lbox_view()

        await interaction.response.edit_message(view=self)

class Gift(discord.ui.LayoutView):    
    def __init__(self, bot, interaction: discord.Interaction, lootboxes, price, economy, p2):
        super().__init__(timeout=60)
        self.user = interaction.user.id
        self.bot = bot
        self.price = price
        self.amount = 1
        self.lootboxes = lootboxes
        self.selected = 0
        self.p2 = p2
        self.economy = economy
        self.lbox_view()
    
    async def bm1(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            await interaction.response.send_message("This aint your menu sonion", ephemeral=True)
            return
        self.amount -= 1
        self.lbox_view()
        await interaction.response.edit_message(view=self)
    async def bp1(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            await interaction.response.send_message("This aint your menu sonion", ephemeral=True)
            return
        self.amount += 1
        self.lbox_view()
        await interaction.response.edit_message(view=self)
    async def bpurchase(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            await interaction.response.send_message("This aint your menu sonion", ephemeral=True)
            return
        view = await GiftConfirmationView.ccv(interaction, self.amount, ((self.price * self.lootboxes[self.selected].price_multiplier) * self.amount), self.lootboxes[self.selected], self.p2)
        await interaction.response.send_message(view=view, ephemeral=True)
        self.lbox_view(d=True)
        await self.m.edit(view=self)

        
    def lbox_view(self, d=False):
        self.clear_items()
        bm1 = discord.ui.Button(style=discord.ButtonStyle.primary, label="-1", disabled=self.amount < 2 or d==True)
        bp1 = discord.ui.Button(style=discord.ButtonStyle.primary, label="+1", disabled=d==True)
        bpurchase = discord.ui.Button(style=discord.ButtonStyle.success, label="Gift", disabled=d==True)
        if self.economy == True:
            text = f"## Amount:\n{self.amount} of lootbox **{self.lootboxes[self.selected]}**\n## Total Price:\n{(self.price * self.lootboxes[self.selected].price_multiplier) * self.amount} {settings.currency_name}"
        else:
            text = f"## Amount:\n{self.amount} of lootbox **{self.lootboxes[self.selected]}**\n## Total Price:\n{(self.price * self.lootboxes[self.selected].price_multiplier) * self.amount} Balls"
        bm1.callback = self.bm1
        bp1.callback = self.bp1
        bpurchase.callback = self.bpurchase
        options = []
        for i in self.lootboxes:
            options.append(
                discord.SelectOption(
                    label=i.name,
                    value=str(i.id),
                    emoji=i.emoji
                )
            )
        lbox_s = discord.ui.Select(placeholder="Select the lootbox you want to gift:", options=options, disabled=d==True)
        lbox_s.callback = self.sc
        container1 = discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay(content="# Gift lootboxes"),
                discord.ui.TextDisplay(content=f"-# Made by @unitedstatesoferland/cewlgruyere"),
                accessory=discord.ui.Thumbnail(
                    media=self.bot.user.display_avatar.url,
                ),
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
            discord.ui.ActionRow(lbox_s),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.large),
            discord.ui.TextDisplay(content=text),
            discord.ui.ActionRow(bm1, bp1, bpurchase),
        )
        
        self.add_item(container1)
    async def sc(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            await interaction.response.send_message("This aint your menu sonion", ephemeral=True)
            return
        si = interaction.data["values"][0]

        for i, lootbox in enumerate(self.lootboxes):
            if str(lootbox.id) == si:
                self.selected = i
                break
        self.lbox_view()

        await interaction.response.edit_message(view=self)

class Open(discord.ui.LayoutView):
    def __init__(self, bot, interaction: discord.Interaction, lootboxes, ball):
        super().__init__(timeout=60)
        self.user = interaction.user.id
        self.interaction = interaction
        self.bot = bot
        self.lootboxes = lootboxes
        self.ball = ball
        self.selected = 0
        self.special = None
        self.view()

    def view(self, d=False):
        self.clear_items()
        options = []
        for i in self.lootboxes[:10]:
            options.append(
                discord.SelectOption(
                    label=i.lootbox.name,
                    value=str(i.id),
                    emoji=i.lootbox.emoji
                )
            )

        plbox_s = discord.ui.Select(placeholder="Select the lootbox you want to open:", options=options, disabled=d==True)
        plbox_s.callback = self.sc
        ol = discord.ui.Button(style=discord.ButtonStyle.success, label="Open Lootbox")
        ol.callback = self.ol

        container1 = discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay(content="# Open a Lootbox"),
                discord.ui.TextDisplay(content="-# Made by unitedstatesoferland/Gruyere"),
                accessory=discord.ui.Thumbnail(
                    media=self.bot.user.display_avatar.url,
                ),
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
            discord.ui.ActionRow(plbox_s),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.large),
            discord.ui.TextDisplay(content=f"## Selected lootbox:\n{self.lootboxes[self.selected].lootbox.name} #{self.lootboxes[self.selected].id}"),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.large),
            discord.ui.ActionRow(ol),
        )
        self.add_item(container1)
    async def sc(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            await interaction.response.send_message("This aint your menu sonion", ephemeral=True)
            return
        si = interaction.data["values"][0]

        for i, lootbox in enumerate(self.lootboxes):
            if str(lootbox.id) == si:
                self.selected = i
                break
        self.view()

        await interaction.response.edit_message(view=self)
    async def ol(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            await interaction.response.send_message("This aint your menu sonion", ephemeral=True)
            return
        self.clear_items()

        lootbox = self.lootboxes[self.selected].lootbox.name
        if random.randint(0, 100) <= self.lootboxes[self.selected].lootbox.special_chance:
            self.special = await get_random_special()
        else:
            self.special = None
        if not self.special:
            container1 = discord.ui.Container(
                discord.ui.TextDisplay(content=f"# Opened lootbox:\n{lootbox}"),
                discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.large),
                discord.ui.TextDisplay(content=f"🎉From this lootbox, you got **{self.ball}**🎉"),
            )
        else:
            container1 = discord.ui.Container(
                discord.ui.TextDisplay(content=f"# Opened lootbox:\n{lootbox}"),
                discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.large),
                discord.ui.TextDisplay(content=f"🎉From this lootbox, you got {self.special.emoji} **{self.ball}**🎉"),
            )
        player = await Player.objects.aget_or_none(discord_id=interaction.user.id)
        self.add_item(container1)
        await BallInstance.objects.acreate(
            ball=self.ball,
            player=player,
            attack_bonus=random.randint(-20, 20),
            health_bonus=random.randint(-20, 20),
            special=self.special
        )
        await self.lootboxes[self.selected].adelete()
        await interaction.response.edit_message(view=self)
class Lootboxes(commands.Cog):
    '''
    Lootbox commands
    '''
    def __init__(
        self,
        bot: "BallsDexBot",
    ):
        self.bot = bot
        self.bias = 1
        self.economy: bool = False
        self.ball_price = 0
        self.economy_price = 0
        self.min_rarity = 0.0
    
    lootboxes = app_commands.Group(name="lootbox", description="Lootbox commands")

    async def get_settings(self):
        settings_obj = await sync_to_async(LootSettings.objects.first)()

        if not settings_obj:
            print("no lootbox settings found... Somehow")
            return

        self.bias = settings_obj.rig_multiplier
        self.ball_price = settings_obj.ball_instance_price
        self.economy_price = settings_obj.economy_price
        self.economy = settings_obj.economy
        self.min_rarity = settings_obj.min_rarity


    @lootboxes.command(name="purchase", description='Purchase a lootbox')
    @app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)
    async def purchase(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        await self.get_settings()
        player = await Player.objects.aget_or_none(discord_id=interaction.user.id)
        if self.economy == False:
            lootboxes = await sync_to_async(lambda:list(
                Lootbox.objects.annotate(
                    price=F("price_multiplier") * self.ball_price
                ).order_by("price")
            ))()
            view = Purchase(self.bot, interaction, lootboxes, self.ball_price, self.economy)
        else:
            lootboxes = await sync_to_async(lambda:list(
                Lootbox.objects.annotate(
                    price=F("price_multiplier") * self.economy_price
                ).order_by("price")
            ))()
            view = Purchase(self.bot, interaction, lootboxes, self.economy_price, self.economy)
        m = await interaction.followup.send(view=view)
        view.m = m
    @lootboxes.command(name="gift", description='Gift someone a lootbox')
    @app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)
    @app_commands.describe(user="The user you want to gift the lootbox to")
    async def purchase(self, interaction: discord.Interaction, user:discord.User):
        await interaction.response.defer(thinking=True)
        await self.get_settings()
        player = await Player.objects.aget_or_none(discord_id=interaction.user.id)
        player2 = await Player.objects.aget_or_none(discord_id=user.id)

        if user.bot:
            await interaction.followup.send("You cannot gift to bots.", ephemeral=True)
            return

        if user == interaction.user:
            await interaction.followup.send("You cant gift a lootbox to yourself.", ephemeral=True)
            return
        if self.economy == False:
            lootboxes = await sync_to_async(lambda:list(
                Lootbox.objects.annotate(
                    price=F("price_multiplier") * self.ball_price
                ).order_by("price")
            ))()
            view = Gift(self.bot, interaction, lootboxes, self.ball_price, self.economy, user)
        else:
            lootboxes = await sync_to_async(lambda:list(
                Lootbox.objects.annotate(
                    price=F("price_multiplier") * self.economy_price
                ).order_by("price")
            ))()
            view = Gift(self.bot, interaction, lootboxes, self.economy_price, self.economy, user)
        m = await interaction.followup.send(view=view)
        view.m = m
        

    @lootboxes.command(name="open", description='Opens a lootbox that you own')
    async def open(self, interaction: discord.Interaction):
        await interaction.response.defer()
        player = await Player.objects.aget_or_none(discord_id=interaction.user.id)
        playerlootboxes = await sync_to_async(list)(
            PlayerLootbox.objects.filter(player=player).select_related("lootbox")
        )

        if not playerlootboxes:
            await interaction.followup.send(content="You dont have any lootboxes", ephemeral=True)
            return

        ball = await get_random_ball(self)
        view = Open(self.bot, interaction, playerlootboxes, ball,)


        await interaction.followup.send(view=view, content=" ")



async def get_random_ball(cog):
    bias = cog.bias
    all_balls = await sync_to_async(list)(Ball.objects.filter(enabled=True))
    if not all_balls:
        return None
    weights = []
    for ball in all_balls:
        weight = ball.rarity
        if ball.rarity >= cog.min_rarity:
            weight *= bias
        weights.append(weight)

    rigged_i_mean_totally_normal_ball = random.choices(all_balls, weights=weights, k=1)[0]
    return rigged_i_mean_totally_normal_ball


async def get_random_special():
    all_specials = await sync_to_async(list)(Special.objects.filter(hidden=False))
    if not all_specials:
        return None
    weights = []
    for special in all_specials:
        weight = special.rarity
        weights.append(weight)

    special_that_will_get_applied = random.choices(all_specials, weights=weights, k=1)[0]


    return special_that_will_get_applied

async def get_random(interaction: discord.Interaction, amount: int):
    player = await Player.objects.aget_or_none(discord_id=interaction.user.id)
    if not player:
        return []

    all_balls = await sync_to_async(list)(
        BallInstance.objects.filter(player=player, deleted=False, special_id=None)
    )

    if len(all_balls) < amount:
        return []

    selected = random.sample(all_balls, amount)
    print(selected)
    return selected



