from django.contrib import admin

from game.models import *


# Register your models here.
@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('tableID', 'status', 'mp_status')

@admin.register(PlayerTracker)
class PlayerTrackerAdmin(admin.ModelAdmin):
    list_display = ('playerID', 'tableID', 'status', 'split_status', 'json_cache')

@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ('tableID', 'playerID', 'amount', 'amount_split')


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('cardID', 'playerID', 'suit', 'rank', 'img', 'dealt', 'dealer', 'hidden', 'split', 'tableID')
