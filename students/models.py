from django.db import models


class Student(models.Model):
    """
    Student model representing transport passenger.
    GAP 1 RESOLUTION: van is directly linked as FK alongside route.
    """
    admission_number = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    program = models.CharField(max_length=100, help_text="e.g. BSIT, BSCS, BBA")
    semester = models.CharField(max_length=20, help_text="e.g. 1st, 2nd, 5th")
    phone = models.CharField(max_length=20, blank=True, default='')

    # Route and Van assignment
    route = models.ForeignKey(
        'transport.Route',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    van = models.ForeignKey(
        'transport.Van',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.admission_number} - {self.name}"

    @property
    def has_active_transport(self):
        return self.is_active and bool(self.route and self.van)
