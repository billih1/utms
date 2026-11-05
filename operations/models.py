from django.db import models
from django.conf import settings


class VehicleLog(models.Model):
    """
    FR-20 / UC-17 / UC-18: Vehicle entry/exit log maintained by drivers and viewed by Admin.
    """
    class TripStatus(models.TextChoices):
        SCHEDULED = 'Scheduled', 'Scheduled'
        DEPARTED = 'Departed', 'Departed'
        ON_ROUTE = 'On Route', 'On Route'
        ARRIVED = 'Arrived', 'Arrived'
        OFF = 'Off', 'Off'

    van = models.ForeignKey(
        'transport.Van',
        on_delete=models.CASCADE,
        related_name='logs'
    )
    route = models.ForeignKey(
        'transport.Route',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs'
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vehicle_logs'
    )
    departure_time = models.TimeField(null=True, blank=True)
    arrival_time = models.TimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=TripStatus.choices,
        default=TripStatus.SCHEDULED
    )
    date = models.DateField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.van.van_number} - {self.date} - {self.status}"
