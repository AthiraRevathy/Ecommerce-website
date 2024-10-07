from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid
from products.models import Product, Size

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(max_length=255, blank=True, null=True)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.street_address}, {self.city}, {self.state}, {self.country}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('Ordered', 'Ordered'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Returned', 'Returned'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Refunded', 'Refunded'),
        ('Failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order_date = models.DateTimeField(auto_now_add=True)
    order_notes = models.TextField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ordered')
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)

    payment_method = models.CharField(max_length=20)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_id = models.CharField(max_length=255, blank=True, null=True)
    wallet_credit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    coupon = models.ForeignKey('Coupon', null=True, blank=True, on_delete=models.SET_NULL)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
   
    def __str__(self):
         return f"Order {self.order_number} - Discount: {self.discount_amount:.2f}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    #is_ordered = models.BooleanField(default=False) 

    def __str__(self):
        return f'{self.product.title} - {self.quantity}'

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    color_code = models.CharField(max_length=7)  # Assuming hex color code
    quantity = models.PositiveIntegerField(default=1)
    ordered = models.BooleanField(default=False)  # Track if the item has been ordered
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Add this line

    def __str__(self):
        return f"{self.product.title} ({self.size.size_name})"

    @property
    def total_price(self):
        return Decimal(self.product.original_price) * Decimal(self.quantity)
    
    
class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, default=None)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_at']  # Optionally, order by the most recent items first

    def __str__(self):
        return f"Wishlist item for {self.user} - Product ID: {self.product_id}"

class Coupon(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    ]

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateField()
    valid_to = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return self.code

    
    def update_status(self):
        today = timezone.now().date()
        print(f"Today's date: {today}")
        print(f"Valid from: {self.valid_from}")
        print(f"Valid to: {self.valid_to}")
        if self.valid_from <= today <= self.valid_to:
            self.status = 'active'
        elif today < self.valid_from:
            self.status = 'inactive'
        else:
            self.status = 'expired'
        print(f"Updated status: {self.status}")  # Deb
        self.save()

    def is_valid(self):
        # Ensure status is up-to-date
        self.update_status()
        return self.status == 'active'