from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class UsedCar(models.Model):
    url = models.URLField(unique=True, db_index=True)
    title = models.CharField()
    price_usd = models.PositiveIntegerField()
    odometer = models.PositiveIntegerField()
    username = models.CharField()
    phone_number = PhoneNumberField(region='UA', max_length=13)
    image_url = models.JSONField(null=True, blank=True)
    images_count = models.PositiveSmallIntegerField(null=True, blank=True)
    car_number = models.CharField(null=True, blank=True)
    car_vin = models.CharField(null=True, blank=True)
    datetime_found = models.DateTimeField(auto_now=True)
