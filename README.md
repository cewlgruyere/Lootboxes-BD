# Ballsdex lootboxes  

> [!NOTE]
> This probably has a lot of bugs, since im not really used to components v2 (and im not the best programmer either). Install with caution, because a lot of balls can get wiped.

> [!IMPORTANT]
> This package is no longer worked on. Feel free to fork it, or contribute to this branch. the last thing will be the V2 version, soon available on the V2 Branch

## Introduction:  
This is a BallsDex extension originally designed for the ReMicroDex april fools event. It has been modified, making it easier and better to use, Users can purchase lootboxes by sacrificing collectibles, or currency; if the owners enabled it. Most settings are changeable within the admin panel, and you, the owner of the instance can even add custom lootboxes in the panel with customizable price, etc. You can also rig it so it only gives common balls, but thats besides the point.
  
## Installation
1. Put this into `config/extra.toml`
   ```toml
   [[ballsdex.packages]]
   location = "git+https://github.com/cewlgruyere/Lootboxes-BD.git"
   path = "lootboxes"
   enabled = true
   ```
2. Rebuild the bot.
   do:  
   ```
   docker compose down
   docker compose build
   docker compose up
   ```
  
## Functionalities:
### Commands:
  - `/lootbox purchase`: Purchase a lootbox for the amount of currency/collectibles you have set in the admin panel.
  - `/lootbox give`: You dont give, but purchase for someone else.
  - `/lootbox open`: Opens a lootbox.
### Admin Panel:
  - Settings: You can modify the rig multiplier, base price (in both collectibles and currency, separately)
  - Playerlootboxes: modify the lootboxes that a player has.
  - lootboxes: Create new lootboxes.
