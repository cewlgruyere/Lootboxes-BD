from django.contrib import admin
from django.utils.safestring import mark_safe
# Register your models here.
from .models import LootSettings, Lootbox, PlayerLootbox
import re
from django.urls import reverse
from django.shortcuts import redirect

dc_emoji_regex_i_think = r"^\d{17,20}$"

@admin.register(Lootbox)
class LootboxAdmin(admin.ModelAdmin):
    list_display = ("name", "price_multiplier", "lootbox_emoji",)
    search_fields = ("name", "price_multiplier",)

    @admin.display(description="Emoji")
    def lootbox_emoji(self, obj: Lootbox):
        value = obj.emoji
        if re.match(dc_emoji_regex_i_think, value):
            return mark_safe(
                f'<img src="https://cdn.discordapp.com/emojis/{value}.png?size=40" '
                f'title="ID: {value}" />'
            )

        return value



@admin.register(LootSettings)
class LootSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Lootbox Settings", {
            "fields": (
                "economy",
                "rig_multiplier",
                "ball_instance_price",
                "min_rarity",
                "economy_price",
            ),
            "description": "Change lootbox settings here :3",
        }),
    )

    def has_add_permission(self, request):
        return not LootSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        if LootSettings.objects.exists():
            obj = LootSettings.objects.first()
            url = reverse(
                "admin:lootboxes_lootsettings_change",
                args=[obj.id]
            )
            return redirect(url)
        return super().changelist_view(request, extra_context)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            if obj.economy:
                readonly_fields += ("ball_instance_price",)
            else:
                readonly_fields += ("economy_price",)

        return readonly_fields

@admin.register(PlayerLootbox)
class PlayerLootboxAdmin(admin.ModelAdmin):
    list_display = ("player", "lootbox",)
    list_display_links = ("player", "lootbox")
    search_fields = ("player__discord_id", "lootbox__name")
