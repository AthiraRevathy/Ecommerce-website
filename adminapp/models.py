from django.contrib.auth.models import AbstractUser, UserManager, Group, Permission
from django.db import models
import uuid

class MyAccountManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Account(AbstractUser):
    username = None  # Disable username field
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is the only required field

    objects = MyAccountManager()

    # Add unique related_name attributes
    groups = models.ManyToManyField(Group, related_name='account_groups', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='account_permissions', blank=True)

    def __str__(self):
        return self.email
