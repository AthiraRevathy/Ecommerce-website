from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.contrib import messages
from .forms import LoginForm
from django.shortcuts import render, redirect, get_object_or_404
from product_cart.models import Order,OrderItem
import calendar 
from django.db.models import Count, Sum  
from django.db.models.functions import TruncDay, TruncMonth, TruncYear 
from django.contrib.auth import get_user_model  
from django.contrib.auth.decorators import login_required  
from products.models import Product 









@cache_control(no_cache=True, no_store=True, must_revalidate=True, max_age=0)
def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('adminlog:admin_dashboard')

    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)

            if user is not None and user.is_superuser:
                login(request, user)
                messages.success(request, 'Login successful.')
                return redirect('adminlog:admin_dashboard')
            else:
                messages.error(request, 'Invalid credentials or not a superuser.')
    else:
        form = LoginForm()

    context = {
        'form': form,
    }
    return render(request, 'adminside/admin_login.html', context)

def admin_dashboard(request):
    # Determine the time period for filtering orders
    filter_type = request.GET.get('filter', 'daily')  # Default to daily if no filter is provided

    # Define the aggregation function based on filter type
    if filter_type == 'monthly':
        truncate_func = TruncMonth
        months = [calendar.month_abbr[i] for i in range(1, 13)]  # List of month abbreviations
    elif filter_type == 'yearly':
        truncate_func = TruncYear
        months = []  # No need for month labels if filtering yearly
    else:  # Default to daily
        truncate_func = TruncDay
        months = []  # No need for month labels if filtering daily

    # Aggregate order data based on the selected filter
    aggregated_orders = (
        Order.objects
        .annotate(date=truncate_func('created_at'))
        .values('date')
        .annotate(order_count=Count('id'))
        .order_by('date')
    )

    # Prepare data for the chart
    if filter_type == 'monthly':
        # Create a dictionary to map months to counts
        monthly_data = {calendar.month_abbr[i]: 0 for i in range(1, 13)}
        for order in aggregated_orders:
            month_name = calendar.month_abbr[order['date'].month]
            monthly_data[month_name] = order['order_count']

        chart_labels = months
        chart_data = [monthly_data[month] for month in months]
    elif filter_type == 'yearly':
        chart_labels = [order['date'].strftime('%Y') for order in aggregated_orders]
        chart_data = [order['order_count'] for order in aggregated_orders]
    else:  # Default to daily
        chart_labels = [order['date'].strftime('%Y-%m-%d') for order in aggregated_orders]
        chart_data = [order['order_count'] for order in aggregated_orders]

    # Fetch most selling products data
    most_selling_products = (
        OrderItem.objects
        .values('product__title')
        .annotate(total_sales=Sum('quantity'))
        .order_by('-total_sales')[:10]  # Top 10 most selling products
    )

    # Prepare data for the most selling products chart
    product_labels = [item['product__title'] for item in most_selling_products]
    product_data = [item['total_sales'] for item in most_selling_products]

    most_selling_brands = (
        OrderItem.objects
        .values('product__brand__brand_name')
        .annotate(total_quantity=Count('quantity'))
        .order_by('-total_quantity')[:10]  # Get top 10 selling brands
    )
    brand_labels = [item['product__brand__brand_name'] for item in most_selling_brands]
    brand_data = [item['total_quantity'] for item in most_selling_brands]

    # Fetch all orders
    orders = Order.objects.all()
    total_sales = Order.objects.filter(status='Delivered').aggregate(total_sales=Sum('grand_total'))['total_sales'] or 0
    total_orders = Order.objects.count()
    active_users = get_user_model().objects.filter(is_active=True).count()
    total_products = Product.objects.count()
    delivered_orders = Order.objects.filter(status='Delivered').count()
    shipped_orders = Order.objects.filter(status='Shipped').count()
    cancelled_orders = Order.objects.filter(status='Cancelled').count()
    returned_orders = Order.objects.filter(status='Returned').count()
    context = {
        'orders': orders,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'product_labels': product_labels,
        'product_data': product_data,
        'brand_labels': brand_labels,
        'brand_data': brand_data,
        'selected_filter': filter_type,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'active_users': active_users,
        'total_products': total_products,
        'delivered_orders': delivered_orders,
        'shipped_orders': shipped_orders,
        'cancelled_orders': cancelled_orders,
        'returned_orders': returned_orders,
    }

    if request.user.is_authenticated and request.user.is_staff:
        return render(request, 'adminside/admin_dashboard.html', context)
    else:
        return redirect('home')
    


def admin_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('adminlog:admin_login')
    

def order_list(request):
    # Get search query and status filter from GET parameters
    query = request.GET.get('q', '')  # Search query
    status_filter = request.GET.get('status', '')  # Filter by status

    # Start with all orders
    orders = Order.objects.all().order_by('-created_at')
    
    # Apply search filter if a query is provided
    if query:
        orders = orders.filter(
            user__username__icontains=query  # Assuming 'user__username' is the field to search
        )
    
    # Apply status filter if a status is provided
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Pass the orders to the template
    context = {
        'orders': orders,
        'query': query,
        'status_filter': status_filter,
    }
    
    return render(request, 'adminside/adminorder_list.html', context)
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from product_cart.models import Order

def update_order_status(request):
    if request.method == 'POST':
        order_number = request.POST.get('order_number')
        new_status = request.POST.get('status')
        
        if not order_number:
            messages.error(request, 'Order number is required.')
            return redirect('adminlog:order_list')

        try:
            order = get_object_or_404(Order, order_number=order_number)
        except ValueError as e:
            messages.error(request, f'Error fetching order: {e}')
            return redirect('adminlog:order_list')

        if new_status not in ['Pending', 'Confirmed', 'Rejected', 'Delivered']:
            messages.error(request, 'Invalid status value.')
            return redirect('adminlog:order_list')

        order.status = new_status
        order.save()

        messages.success(request, 'Order status updated successfully!')
        return redirect('adminlog:order_list')

    return redirect('adminlog:order_list')


