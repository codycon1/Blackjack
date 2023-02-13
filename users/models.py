from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class BlackjackUser(AbstractUser):
    balance = models.DecimalField(default=500, max_digits=10, decimal_places=2)
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username
