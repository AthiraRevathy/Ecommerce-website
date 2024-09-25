from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms import ValidationError

class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)
    is_active = models.BooleanField(default=True)
    category_offer = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, )

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.category_name

class Size(models.Model):
    size_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.size_name

class Color(models.Model):
    color_name = models.CharField(max_length=50, unique=True)
    color_code = models.CharField(max_length=7)
    image = models.ImageField(upload_to='colors/', blank=True, null=True)  # Image associated with the color  # Hex color code including '#'

    def __str__(self):
        return self.color_name

    

class Brand(models.Model):
    brand_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    brand_offer = models.DecimalField(max_digits=5, decimal_places=2, default=0.00,)
    
    def __str__(self):
        return self.brand_name

class Product(models.Model):
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    AVAILABILITY_CHOICES = [
        ('in_stock', _('In Stock')),
        ('out_of_stock', _('Out of Stock')),
    ]

    title = models.CharField(max_length=100)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_new = models.BooleanField(default=False)
    is_popular = models.BooleanField(default=False)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # This is optional
    category = models.ForeignKey('Category', related_name='products', on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    brand = models.ForeignKey('Brand', related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    in_stock = models.BooleanField(default=True)
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='in_stock')
    trending = models.BooleanField(default=False, help_text=_('0=default, 1=Hidden'))
    is_featured = models.BooleanField(default=False, help_text=_('Is this product featured?'))
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    product_image = models.ImageField(upload_to='photos/products', verbose_name=_("Product Image"), default='photos/products/default_product_image.jpg')
    sizes = models.ManyToManyField('Size', related_name='products')
    colors = models.ManyToManyField('Color', related_name='products')
    product_offer = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text=_('Discount percentage applied to the product'))


    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_main_image_url(self):
        if self.product_image:
            return self.product_image.url
        return ''  # Return default image URL if needed
    


    @property
    def discounted_price(self):
        """Calculate the discounted price based on the best available offer."""
        best_offer_percentage = self.get_best_offer()
        if best_offer_percentage:
            return self.original_price * (1 - (best_offer_percentage / 100))
        return self.original_price
    
    def get_best_offer(self):
        
        category_offer = self.category.category_offer if self.category else 0
        brand_offer = self.brand.brand_offer if self.brand else 0
        offers = {
            'product_offer': self.product_offer,
            'category_offer': category_offer,
            'brand_offer': brand_offer
        }
        best_offer_type = max(offers, key=offers.get)
        best_offer_percentage = offers[best_offer_type]
        return best_offer_percentage

    @property
    def main_image(self):
        return self.product_image.url if self.product_image else None

    def save(self, *args, **kwargs):
        if self.quantity == 0:
            self.availability_status = 'out_of_stock'
        elif self.quantity == 1:
            self.availability_status = 'in_stock'
        if self.original_price < 0:
            raise ValidationError("Original price cannot be negative.")
        if self.product_offer < 0 or self.product_offer > 100:
            raise ValidationError("Product offer must be between 0 and 100 percent.")
        super(Product, self).save(*args, **kwargs)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='photos/products')
    is_main = models.BooleanField(default=False)
    color = models.ForeignKey(Color, related_name='product_images', on_delete=models.SET_NULL, null=True, blank=True)

    


class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(default='No content provided')
    rating = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(5.0)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.title}"
    
