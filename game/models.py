from django.db import models
from users import models as user_model


# Create your models here.

class Table(models.Model):
    tableID = models.AutoField(primary_key=True)
    pot = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.IntegerField(default=0)
    singleplayerID = models.ForeignKey(user_model.BlackjackUser, on_delete=models.CASCADE, null=True)


class Card(models.Model):
    cardID = models.AutoField(primary_key=True)
    userID = models.ForeignKey(user_model.BlackjackUser, on_delete=models.CASCADE, null=True, default=None)
    suit = models.IntegerField()
    rank = models.IntegerField()
    img = models.URLField(max_length=100)
    dealt = models.BooleanField(default=False)
    tableID = models.ForeignKey(Table, on_delete=models.CASCADE)
