from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Address,Cart, Order,CartItem,Coupon
from .forms import AddressForm, UserProfileForm, CheckoutForm,OrderForm,CouponForm
from django.http import JsonResponse
from django.contrib import messages
from datetime import datetime, timedelta
from products.models import Product,Size
from django.utils import timezone
from .models import Order, OrderItem,Wishlist
from django.urls import reverse
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.http import Http404
from django.db import transaction
from django.http import HttpResponseForbidden
from django.db import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from .models import Wishlist, Product
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .forms import CouponForm
from decimal import Decimal
from django.urls import reverse
from django.conf import settings
import razorpay





def remove_from_cart(request, item_id):
    # Fetch the cart item based on item_id
    item = get_object_or_404(CartItem, id=item_id)
    
    # Check if the item belongs to the current user's cart
    if item.cart.user != request.user:
        return HttpResponseForbidden("You do not have permission to remove this item from the cart.")
    
    # Optionally get the related product_id or any other necessary data
    product_id = item.product.id
    
    # Delete the item from the cart
    item.delete()
    
    # Redirect to the cart summary or a relevant page
    return redirect('cart_summary')  

def cart_summary(request):
    if request.user.is_authenticated:
        # Get or create the cart for the current user
        cart = get_object_or_404(Cart, user=request.user)
        
        # Filter CartItem based on the cart
        cart_items = CartItem.objects.filter(cart=cart)

        # Initialize total and item_totals list
        total = 0
        item_totals = []



        # Initialize variables to check for out-of-stock products
        out_of_stock_products = []
        can_checkout = True  # Flag to determine if checkout is allowed

        # Calculate total and individual item totals
        for item in cart_items:
            item_total = item.product.original_price * item.quantity
            item_totals.append(item_total)
            total += item_total

        
            # Check if the product is out of stock
            if item.product.availability_status == 'out_of_stock':
                out_of_stock_products.append(item.product)
                can_checkout = False  # Cannot proceed to checkout if any product is out of stock

        
        return render(request, 'productside/cart.html', {
            'cart_items': cart_items,
            'total': total,
            'cart_count': cart_items.count(),
            'item_totals': item_totals,
             'out_of_stock_products': out_of_stock_products,
            'can_checkout': can_checkout,
        })
    else:
        # Handle the case for unauthenticated users
        return redirect('login')# Redirect to login page or show an error


def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')

    product = get_object_or_404(Product, id=product_id)

    if product.availability_status == 'out_of_stock':
        messages.error(request, 'This product is currently out of stock.')
        return redirect('product_home')

    size_id = request.POST.get('size')

    if not size_id:
        messages.error(request, 'No size selected.')
        return redirect('product_home')

    size = Size.objects.filter(id=size_id).first()

    quantity = int(request.POST.get('quantity', 1))

    if product.quantity < quantity:
        messages.error(request, f'Only {product.quantity} units of {product.title} are available.')
        return redirect('product_home')

    # Determine the price to use
    price = product.discounted_price if product.discounted_price and product.discounted_price < product.original_price else product.original_price

    # Debug print to ensure correct price is used
    print(f"Price to be set: {price}")

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=size,
        defaults={'quantity': quantity, 'price': price}
    )

    if not created:
        # If the cart item already exists, update its quantity
        new_quantity = cart_item.quantity + quantity
        if product.quantity < new_quantity:
            messages.error(request, f'Only {product.quantity} units of {product.title} are available.')
            return redirect('product_home')
        cart_item.quantity = new_quantity
    else:
        # If a new cart item was created, use the original quantity
        new_quantity = quantity

    # Save the cart item with the updated or initial quantity
    cart_item.save()

    messages.success(request, 'Product added to cart!')
    return redirect('cart_summary')

@login_required
def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect('checkout')
    else:
        form = AddressForm()
    return render(request, 'userprofileside/add_address.html', {'form': form})




def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)#edit
        if form.is_valid():
            form.save()
            # Redirect to the address list or another appropriate page
            return redirect('address_display')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'userprofileside/edit_address.html', {'form': form, 'address_id': address_id})





