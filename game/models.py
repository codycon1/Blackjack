from django.db import models
from users import models as user_model


# Create your models here.

class Table(models.Model):
    tableID = models.AutoField(primary_key=True)
    status = models.IntegerField(default=0)
    players = models.ManyToManyField(user_model.BlackjackUser)


class PlayerTracker(models.Model):
    playerID = models.ForeignKey(user_model.BlackjackUser, on_delete=models.CASCADE, null=False)
    tableID = models.ForeignKey(Table, on_delete=models.CASCADE, null=False)
    status = models.IntegerField(default=0)
    split_status = models.IntegerField(default=None, null=True)
    json_cache = models.JSONField(null=True)


class Bet(models.Model):
    tableID = models.ForeignKey(Table, on_delete=models.CASCADE, null=False)
    playerID = models.ForeignKey(user_model.BlackjackUser, on_delete=models.CASCADE, null=False)
    amount = models.IntegerField(default=0, null=False)
    amount_split = models.IntegerField(default=0, null=False)


class Card(models.Model):
    cardID = models.AutoField(primary_key=True)
    playerID = models.ForeignKey(user_model.BlackjackUser, on_delete=models.CASCADE, null=True, default=None)
    suit = models.IntegerField()
    rank = models.IntegerField()
    img = models.URLField(max_length=100)
    dealt = models.BooleanField(default=False)
    dealer = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    split = models.BooleanField(default=False)
    tableID = models.ForeignKey(Table, on_delete=models.CASCADE)
