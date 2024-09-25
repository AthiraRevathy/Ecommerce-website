from django import forms
from django.forms import modelformset_factory
from .models import Product, ProductImage, Category, Size, Color, Brand

class ProductForm(forms.ModelForm):
    sizes = forms.ModelMultipleChoiceField(
        queryset=Size.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    colors = forms.ModelMultipleChoiceField(
        queryset=Color.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        widget=forms.Select,
        required=False
    )
    discount_percentage = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        help_text="Discount percentage"
    )
    minimum_stock_level = forms.IntegerField(
        required=False,
        min_value=0,
        help_text="Minimum stock level before alert"
    )
    
    class Meta:
        model = Product
        exclude = ['created_by']  # Exclude 'created_by' if it's not to be filled manually
        fields = [
            'title', 'description', 'category', 'original_price', 'product_image',
            'quantity', 'trending', 'availability_status','product_offer',
            'sizes', 'colors', 'is_featured', 'brand',
            'discount_percentage', 'minimum_stock_level'
        ]

    def clean_original_price(self):
        original_price = self.cleaned_data.get('original_price')
        if original_price < 0:
            raise forms.ValidationError("Original price cannot be negative.")
        return original_price

    def clean_product_offer(self):
        product_offer = self.cleaned_data.get('product_offer')
        if product_offer < 0 or product_offer >= 100:
            raise forms.ValidationError("Product offer must be between 0 and 100 percent.")
        return product_offer


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name','category_offer' ,'is_active',]

    def clean_category_offer(self):
        category_offer = self.cleaned_data.get('category_offer')
        if category_offer < 0 or category_offer >= 100:
            raise forms.ValidationError("Category offer must be between 0 and 100 percent.")
        return category_offer

class SizeForm(forms.ModelForm):
    class Meta:
        model = Size
        fields = ['size_name']

class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ['color_name']

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'is_main']
        widgets = {
            'is_main': forms.CheckboxInput(),
        }
    
        
class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['brand_name','brand_offer', 'is_active']

ProductImageFormset = modelformset_factory(
    ProductImage,
    form=ProductImageForm,
    extra=3,  # Number of additional empty forms to display
    max_num=3,  # Limit the total number of forms to 3
    min_num=3,  # Ensure at least 3 forms are submitted
    validate_min=True  # Enforce the minimum number of forms
)

def clean_brand_offer(self):
        brand_offer = self.cleaned_data.get('brand_offer')
        if brand_offer < 0 or brand_offer >= 100:
            raise forms.ValidationError("Brand offer must be between 0 and 100 percent.")
        return brand_offer