@login_required(login_url='login')
def user_profile(request):
    user = request.user
    addresses = Address.objects.filter(user=user)
    orders = Order.objects.filter(user=user)

    # Initialize forms with default values
    profile_form = UserProfileForm(instance=user)
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'profile-form' in request.POST:
            # Handle profile update
            profile_form = UserProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile has been updated successfully.")
                return redirect('user_profile')
        elif 'reset-password-form' in request.POST:
            # Handle password reset
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important to update session with new password
                messages.success(request, "Your password has been updated successfully.")
                return redirect('user_profile')
            else:
                messages.error(request, "Please correct the errors below.")
        elif 'delete-account' in request.POST:
            # Handle account deletion confirmation
            if 'confirm' in request.POST:
                user.delete()
                messages.success(request, "Your account has been deleted successfully.")
                return redirect('home')  # Redirect to home or login page after deletion
            else:
                messages.error(request, "Please confirm account deletion.")

    return render(request, 'userprofileside/user_profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'addresses': addresses,
        'orders': orders,
    })



@transaction.atomic
def cancel_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if order.status != 'Cancelled':
        try:
            # Restore stock quantities
            for item in order.items.all():
                product = item.product
                product.quantity += item.quantity
                product.save()  # Save product to update stock

            # Update the order status
            order.status = 'Cancelled'
            order.save()  # Save order status

            messages.success(request, 'Order has been canceled and stock has been updated.')
        except Exception as e:
            # Handle potential errors and rollback transaction
            transaction.rollback()
            messages.error(request, f'An error occurred while canceling the order: {e}')
    else:
        messages.error(request, 'Order is already canceled.')

    return redirect('my_orders')  # Redirect to a list of orders or another appropriate page


def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        address.delete()
        return redirect('profile_main')
    return render(request, 'userprofileside/delete_address.html', {'address': address})


@login_required
def order_summary(request, order_number):
    # Fetch the order based on order_number and the logged-in user
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    # Debugging information (can be removed in production)
    print(f"Order Number: {order_number}")
    print(f"Payment Method: {order.payment_method}")
    print(f"Initial Discount Amount: {order.discount_amount}")

    # Extract order details
    cart_items = order.items.all()  # Assuming 'items' is a related_name in OrderItem
    total = order.total
    shipping_fee = order.shipping_fee
    payment_method = order.payment_method

    # Initialize discount amount
    discount_amount = order.discount_amount

    # Check if a coupon is applied and adjust discount amount accordingly
    if order.coupon:  # Assuming there is a field to track the coupon used in Order
        # Recalculate the discount based on the coupon's discount percentage
        coupon_discount = (order.coupon.discount / 100) * total
        discount_amount = min(discount_amount, coupon_discount)  # Ensure we do not exceed the calculated discount

    # Calculate the adjusted grand total based on the final discount amount
    grand_total = total - discount_amount + shipping_fee

    # Format the address if Address is related and has relevant fields
    if order.address:
        address = order.address
        formatted_address = f"{address.street_address}, {address.city}, {address.state}, {address.postal_code}"
    else:
        formatted_address = 'No address available'

    # Prepare context for the template
    context = {
        'order': order,
        'cart_items': cart_items,
        'total': total,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total,  # Use the calculated grand total
        'discount_amount': discount_amount,
        'payment_method': payment_method,
        'formatted_address': formatted_address,
    }
    
    # Debugging information (can be removed in production)
    print(context)
    
    return render(request, 'userprofileside/order_summary.html', context)

# A placeholder for the discount calculation logic
def calculate_discount(order):
    # Implement your discount logic here (e.g., promotional code, user-based discounts)
    # For simplicity, returning a fixed discount value (e.g., $10). Update this logic as needed.
    return 10.00  # Example discount

def order_detail(request, order_number):
    print(f"Order number received: {order_number}")  # Debugging print
    try:
        order = Order.objects.get(order_number=order_number)
        order_items = OrderItem.objects.filter(order=order)
    except Order.DoesNotExist:
        return render(request, 'userprofileside/order_not_found.html')

    context = {
        'order': order,
        'order_items': order_items,  # Ensure correct context key
    }
    return render(request, 'userprofileside/order_detail.html', context)







@login_required
def order_success(request, order_number):
    # Fetch the order using the order_number
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    context = {
        'order_number': order.order_number,
    }
    
    return render(request, 'userprofileside/order_success.html', context)


