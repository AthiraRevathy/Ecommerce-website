from django.shortcuts import render, redirect, get_object_or_404,reverse
from django.contrib import messages
from .models import Product, Size, Category, Brand, Color, ProductImage,Review
from .forms import ProductForm, CategoryForm, SizeForm, ColorForm, BrandForm, ProductImageForm
from .formsets import ProductImageFormset
from django.http import HttpResponse
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from .models import Product, Brand, Category, Color, Size
from .forms import BrandForm




@login_required
def product_home(request):
    # Get filter and sort parameters from GET request
    category_id = request.GET.get('category', 'unapplied')
    brand_name = request.GET.get('brand', 'unapplied')
    color_name = request.GET.get('color', 'unapplied')
    size_name = request.GET.get('size', 'unapplied')
    sort_by = request.GET.get('sort', 'popularity')  # Default sort by popularity

    # Initialize product queryset
    products = Product.objects.all()

    # Apply filters
    if category_id != 'unapplied':
        products = products.filter(category_id=category_id)
    if brand_name != 'unapplied':
        products = products.filter(brand__brand_name=brand_name)  # Use 'brand__brand_name' for ForeignKey
    if color_name != 'unapplied':
        products = products.filter(colors__color_name=color_name)  # Use 'colors' for ManyToManyField
    if size_name != 'unapplied':
        products = products.filter(sizes__size_name=size_name)  # Use 'sizes' for ManyToManyField

    # Apply sorting
    if sort_by == 'popularity':
        products = products.order_by('-is_popular')  # Ensure 'is_popular' is a valid field
    elif sort_by == 'price_low_to_high':
        products = products.order_by('original_price')
    elif sort_by == 'price_high_to_low':
        products = products.order_by('-original_price')
    elif sort_by == 'new_arrivals':
        products = products.order_by('-created_at')
    elif sort_by == 'a_z':
        products = products.order_by('title')
    elif sort_by == 'z_a':
        products = products.order_by('-title')

    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    # Fetch all brands, categories, colors, and sizes for filters
    brands = Brand.objects.all()
    categories = Category.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.all()

    # Initialize and handle brand form
    if request.method == 'POST':
        brand_form = BrandForm(request.POST)
        if brand_form.is_valid():
            brand_form.save()
            return redirect('product_home')  # Redirect to the same page after saving
    else:
        brand_form = BrandForm()

    # Prepare context for rendering
    context = {
        'products': products_page,
        'brands': brands,
        'categories': categories,
        'colors': colors,
        'sizes': sizes,
        'brand_form': brand_form,
    }

    return render(request, 'product_home.html', context)


