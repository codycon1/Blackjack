from django.contrib import admin

from game.models import *


# Register your models here.
@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('tableID', 'pot', 'status',)


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('cardID', 'userID', 'suit', 'rank', 'img', 'dealt')
