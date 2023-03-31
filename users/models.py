from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class BlackjackUser(AbstractUser):
    balance = models.IntegerField(default=500)
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username