@login_required
def place_order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.payment_method = request.POST.get('payment_method')  # Ensure the payment method is captured
            order.discount_amount = request.POST.get('discount_amount', 0)  # Capture discount if any
            order.save()

            cart_items = CartItem.objects.filter(user=request.user)
            for cart_item in cart_items:
                # Create order items and update stock
                product = cart_item.product
                if product.in_stock >= cart_item.quantity:  # Ensure enough stock
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=cart_item.quantity,
                        total_price=cart_item.total_price
                    )

                    # Decrease stock quantity
                    product.in_stock -= cart_item.quantity
                    product.save()
                else:
                    messages.error(request, f"Not enough stock for {product.name}.")
                    return redirect('cart')  # Redirect to cart if stock is insufficient
            
            # Clear the cart after placing the order
            cart_items.delete()

            # Redirect to the order success page with the order number
            return redirect(reverse('order_success', args=[order.id]))

    else:
        form = OrderForm()

    return render(request, 'userprofileside/order_success.html', {'form': form})



@login_required
def my_orders(request):
    # Fetch orders for the logged-in user
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    
    context = {
        'orders': orders
        
    }
    return render(request, 'userprofileside/my_orders.html', context)








@login_required
def profile_main(request, *args, **kwargs):
    # Get the logged-in user
    user = request.user
    
    # Retrieve the address_id from kwargs or GET parameters
    address_id = kwargs.get('address_id') or request.GET.get('address_id')

    if address_id:
        try:
            address_id = int(address_id)
            url = reverse('address_display', kwargs={'address_id': address_id})
        except (ValueError, TypeError):
            # Handle cases where address_id is not valid
            url = None
    else:
        url = None  # Handle case where address_id is missing

    # Render the template with the user's details
    return render(request, 'userprofileside/userprofile_main.html', {
        'user': user,
        'address_display_url': url
    })



def address_display(request):
    # Ensure user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login if not authenticated

    # Filter addresses for the logged-in user
    addresses = Address.objects.filter(user=request.user)

    return render(request, 'userprofileside/address_display.html', {'addresses': addresses})



def reset_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password and confirm_password:
            if new_password == confirm_password:
                user = request.user
                user.set_password(new_password)
                user.save()

                update_session_auth_hash(request, user)  # Important to keep the user logged in
                messages.success(request, 'Your password was successfully updated!')
                return redirect('profile_main')  # Redirect to the profile page
            else:
                messages.error(request, "Passwords do not match. Please enter matching passwords.")
        else:
            messages.error(request, 'Please fill out both password fields.')

    return render(request, 'userprofileside/user_profile.html')

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import CartItem

