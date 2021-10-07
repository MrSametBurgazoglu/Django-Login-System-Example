from django.contrib.sessions.models import Session
from django.db import models
from django.contrib.auth.models import User


class UserModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True)
    activation_code = models.IntegerField(blank=True)
    is_activated = models.BooleanField(default=False)
    date = models.TimeField(auto_now=True)

    def __str__(self):
        return self.user.get_username()


class DayLoginCompleteTime(models.Model):
    day = models.DateField(null=True)
    user_count = models.IntegerField(default=1)
    average = models.BigIntegerField(default=0)


class LoginTime(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    beginning_time = models.TimeField()
    finish_time = models.TimeField(null=True)
# Create your models here.
