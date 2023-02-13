from django.contrib import admin

from users import models


# Register your models here.
@admin.register(models.BlackjackUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'balance')
