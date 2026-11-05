from django.db import models


class Route(models.Model):
    """Transport route with fixed monthly rent."""
    route_name = models.CharField(max_length=200, unique=True)
    rent = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monthly rent in PKR")
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['route_name']

    def __str__(self):
        return f"{self.route_name} (Rs. {self.rent:,.0f})"

    @property
    def total_vans(self):
        return self.vans.count()

    @property
    def total_students(self):
        return self.students.filter(is_active=True).count()


class Van(models.Model):
    """Van / vehicle with fixed seat capacity (typically 20-22)."""
    van_number = models.CharField(max_length=50, unique=True, help_text="Vehicle registration number e.g. LEA-101")
    capacity = models.PositiveIntegerField(default=22, help_text="Seat capacity (typically 20-22)")
    route = models.ForeignKey(
        Route,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vans',
        help_text="Assigned route. Leave empty for Spare vehicle."
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['van_number']

    def __str__(self):
        route_text = self.route.route_name if self.route else "Spare Vehicle"
        return f"{self.van_number} ({route_text})"

    @property
    def filled_seats(self):
        return self.students.filter(is_active=True).count()

    @property
    def available_seats(self):
        return max(0, self.capacity - self.filled_seats)

    @property
    def is_full(self):
        return self.filled_seats >= self.capacity

    @property
    def is_spare(self):
        return self.route is None
