from django.contrib import admin
from .models import Product, Category, Size, Color, ProductImage, Brand

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'color', 'is_main')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'original_price','product_offer', 'is_new', 'is_popular', 'discount_percentage',
        'get_discounted_price', 'in_stock', 'trending', 'brand',
        'created_at', 'updated_at'
    )
    list_filter = ('category', 'in_stock', 'trending', 'discount_percentage', 'brand')
    search_fields = ('title', 'category__category_name', 'brand__brand_name')

    fields = (
        'title', 'category', 'original_price', 'is_new', 'is_popular', 'discount_percentage',
        'in_stock', 'trending', 'brand', 'description', 'quantity', 'availability_status', 'is_featured',
        'sizes', 'colors'
    )
    inlines = [ProductImageInline]

    def get_discounted_price(self, obj):
        return obj.discounted_price
    get_discounted_price.short_description = 'Discounted Price'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name','category_offer','is_active')
    search_fields = ('category_name',)
    list_filter = ('is_active',)

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('size_name',)
    search_fields = ('size_name',)

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('color_name', 'color_code')

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'is_main')
    list_filter = ('color',)

class BrandAdmin(admin.ModelAdmin):
    list_display = ('brand_name','brand_offer', 'is_active')
    search_fields = ('brand_name',)
    list_filter = ('is_active',)
    filter_horizontal =()

      

admin.site.register(Brand, BrandAdmin)