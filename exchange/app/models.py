from django.db import models
from django.contrib.auth.models import User
from djongo.models.fields import ObjectIdField


class Profile(models.Model):
    _id = ObjectIdField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    BTC = models.FloatField(default=0)
    fiatMoney = models.FloatField(default=0)
    profit = models.FloatField(default=0)


class Order(models.Model):
    _id = ObjectIdField()
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=50)
    complete = models.BooleanField(default=False)
    price = models.FloatField(default=0)
    quantity = models.FloatField(default=0)