def update_cart(request):
    if request.method == 'POST' and request.is_ajax():
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))

        # Fetch the cart item
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.quantity = quantity
        cart_item.save()

        # Calculate updated totals
        item_total = cart_item.quantity * cart_item.product.original_price

        # Calculate cart totals
        cart_items = CartItem.objects.all()  # Adjust this if necessary
        cart_subtotal = sum(item.quantity * item.product.original_price for item in cart_items)
        cart_total = cart_subtotal  # Modify this if there are taxes, shipping, etc.

        # Return updated totals as JSON
        return JsonResponse({
            'item_total': item_total,
            'cart_subtotal': cart_subtotal,
            'cart_total': cart_total,
            'cart_quantity': sum(item.quantity for item in cart_items)
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def wishlist(request):
    try:
        wishlist_items = Wishlist.objects.filter(user=request.user)
    except MultipleObjectsReturned:
        # Handle the case where multiple objects are returned
        wishlist_items = Wishlist.objects.filter(user=request.user).first()  # Get the first item
        Wishlist.objects.filter(user=request.user).exclude(id=wishlist_items.id).delete()  # Remove other duplicates

    # Filter messages that should only be displayed on the wishlist page
    messages_for_wishlist = [msg for msg in messages.get_messages(request) if 'wishlist' in msg.tags]

    context = {
        'wishlist_items': wishlist_items,
        'messages_for_wishlist': messages_for_wishlist
    }
    return render(request, 'userprofileside/wishlist.html', context)



@login_required
def remove_from_wishlist(request, item_id):
    if request.method == 'POST':
        wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
        wishlist_item.delete()
        messages.success(request, "Item removed from wishlist.")
    else:
        messages.error(request, "Invalid request method.")
    return redirect('wishlist')

@login_required
def toggle_wishlist(request, product_id):
    # Example view for toggling wishlist status
    if request.method == 'GET':
        product = get_object_or_404(Product, id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if not created:
            wishlist_item.delete()
            message = 'Item removed from wishlist'
        else:
            message = 'Item added to wishlist'
        return JsonResponse({'success': True, 'message': message})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method'})


def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        # Handle unauthenticated user: redirect to login with a message
        messages.error(request, 'You need to be logged in to add items to your wishlist.', extra_tags='wishlist')
        return redirect('login')  # Redirect to the login page

    try:
        # Get the product object
        product = get_object_or_404(Product, id=product_id)
        
        # Check if the product is already in the user's wishlist
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        
        # Inform the user about the status
        if created:
            message = 'Product added to your wishlist.'
            messages.success(request, message, extra_tags='wishlist')
            success = True
        else:
            message = 'Product is already in your wishlist.'
            messages.info(request, message, extra_tags='wishlist')
            success = False

        # Handle AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': success, 'message': message})

    except Exception as e:
        # Handle unexpected errors
        message = 'An error occurred while adding the product to your wishlist. Please try again.'
        messages.error(request, message, extra_tags='wishlist')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': message})

    # For non-AJAX requests or if no exception occurs, redirect to the wishlist page
    return redirect('wishlist')  # Change 'wishlist' to your wishlist page name


#check out cod and razor pay

import uuid

def generate_unique_order_number():
    return str(uuid.uuid4())



#coupon admin

def coupon_list(request):
    search_query = request.GET.get('search', '')

    if search_query:
        coupon_list = Coupon.objects.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    else:
        coupon_list = Coupon.objects.all()

    paginator = Paginator(coupon_list, 3)  # Show 3 coupons per page

    page = request.GET.get('page')
    try:
        coupons = paginator.page(page)
    except PageNotAnInteger:
        coupons = paginator.page(1)
    except EmptyPage:
        coupons = paginator.page(paginator.num_pages)

    context = {
        'coupons': coupons,
        'search_query': search_query,
    }
    return render(request, 'adminside/coupon_list.html', context)

def coupon_add(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('coupon_list')
    else:
        form = CouponForm()
    return render(request, 'adminside/coupon_form.html', {'form': form})

def coupon_edit(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            return redirect('coupon_list')
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'adminside/coupon_form.html', {'form': form})

def coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)

    # Directly update the status field
    if coupon.status == 'active':
        coupon.status = 'inactive'
    else:
        coupon.status = 'active'
    
    coupon.save(update_fields=['status'])
    return redirect('coupon_list')  # Use update_fields to only save the status field


from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal
from .models import Cart, CartItem, Coupon, Address, Order, OrderItem
from wallet.models import Wallet

def checkout(request):
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle AJAX requests for coupon application/removal
            # Same as before, no changes required here...
            pass
        else:
            # Handle regular form submission for checkout
            selected_address_id = request.POST.get('selected_address')
            payment_method = request.POST.get('payment_method')
            coupon_code = request.POST.get('coupon_code', '')

            try:
                cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                messages.error(request, 'Your cart is empty.')
                return redirect('home')

            cart_items = CartItem.objects.filter(cart=cart)
            addresses = Address.objects.filter(user=request.user)

            try:
                address = Address.objects.get(id=selected_address_id, user=request.user)
            except Address.DoesNotExist:
                messages.error(request, 'Invalid address selected.')
                return redirect('checkout')

            total = sum(item.total_price for item in cart_items)
            shipping_fee = Decimal('10.00')

            # Calculate offer discount
            offer_discount = max((item.product.get_best_offer() for item in cart_items), default=Decimal('0.00'))
            total_discount_amount = (offer_discount / 100) * total
            discounted_total = total - total_discount_amount

            coupon_message = ''
            coupon_discount = Decimal('0.00')

            # Calculate coupon discount
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)
                    if coupon.is_valid():
                        coupon_discount = (coupon.discount / 100) * discounted_total
                        total_discount_amount += coupon_discount
                        discounted_total -= coupon_discount
                        coupon_message = f'Coupon applied: {coupon_code} gives {coupon.discount}% discount.'
                    else:
                        coupon_message = 'Coupon is expired or not valid.'
                except Coupon.DoesNotExist:
                    coupon_message = 'Invalid coupon code.'

            grand_total = discounted_total + shipping_fee

            if payment_method == 'cod' and grand_total > 1000:
                messages.error(request, 'Cash on Delivery is not available for orders above Rs. 1000.')
                return redirect('checkout')

            # Validate stock for each item before creating the order
            for item in cart_items:
                product = item.product
                if product.quantity < item.quantity:
                    messages.error(request, f'Not enough stock for {product.title}. Only {product.quantity} units available.')
                    return redirect('checkout')

            # Proceed with payment and order creation
            if payment_method:
                if payment_method == 'wallet':
                    try:
                        wallet = Wallet.objects.get(user=request.user)
                        if wallet.balance >= grand_total:
                            wallet.balance -= grand_total
                            wallet.save()

                            # Create the order after successful payment
                            order = Order.objects.create(
                                user=request.user,
                                total=total,
                                shipping_fee=shipping_fee,
                                discount_amount=total_discount_amount,
                                grand_total=grand_total,
                                address=address,
                                payment_method=payment_method,
                                payment_status='pending'
                            )

                            # Reduce stock and create OrderItems
                            for item in cart_items:
                                product = item.product
                                product.quantity -= item.quantity  # Reduce the stock
                                product.save()

                                OrderItem.objects.create(
                                    order=order,
                                    product=product,
                                    quantity=item.quantity,
                                    total_price=item.total_price
                                )

                            cart_items.delete()
                            messages.success(request, 'Order placed successfully with wallet payment!')
                            return redirect(reverse('order_summary', kwargs={'order_number': order.order_number}))
                        else:
                            messages.error(request, 'Insufficient wallet balance.')
                            return redirect('checkout')
                    except Wallet.DoesNotExist:
                        messages.error(request, 'Wallet not found.')
                        return redirect('checkout')

                elif payment_method == 'razorpay':
                    order = Order.objects.create(
                        user=request.user,
                        total=total,
                        shipping_fee=shipping_fee,
                        discount_amount=total_discount_amount,
                        grand_total=grand_total,
                        address=address,
                        payment_method=payment_method,
                        payment_status='Pending'
                    )

                    # Reduce stock and create OrderItems
                    for item in cart_items:
                        product = item.product
                        product.quantity -= item.quantity  # Reduce the stock
                        product.save()

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=item.quantity,
                            total_price=item.total_price
                        )

                    cart_items.delete()
                    return redirect(reverse('payment_view', kwargs={'order_id': order.id}))

                elif payment_method == 'cod':
                    order = Order.objects.create(
                        user=request.user,
                        total=total,
                        shipping_fee=shipping_fee,
                        discount_amount=total_discount_amount,
                        grand_total=grand_total,
                        address=address,
                        payment_method=payment_method,
                        payment_status='Pending'
                    )

                    # Reduce stock and create OrderItems
                    for item in cart_items:
                        product = item.product
                        product.quantity -= item.quantity  # Reduce the stock
                        product.save()

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=item.quantity,
                            total_price=item.total_price
                        )

                    cart_items.delete()
                    messages.success(request, 'Order placed successfully with Cash on Delivery!')
                    return redirect(reverse('order_summary', kwargs={'order_number': order.order_number}))

                else:
                    messages.error(request, 'Invalid payment method selected.')
                    return redirect('checkout')
            else:
                messages.error(request, 'Please select a payment method.')
                return redirect('checkout')
    else:
        # Handle GET request to display checkout page
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            messages.error(request, 'Your cart is empty.')
            return redirect('home')

        cart_items = CartItem.objects.filter(cart=cart)
        addresses = Address.objects.filter(user=request.user)
        total = sum(item.total_price for item in cart_items)
        shipping_fee = Decimal('10.00')
        coupon_message = ''
        coupons = Coupon.objects.all()

        # Calculate offer discount
        offer_discount = max((item.product.get_best_offer() for item in cart_items), default=Decimal('0.00'))
        total_discount_amount = (offer_discount / 100) * total
        discounted_total = total - total_discount_amount

        # Get wallet balance
        try:
            wallet = Wallet.objects.get(user=request.user)
            wallet_balance = wallet.balance
        except Wallet.DoesNotExist:
            wallet_balance = Decimal('0.00')

        context = {
            'addresses': addresses,
            'cart_items': cart_items,
            'total': total,
            'shipping_fee': shipping_fee,
            'grand_total': discounted_total + shipping_fee,
            'coupon_message': coupon_message,
            'discount_amount': total_discount_amount,
            'coupons': coupons,
            'wallet_balance': wallet_balance,
        }
        return render(request, 'userprofileside/checkout.html', context)




