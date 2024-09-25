from django.contrib import admin
from .models import Address, Order, OrderItem, Cart, CartItem, Wishlist, Coupon
from products.models import Product, Size
from django.utils import timezone
class AddressAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone_number', 'email', 'street_address', 'city', 'state', 'postal_code', 'country', 'is_default', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone_number', 'email', 'street_address', 'city', 'state', 'postal_code', 'country')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'order_date', 'total', 'status', 'payment_status', 'grand_total', 'payment_id', 'wallet_credit', 'coupon')
    list_filter = ('status', 'payment_status', 'order_date')
    search_fields = ('order_number', 'user__username', 'user__email', 'payment_id')

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'total_price')
    search_fields = ('order__order_number', 'product__title')

class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username',)

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'size', 'color_code', 'quantity', 'ordered')
    search_fields = ('cart__user__username', 'product__title', 'size__size_name', 'color_code')

class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    search_fields = ('user__username', 'product__title')



class CouponAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'discount', 'valid_from', 'valid_to', 'status')
    list_filter = ('status', 'valid_from', 'valid_to')
    search_fields = ('name', 'code')
    ordering = ('-valid_to',)  # Order by expiration date in descending order

    def save_model(self, request, obj, form, change):
        # Automatically set the status before saving
        today = timezone.now().date()
        if obj.valid_from <= today <= obj.valid_to:
            obj.status = 'active'
        elif today < obj.valid_from:
            obj.status = 'inactive'
        else:
            obj.status = 'expired'
        super().save_model(request, obj, form, change)

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Optionally remove some actions or add custom actions here
        return actions

admin.site.register(Coupon, CouponAdmin)




admin.site.register(Address, AddressAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Wishlist, WishlistAdmin)

