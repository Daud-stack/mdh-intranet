from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=100, blank=True)
    avatar = models.FileField(upload_to='avatars/', blank=True)
    
    # HR Fields
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    join_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True)
    employment_status = models.CharField(max_length=20, choices=[
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERN', 'Intern'),
    ], default='FULL_TIME')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.employee_id or 'No ID'})"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Removed redundant save signal to prevent interference with manual profile updates
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Pass since we handle profile saving explicitly in views to avoid race conditions
    pass
