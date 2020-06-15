from django.db import models


class Service(models.Model):
    class Meta:
        db_table = 'service'

    id = models.AutoField(primary_key=True)
    room_id = models.IntegerField()
    request_time = models.DateTimeField()
    finish_time = models.DateTimeField()
    request_duration = models.DecimalField(max_digits=20, decimal_places=1)
    fan_speed = models.IntegerField()
    fee_rate = models.DecimalField(max_digits=3, decimal_places=1)
    fee = models.DecimalField(max_digits=10, decimal_places=2)