def update_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 0))
        print(quantity)

        try:
            cart = Cart.objects.get(user=request.user)
            item = CartItem.objects.get(cart=cart, id=item_id)
            product = item.product

            # Check if quantity exceeds stock
            if quantity > product.quantity:
                return JsonResponse({'success': False, 'error_message': f"Not enough stock available for {product.title}."})
            # Check if quantity exceeds maximum allowed per person
           
            else:
                item.quantity = quantity
                item.save()
                return JsonResponse({'success': True})

        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'error_message': 'Cart not found.'})
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error_message': 'Cart item not found.'})
        except ValueError:
            return JsonResponse({'success': False, 'error_message': 'Invalid quantity.'})

    return JsonResponse({'success': False, 'error_message': 'Invalid request method'}, status=405)

"""from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal
from .models import Cart, CartItem, Coupon, Address, Order, OrderItem
from wallet.models import Wallet

def checkout(request):
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle AJAX requests for coupon application/removal
            action = request.POST.get('action')
            response_data = {}

            try:
                cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                response_data = {'success': False, 'message': 'Your cart is empty.'}
                return JsonResponse(response_data)

            cart_items = CartItem.objects.filter(cart=cart)
            total = sum(item.total_price for item in cart_items)
            shipping_fee = Decimal('10.00')
            discounted_total = total
            total_discount_amount = Decimal('0.00')
            coupon_discount_amount = Decimal('0.00')

            # Calculate offer discount
            offer_discount = Decimal('0.00')
            for item in cart_items:
                offer_discount = max(offer_discount, item.product.get_best_offer())

            
            if action == 'apply':
                coupon_code = request.POST.get('coupon_code', '')
                if coupon_code:
                    try:
                        coupon = Coupon.objects.get(code=coupon_code)
                        if coupon.is_valid():
                            coupon_discount = (coupon.discount / 100) * discounted_total
                            total_discount_amount += coupon_discount
                            discounted_total -= coupon_discount
                            response_data['message'] = f'Coupon applied: {coupon_code} gives {coupon.discount}% discount.'
                        else:
                            response_data['message'] = 'Coupon is expired or not valid.'
                    except Coupon.DoesNotExist:
                        response_data['message'] = 'Invalid coupon code.'

                grand_total = discounted_total + shipping_fee
                response_data['success'] = True
                response_data['new_total'] = grand_total
                response_data['discount'] = total_discount_amount

            elif action == 'remove':
                # Recalculate totals without any coupon
                discounted_total = total
                total_discount_amount = Decimal('0.00')

                # Calculate offer discount
                offer_discount = Decimal('0.00')
                for item in cart_items:
                    offer_discount = max(offer_discount, item.product.get_best_offer())

                if offer_discount:
                    total_discount_amount += (offer_discount / 100) * total
                    discounted_total -= (offer_discount / 100) * total

                grand_total = discounted_total + shipping_fee
                response_data['success'] = True
                response_data['new_total'] = grand_total
                response_data['discount'] = total_discount_amount
                response_data['message'] = 'Coupon removed successfully.'

            else:
                response_data = {'success': False, 'message': 'Invalid action'}

            return JsonResponse(response_data)

        else:
            # Handle regular form submission for checkout
            selected_address_id = request.POST.get('selected_address')
            payment_method = request.POST.get('payment_method')
            coupon_code = request.POST.get('coupon_code', '')

            try:
                cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                messages.error(request, 'Your cart is empty.')
                return redirect('home')

            cart_items = CartItem.objects.filter(cart=cart)
            addresses = Address.objects.filter(user=request.user)

            try:
                address = Address.objects.get(id=selected_address_id, user=request.user)
            except Address.DoesNotExist:
                messages.error(request, 'Invalid address selected.')
                return redirect('checkout')

            total = sum(item.total_price for item in cart_items)
            shipping_fee = Decimal('10.00')
            discounted_total = total
            total_discount_amount = Decimal('0.00')

            # Calculate offer discount
            offer_discount = Decimal('0.00')
            for item in cart_items:
                offer_discount = max(offer_discount, item.product.get_best_offer())

            if offer_discount:
                total_discount_amount += (offer_discount / 100) * total
                discounted_total -= (offer_discount / 100) * total

            # Calculate coupon discount
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)
                    if coupon.is_valid():
                        coupon_discount = (coupon.discount / 100) * discounted_total
                        total_discount_amount += coupon_discount
                        discounted_total -= coupon_discount
                    else:
                        messages.error(request, 'Coupon is expired or not valid.')
                except Coupon.DoesNotExist:
                    messages.error(request, 'Invalid coupon code.')

            grand_total = discounted_total + shipping_fee

            if payment_method:
                # Handle wallet payment
                if payment_method == 'wallet':
                    try:
                        wallet = Wallet.objects.get(user=request.user)
                        if wallet.balance >= grand_total:
                            wallet.balance -= grand_total
                            wallet.save()
                            order = Order.objects.create(
                                user=request.user,
                                total=total,
                                shipping_fee=shipping_fee,
                                discount_amount=total_discount_amount,
                                grand_total=grand_total,
                                address=address,
                                payment_method=payment_method,
                                payment_status='Paid'
                            )
                            for item in cart_items:
                                OrderItem.objects.create(
                                    order=order,
                                    product=item.product,
                                    quantity=item.quantity,
                                    total_price=item.total_price
                                )
                            cart_items.delete()
                            messages.success(request, 'Order placed successfully with wallet payment!')
                            return redirect(reverse('order_summary', kwargs={'order_number': order.order_number}))
                        else:
                            messages.error(request, 'Insufficient wallet balance.')
                            return redirect('checkout')
                    except Wallet.DoesNotExist:
                        messages.error(request, 'Wallet not found.')
                        return redirect('checkout')

                # Handle Razorpay payment
                elif payment_method == 'razorpay':
                    order = Order.objects.create(
                        user=request.user,
                        total=total,
                        shipping_fee=shipping_fee,
                        discount_amount=total_discount_amount,
                        grand_total=grand_total,
                        address=address,
                        payment_method=payment_method,
                        payment_status='Pending'
                    )
                    for item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            total_price=item.total_price
                        )
                    cart_items.delete()
                    return redirect(reverse('payment_view', kwargs={'order_id': order.id}))

                # Handle Cash on Delivery
                elif payment_method == 'cod':
                    order = Order.objects.create(
                        user=request.user,
                        total=total,
                        shipping_fee=shipping_fee,
                        discount_amount=total_discount_amount,
                        grand_total=grand_total,
                        address=address,
                        payment_method=payment_method,
                        payment_status='Pending'
                    )
                    for item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            total_price=item.total_price
                        )
                    cart_items.delete()
                    messages.success(request, 'Order placed successfully with Cash on Delivery!')
                    return redirect(reverse('order_summary', kwargs={'order_number': order.order_number}))
                else:
                    messages.error(request, 'Invalid payment method selected.')
                    return redirect('checkout')
            else:
                messages.error(request, 'Please select a payment method.')
                return redirect('checkout')
    else:
        # Handle GET request to display checkout page
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            messages.error(request, 'Your cart is empty.')
            return redirect('home')

        cart_items = CartItem.objects.filter(cart=cart)
        addresses = Address.objects.filter(user=request.user)
        total = sum(item.total_price for item in cart_items)
        shipping_fee = Decimal('10.00')
        total_discount_amount = Decimal('0.00')
        coupon_message = ''
        coupons = Coupon.objects.all()

        # Calculate offer discount
        offer_discount = Decimal('0.00')
        for item in cart_items:
            offer_discount = max(offer_discount, item.product.get_best_offer())

        if offer_discount:
            total_discount_amount += (offer_discount / 100) * total
            discounted_total = total - (offer_discount / 100) * total
        else:
            discounted_total = total

        # Get wallet balance
        try:
            wallet = Wallet.objects.get(user=request.user)
            wallet_balance = wallet.balance
        except Wallet.DoesNotExist:
            wallet_balance = Decimal('0.00')

        context = {
            'addresses': addresses,
            'cart_items': cart_items,
            'total': total,
            'shipping_fee': shipping_fee,
            'grand_total': discounted_total + shipping_fee,
            'discount_amount': total_discount_amount,
            'coupons': coupons,
            'wallet_balance': wallet_balance,
        }
        return render(request, 'userprofileside/checkout.html', context)"""