def admin_products(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    brands = Brand.objects.all()
    sizes = Size.objects.all()
    colors = Color.objects.all()


    if request.method == 'POST':
        category_form = CategoryForm(request.POST)
        brand_form = BrandForm(request.POST)
        size_form = SizeForm(request.POST)
        color_form = ColorForm(request.POST)

        if category_form.is_valid():
            category_form.save()
            messages.success(request, 'Category added successfully.', extra_tags='product_update')
            return redirect('admin_products')
        elif brand_form.is_valid():
            brand_form.save()
            messages.success(request, 'Brand added successfully.', extra_tags='product_update')
            return redirect('admin_products')
        elif size_form.is_valid():
            size_form.save()
            messages.success(request, 'Size added successfully.')
            return redirect('admin_products')
        elif color_form.is_valid():
            color_form.save()
            messages.success(request, 'Color added successfully.')
            return redirect('admin_products')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        category_form = CategoryForm()
        brand_form = BrandForm()
        size_form = SizeForm()
        color_form = ColorForm()

    context = {
        
        'products': products,
        'categories': categories,
        'brands': brands,
        'sizes': sizes,
        'colors': colors,
        'category_form': category_form,
        'brand_form': brand_form,
        'size_form': size_form,
        'color_form': color_form,
    }
    return render(request, 'productside/admin_products.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from .models import Product, ProductImage
from .forms import ProductForm, ProductImageForm

ProductImageFormset = inlineformset_factory(
    Product, ProductImage, form=ProductImageForm, extra=3, can_delete=True
)

def add_products(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        image_formset = ProductImageFormset(request.POST, request.FILES)

        if form.is_valid() and image_formset.is_valid():
            product = form.save(commit=False)  # Create Product instance without saving to DB
            product.created_by = request.user  # Set the created_by field
            product.save()  # Save the Product instance

            # Associate the formset with the product and save it
            for image_form in image_formset:
                if image_form.cleaned_data and image_form.cleaned_data.get('image'):
                    image = image_form.save(commit=False)
                    image.product = product
                    image.save()
            
            return redirect('admin_products')  # Redirect after successful save
        else:
            print('Product Form Errors:', form.errors)
            print('Image Formset Errors:', image_formset.errors)
    else:
        form = ProductForm()
        image_formset = ProductImageFormset()

    return render(request, 'productside/add_products.html', {
        'form': form,
        'image_formset': image_formset,
    })


def edit_products(request, pk):
    product = get_object_or_404(Product, pk=pk)#it fetches the product object from db using pk or else gpo 404 error

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        formset = ProductImageFormset(request.POST, request.FILES, instance=product)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('admin_products')  # Replace with your actual URL name
        else:
            print('Product Form Errors:', form.errors)
            print('Image Formset Errors:', formset.errors)
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormset(queryset=product.images.all())  # Use the correct related name here

    return render(request, 'productside/edit_products.html', {
        'form': form,
        'formset': formset,
        'product': product,  # Ensure this line is present
    })





def delete_products(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        
        
        if product.availability_status == 'in_stock':
            product.availability_status = 'out_of_stock'
        else:
            product.availability_status = 'in_stock'
        
        product.save()
        
        # Confirm the update
        updated_product = Product.objects.get(pk=pk)
        print(f"After update: {updated_product.availability_status}")  # Debug after update
        
        messages.success(request, f'Availability of "{product.title}" changed successfully.', extra_tags='product_update')
        return redirect('admin_products')
    
    return render(request, 'productside/delete_products.html', {'product': product})



def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        # Toggle is_active status instead of deleting
        category.is_active = not category.is_active
        category.save()
        
        messages.success(request, 'Category status updated successfully.')
        return redirect('admin_products')
    
    return render(request, 'productside/delete_category.html', {'category': category})



def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!', extra_tags='product_update')
            return redirect('admin_products')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'productside/edit_category.html', {'form': form, 'category': category})

def add_category(request):
    if request.method == 'POST':
        category_form = CategoryForm(request.POST)
        if category_form.is_valid():
            category_form.save()
            messages.success(request, 'Category added successfully.', extra_tags='product_update')
            return redirect('admin_products')
        else:
            messages.error(request, 'Please correct the errors below.', extra_tags='product_update')
    else:
        category_form = CategoryForm()
    
    return render(request, 'productside/add_category.html', {'form': category_form})


from django.shortcuts import render, get_object_or_404
from .models import Product, ProductImage, Review, Color
@login_required
def single_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Fetch images associated with the product
    product_images = ProductImage.objects.filter(product=product)
    
    # Fetch reviews associated with the product
    reviews = Review.objects.filter(product=product)
    
    # Fetch related products based on the category of the current product
    related_products = Product.objects.filter(category=product.category).exclude(id=product_id)[:4]
    
    # Fetch colors associated with the product
    colors = Color.objects.filter(products=product)
    #sizes = product.sizes.all()
    sizes=Size.objects.all()
    best_offer = product.get_best_offer()  # Get the best offer for the product
    # Ensure discount_percentage is not None
    discount_percentage = product.discount_percentage if product.discount_percentage is not None else 0
    # Calculate offer price if discount percentage is available
    if discount_percentage  > 0:
        offer_price = product.original_price * (1 -product.discount_percentage / 100)
    else:
        offer_price = product.original_price
    
    
    # Determine quantity range based on in_stock status and quantity
    if product.availability_status == 'in_stock' and product.quantity > 0:
        quantities = range(1, min(21, product.quantity + 1))
        out_of_stock = False
    else:
        quantities = range(0, 1)  # Set to an empty range to indicate out of stock
        out_of_stock = True
    
    # Debugging outputs
    print(f"Product ID: {product.id}")
    print(f"Availability Status: {product.availability_status}")
    print(f"Quantity in Stock: {product.quantity}")
    print(f"Quantities Range: {list(quantities)}")
    
    context = {
        'product': product,
        'product_images': product_images,
        'reviews': reviews,
        'related_products': related_products,
        'colors': colors,
        'quantities': quantities,
        'sizes': sizes,
        'out_of_stock': out_of_stock,
        'offer_price': offer_price,
        'best_offer' :best_offer
        
    }
    
    return render(request, 'productside/single_product.html', context)

def toggle_brand_status(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    brand.is_active = not brand.is_active  # Toggle the status
    brand.save()
    return redirect('admin_products')




# views.py
from django.http import JsonResponse
from .models import Product  # Import your Product model or appropriate model

def get_variant_details(request):
    color_code = request.GET.get('color_code')
    try:
        # Fetch the product variant based on the color_code
        product = Product.objects.get(colors__color_code=color_code)
        variant_details = {
            'price': product.discounted_price or product.original_price,
            'stock': product.stock,
            'description': product.description,
        }
        return JsonResponse(variant_details)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Variant not found'}, status=404)
