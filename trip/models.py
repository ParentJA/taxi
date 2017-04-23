# Standard library imports.
import datetime
import hashlib

# Django imports.
from django.conf import settings
from django.db import models
from django.shortcuts import reverse


class Trip(models.Model):
    REQUESTED = 'REQUESTED'
    STARTED = 'STARTED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    TRIP_STATUSES = (
        (REQUESTED, REQUESTED),
        (STARTED, STARTED),
        (IN_PROGRESS, IN_PROGRESS),
        (COMPLETED, COMPLETED),
    )

    nk = models.CharField(max_length=32, unique=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    pick_up_address = models.CharField(max_length=255)
    drop_off_address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=TRIP_STATUSES, default=REQUESTED)
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='trips_as_driver')
    riders = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='trips_as_rider')

    def save(self, **kwargs):
        if not self.nk:
            secure_hash = hashlib.md5()
            secure_hash.update('{now}:{pick_up_address}:{drop_off_address}'.format(
                now=datetime.datetime.now(),
                pick_up_address=self.pick_up_address,
                drop_off_address=self.drop_off_address
            ).encode('utf-8'))
            self.nk = secure_hash.hexdigest()
        super().save(**kwargs)

    def get_absolute_url(self):
        return reverse('trip:trip_detail', kwargs={'trip_nk': self.nk})
