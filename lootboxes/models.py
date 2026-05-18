from django.db import models
from bd_models.models import Player
# Create your models here.

class LootSettings(models.Model):
    economy = models.BooleanField(help_text="Enables economy settings")
    ball_instance_price = models.IntegerField(default=1, help_text="How many balls get sacrificed for a lootbox")
    economy_price = models.IntegerField(default=100, help_text="How much money gets used to obtain a lootbox")
    min_rarity = models.FloatField(default=3.0, help_text="The default rarity where if the collectibles rarity is above then the rig multiplier will apply.")
    rig_multiplier = models.IntegerField(default=1, help_text="The bias towards common balls")
    class Meta:
        verbose_name_plural = "Lootbox Settings"
        verbose_name = "Lootbox Setting"

class Lootbox(models.Model):

    name = models.CharField(default=None, help_text="The name of the lootbox")
    price_multiplier = models.IntegerField(default=1, help_text="The price multiplier for this lootbox; eg. tiers.")
    special_chance = models.IntegerField(help_text="Chance in percentage to get a special", default=2)
    emoji = models.CharField(default="🎁", help_text="The emoji for the lootbox.", max_length=50)

    class Meta:
        verbose_name_plural = "Lootboxes"
        verbose_name = "Lootbox"
    def __str__(self):
        return self.name

class PlayerLootbox(models.Model):
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="player_lootbox"
    )
    lootbox = models.ForeignKey(
        Lootbox,
        on_delete=models.CASCADE,
        related_name="player_lootbox"
    )
    class Meta:
        verbose_name_plural = "Player Lootboxes"
        verbose_name = "Player Lootbox"

