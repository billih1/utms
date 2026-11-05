from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with role-based access control for UTMS."""
    class Role(models.TextChoices):
        ADMIN = 'Admin', 'Admin'
        ACCOUNTANT = 'Accountant', 'Accountant'
        DRIVER = 'Driver', 'Driver'
        STUDENT = 'Student', 'Student'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text="User system role"
    )
    linked_student_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Primary key of linked students.Student for Student role"
    )
    linked_driver_info = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Driver name / vehicle info for Driver role"
    )
    phone = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_accountant(self):
        return self.role == self.Role.ACCOUNTANT or self.is_admin_role

    @property
    def is_driver(self):
        return self.role == self.Role.DRIVER

    @property
    def is_student_role(self):
        return self.role == self.Role.STUDENT
