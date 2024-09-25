# store/models.py
# store/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.contrib.sites.models import Site
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add additional fields if needed
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.username

class OTPVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Automate the profile thing
post_save.connect(create_profile, sender=User)

class SocialApp(models.Model):
    provider = models.CharField(max_length=30)
    name = models.CharField(max_length=40)
    client_id = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)
    
    class Meta:
        unique_together = ('provider', 'name')


class AccountManager(BaseUserManager):
    def create_user(self, username, email, password=None, first_name='', last_name='', phone_number='', **extra_fields):
        if not email:
            raise ValueError("User must have an email")
        if not username:
            raise ValueError("User must have a username")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, first_name=first_name, last_name=last_name, phone_number=phone_number, **extra_fields)

        user.is_active = True
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, first_name='', last_name='', phone_number=''):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
    


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username} - {self.token}"
    
    def is_valid(self):
        # Define token validity period (e.g., 1 hour)
        return (timezone.now() - self.created_at).total_seconds() < 3600
