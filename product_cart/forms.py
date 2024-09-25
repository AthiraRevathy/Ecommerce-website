from django import forms
from .models import Address, Order, OrderItem, Cart, CartItem, Wishlist, Coupon
from products.models import Product, Size
from django.contrib.auth.models import User

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'street_address', 'city', 'state', 'postal_code', 'country', 'is_default']
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'user',
            'order_notes',
            'total',
            'status',
            'shipping_fee',
            'address',
            'payment_method',
            'grand_total',
            'payment_status',
            'payment_id',
            'wallet_credit',
            'coupon'
        ]


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['order', 'product', 'quantity', 'total_price']

class CartForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ['user']

class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['cart', 'product', 'size', 'color_code', 'quantity', 'ordered']

class WishlistForm(forms.ModelForm):
    class Meta:
        model = Wishlist
        fields = ['user', 'product']




class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['user', 'order_notes', 'total', 'status', 'shipping_fee', 'address', 'payment_method', 'grand_total', 'payment_status', 'payment_id', 'wallet_credit', 'coupon']
    
    # You can also add custom validation or methods if needed

    def clean(self):
        cleaned_data = super().clean()
        # Add any custom validation here
        return cleaned_data
    
class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'name', 'discount', 'valid_from', 'valid_to']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valid_from'].widget = forms.SelectDateWidget(years=range(2000, 2031))
        self.fields['valid_to'].widget = forms.SelectDateWidget(years=range(2000, 2031))