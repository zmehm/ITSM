# accounts/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Employee

# Get the custom user model you are using (e.g., CustomUser)
User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_employee(sender, instance, created, **kwargs):
    # 'created' is True if a new record was just made
    if created:
        # Check if an Employee record already exists before creating
        if not hasattr(instance, 'employee'):
            Employee.objects.create(user=instance)