from django.forms import inlineformset_factory
from .models import Product, ProductImage
from .forms import ProductImageForm

# Define the formset for ProductImage
ProductImageFormset = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=3,  # Number of empty forms to display
    can_delete=True  # Allow deleting forms
)
