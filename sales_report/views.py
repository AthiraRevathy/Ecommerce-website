from django.shortcuts import render
import pandas as pd
from product_cart.models import Coupon
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from django.utils.timezone import make_naive
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.db.models import Q
from decimal import Decimal
from product_cart.models import Order
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger 






def sale_report_view(request):
    filter_option = request.GET.get('filter', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search', '').strip()

    # Base query for orders
    orders_query = Order.objects.all()

    # Date filters
    today = timezone.now().date()
    
    if filter_option == 'today':
        orders_query = orders_query.filter(created_at__date=today)
    elif filter_option == 'weekly':
        start_of_week = today - timedelta(days=today.weekday())
        orders_query = orders_query.filter(created_at__date__gte=start_of_week)
    elif filter_option == 'monthly':
        start_of_month = today.replace(day=1)
        orders_query = orders_query.filter(created_at__date__gte=start_of_month)
    elif filter_option == 'yearly':
        start_of_year = today.replace(month=1, day=1)
        orders_query = orders_query.filter(created_at__date__gte=start_of_year)

    # Debug: Print the count of orders after applying date filters
    print(f"After filter '{filter_option}': {orders_query.count()} orders found")

    # Search functionality
    if search_query:
        orders_query = orders_query.filter(
            Q(user__username__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(items__product__title__icontains=search_query) |
            Q(items__product__description__icontains=search_query) |
            Q(items__product__original_price__icontains=search_query) |
            Q(items__total_price__icontains=search_query) |
            Q(items__quantity__icontains=search_query) |
            Q(grand_total__icontains=search_query) |
            Q(status__icontains=search_query) |
            Q(payment_method__icontains=search_query)
        ).distinct()

    # Debug: Print the count of orders after applying search query
    print(f"After search '{search_query}': {orders_query.count()} orders found")

    # Overall statistics
    overall_sales_count = orders_query.count()
    overall_success_amount = orders_query.filter(status='Delivered').aggregate(Sum('grand_total'))['grand_total__sum'] or Decimal('0.00')

    # Calculate overall discount based on offer_price
    discount_amount = Decimal('0.00')
    for order in orders_query:
        for item in order.items.all():
            original_price = item.product.original_price or Decimal('0.00')
            offer_price = item.product.offer_price or Decimal('0.00')
            discount_amount += (original_price - offer_price) * item.quantity

    overall_discount = discount_amount

    # Additional statistics
    success_order_count = orders_query.filter(status='Delivered').count()
    cancelled_order_count = orders_query.filter(status='Cancelled').count()
    returned_order_count = orders_query.filter(return_request__isnull=False).count()
    return_request_count = orders_query.filter(return_request__status='Requested').count()
    in_progress_count = orders_query.filter(status='Ordered').count()

    # Sales data for chart
    sales_data = orders_query.values('created_at__date').annotate(
        total_sales=Sum('grand_total')
    ).order_by('created_at__date')

    # Generate chart data based on sales_data
    chart_labels = [data['created_at__date'].strftime('%Y-%m-%d') for data in sales_data]
    chart_data = [data['total_sales'] or Decimal('0.00') for data in sales_data]
    chart_data = [float(value) for value in chart_data]

    # Order by the created_at date
    orders_query = orders_query.order_by('-created_at')

    # Pagination
    paginator = Paginator(orders_query, 30)  # Show 30 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,  # Use the paginated results
        'overall_sales_count': overall_sales_count,
        'overall_success_amount': overall_success_amount,
        'overall_discount': overall_discount,
        'success_order_count': success_order_count,
        'cancelled_order_count': cancelled_order_count,
        'returned_order_count': returned_order_count,
        'return_request_count': return_request_count,
        'in_progress_count': in_progress_count,
        'search_query': search_query,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }

    return render(request, 'adminside/sales_report.html', context)


def truncate_title(title, length=15):
    if len(title) > length:
        return title[:length] + '...'
    return title

def pdf_report_view(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Fetching filtered data
    filter_option = request.GET.get('filter', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if filter_option == 'all':
        orders = Order.objects.all()
    elif filter_option == 'today':
        today = timezone.now().date()
        orders = Order.objects.filter(created_at__date=today)
    elif filter_option == 'weekly':
        start_of_week = timezone.now().date() - timedelta(days=timezone.now().weekday())
        orders = Order.objects.filter(created_at__date__gte=start_of_week)
    elif filter_option == 'monthly':
        start_of_month = timezone.now().date().replace(day=1)
        orders = Order.objects.filter(created_at__date__gte=start_of_month)
    elif filter_option == 'yearly':
        start_of_year = timezone.now().date().replace(month=1, day=1)
        orders = Order.objects.filter(created_at__date__gte=start_of_year)
    elif filter_option == 'custom' and start_date and end_date:
        orders = Order.objects.filter(created_at__date__range=[start_date, end_date])
    else:
        orders = Order.objects.all()

    # Calculate overall details
    overall_sales_count = orders.count()
    overall_success_amount = orders.filter(status='Delivered').aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    discount_amount = 0
    for order in orders:
        for item in order.items.all():
            original_price = item.product.original_price or 0  # Handle NoneType
            offer_price = item.product.offer_price or original_price  # Handle NoneType
            discount_amount += (original_price - offer_price) * item.quantity

    overall_discount = discount_amount

    success_order_count = orders.filter(status='Delivered').count()
    cancelled_order_count = orders.filter(status='Cancelled').count()
    returned_order_count = orders.filter(return_request__isnull=False).count()
    return_request_count = orders.filter(return_request__status='Requested').count()
    in_progress_count = orders.filter(status='Ordered').count()

    # Set up PDF styles
    p.setFont("Helvetica-Bold", 14)
    p.drawString(230, height - 50, "Sales Report")

    # Overall Sales Details
    y_position = height - 80
    p.setFont("Helvetica", 10)
    p.drawString(40, y_position, f"Total Sales Count: {overall_sales_count}")
    p.drawString(40, y_position - 15, f"Total Success Order Amount: ${overall_success_amount:.2f}")
    p.drawString(40, y_position - 30, f"Total Discount Given: ${overall_discount:.2f}")
    p.drawString(40, y_position - 45, f"Success Order Count: {success_order_count}")
    p.drawString(40, y_position - 60, f"Cancelled Order Count: {cancelled_order_count}")
    p.drawString(40, y_position - 75, f"Returned Order Count: {returned_order_count}")
    p.drawString(40, y_position - 90, f"Return Request Count: {return_request_count}")
    p.drawString(40, y_position - 105, f"In Progress Count: {in_progress_count}")

    y_position -= 130  # Adjust position for the table

    # Sales Report Table
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y_position, "Sales Report Table")

    y_position -= 20  # Adjust position for table headers

    # Define column positions with "User" instead of "Username"
    col_positions = {
        "id": 40,
        "user": 80,
        "order_date": 120,
        "product_title": 180,
        "og_price": 260,
        "quantity": 320,
        "discount": 380,
        "total_amount": 440,
        "status": 500
    }

    # Table Headers
    p.setFont("Helvetica-Bold", 8)
    p.drawString(col_positions["id"], y_position, "ID")
    p.drawString(col_positions["user"], y_position, "User")
    p.drawString(col_positions["order_date"], y_position, "Order Date")
    p.drawString(col_positions["product_title"], y_position, "Product Title")
    p.drawString(col_positions["og_price"], y_position, "OG Price")
    p.drawString(col_positions["quantity"], y_position, "Quantity")
    p.drawString(col_positions["discount"], y_position, "Discount")
    p.drawString(col_positions["total_amount"], y_position, "Total")
    p.drawString(col_positions["status"], y_position, "Status")

    y_position -= 20  # Adjust position for table rows

    # Table Rows
    p.setFont("Helvetica", 8)
    row_height = 12  # Reduced row size
    max_rows_per_page = int((height - y_position - 40) / row_height)  # Calculate max rows per page
    row_count = 0

    for order in orders:
        for item in order.items.all():
            if row_count >= max_rows_per_page:
                p.showPage()  # Create a new page
                p.setFont("Helvetica", 8)
                y_position = height - 40  # Reset position for new page
                row_count = 0
                # Reprint headers
                p.drawString(col_positions["id"], y_position, "ID")
                p.drawString(col_positions["user"], y_position, "User")
                p.drawString(col_positions["order_date"], y_position, "Order Date")
                p.drawString(col_positions["product_title"], y_position, "Product Title")
                p.drawString(col_positions["og_price"], y_position, "OG Price")
                p.drawString(col_positions["quantity"], y_position, "Quantity")
                p.drawString(col_positions["discount"], y_position, "Discount")
                p.drawString(col_positions["total_amount"], y_position, "Total")
                p.drawString(col_positions["status"], y_position, "Status")
                y_position -= 20  # Adjust position for table rows

            # Draw each row with "User" instead of "Username"
            p.drawString(col_positions["id"], y_position, str(item.id))
            p.drawString(col_positions["user"], y_position, order.user.username)
            p.drawString(col_positions["order_date"], y_position, order.created_at.strftime("%Y-%m-%d"))
            p.drawString(col_positions["product_title"], y_position, truncate_title(item.product.title))
            p.drawString(col_positions["og_price"], y_position, f"${item.product.original_price:.2f}")
            p.drawString(col_positions["quantity"], y_position, str(item.quantity))
            p.drawString(col_positions["discount"], y_position, f"{item.product.get_best_offer()}%")
            p.drawString(col_positions["total_amount"], y_position, f"${order.grand_total:.2f}")
            p.drawString(col_positions["status"], y_position, order.status)

            y_position -= row_height
            row_count += 1

    p.showPage()
    p.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
    return response



def download_sales_report_excel(request):
    # Filter orders based on the user's selected filter
    filter_option = request.GET.get('filter', 'all')

    if filter_option == 'today':
        orders = Order.objects.filter(created_at__date=timezone.now().date())
    elif filter_option == 'weekly':
        start_of_week = timezone.now() - timedelta(days=timezone.now().weekday())
        orders = Order.objects.filter(created_at__date__gte=start_of_week)
    elif filter_option == 'monthly':
        orders = Order.objects.filter(created_at__month=timezone.now().month)
    elif filter_option == 'yearly':
        orders = Order.objects.filter(created_at__year=timezone.now().year)
    elif filter_option == 'custom':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date and end_date:
            orders = Order.objects.filter(created_at__date__range=[start_date, end_date])
        else:
            orders = Order.objects.all()
    else:
        orders = Order.objects.all()

    # Prepare the data for the Excel file
    data = []
    for order in orders:
        for item in order.items.all():
            data.append({
                'Order ID': order.id,
                'Username': order.user.username,
                'Product Title': item.product.title,
                'Original Price': item.product.original_price,
                'Sold Price': item.total_price,
                'Quantity': item.quantity,
                'Discount': item.product.get_best_offer(),
                'Total Amount': order.grand_total,
                'Status': order.status,
                'Payment Method': order.payment_method,
            })

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Create a response object and set the appropriate headers
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=sales_report.xlsx'

    # Use pandas to write the DataFrame to the response
    df.to_excel(response, index=False, engine='openpyxl')

    return response

def download_sales_report_excel(request):
    # Filter orders based on the user's selected filter
    filter_option = request.GET.get('filter', 'all')

    if filter_option == 'today':
        orders = Order.objects.filter(created_at__date=timezone.now().date())
    elif filter_option == 'weekly':
        start_of_week = timezone.now() - timedelta(days=timezone.now().weekday())
        orders = Order.objects.filter(created_at__date__gte=start_of_week)
    elif filter_option == 'monthly':
        orders = Order.objects.filter(created_at__month=timezone.now().month)
    elif filter_option == 'yearly':
        orders = Order.objects.filter(created_at__year=timezone.now().year)
    elif filter_option == 'custom':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date and end_date:
            orders = Order.objects.filter(created_at__date__range=[start_date, end_date])
        else:
            orders = Order.objects.all()
    else:
        orders = Order.objects.all()

    # Prepare the data for the Excel file
    data = []
    for order in orders:
        for item in order.items.all():
            data.append({
                'Order ID': order.id,
                'Username': order.user.username,
                'Product Title': item.product.title,
                'Original Price': item.product.original_price,
                'Sold Price': item.total_price,
                'Quantity': item.quantity,
                'Discount': item.product.get_best_offer(),
                'Total Amount': order.grand_total,
                'Status': order.status,
                'Payment Method': order.payment_method,
            })

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Create a response object and set the appropriate headers
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=sales_report.xlsx'

    # Use pandas to write the DataFrame to the response
    df.to_excel(response, index=False, engine='openpyxl')

    return response




def generate_invoice(request, order_number):
    order = Order.objects.get(order_number=order_number)
    
   
    context = {
        'order': order,
        'user': order.user,
        'coupon': order.coupon,
    }
    
    # Render the HTML template with the context
    html_string = render_to_string('userprofileside/invoice_template.html', context)
    
    # Convert HTML to PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)
    
    # Create the HTTP response with the PDF file
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order_number}.pdf"'
        return response
    return None


