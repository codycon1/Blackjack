from django.contrib.auth.forms import UserCreationForm

from users import models


class BlackjackUserCreationForm(UserCreationForm):
    class Meta:
        model = models.BlackjackUser
        fields = ('username',)