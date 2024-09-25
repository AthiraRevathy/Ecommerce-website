
from decimal import Decimal
import random
import string
from django.conf import settings
from django.db import models
from product_cart.models import Order
from django.contrib.auth.models import User



class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f'{self.user.username} Wallet'


# Create your models here.
class WalletTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=(('Credit', 'Credit'), ('Debit', 'Debit')))
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    def __str__(self):
        return f'{self.transaction_type} - {self.amount} for {self.user.email}'
    

class ReturnRequest(models.Model):
    STATUS_CHOICES = (
        ('Requested', 'Requested'),
        ('Confirmed', 'Confirmed'),
        ('Rejected', 'Rejected'),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='return_request')
    
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Requested')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Return Request for Order {self.order.order_number}'
    
     
class CancellationRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Rejected', 'Rejected'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    admin_comment = models.TextField(blank=False, null=False)
    reason = models.CharField(max_length=255, null=True, blank=True)  # Ensure this line is present 

    def __str__(self):
        return f"Cancellation Request for Order {self.order.order_number} - {self.status}"
    

class Referral(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    referral_code = models.CharField(max_length=50, unique=True)
    referred_friends = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='referred_by', blank=True)
    referral_discount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('50.00'))
    

    def __str__(self):
        return f"{self.user.username}'s Referral Code: {self.referral_code}"
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        # Ensure the referral code is unique
        while True:
            # Get the first 4 characters of the username (or any identifier)
            username_part = self.user.username[:4].upper()
            # Generate a 4-digit random number
            random_part = ''.join(random.choices(string.digits, k=4))
            # Combine parts
            code = f"{username_part}{random_part}"
            if not Referral.objects.filter(referral_code=code).exists():
                return code