

import json
import logging
import razorpay
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from product_cart.models import Order
from django.urls import reverse

# Set up logger
logger = logging.getLogger(__name__)

def payment_view(request, order_id):
    logger.debug(f"Payment view called for order ID: {order_id}")
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    # Retrieve the order
    order = get_object_or_404(Order, id=order_id)
    logger.debug(f"Order retrieved: {order}")

    try:
        # Create a Razorpay order
        razorpay_order = client.order.create({
            'amount': int(order.grand_total * 100),  # Amount in paise
            'currency': 'INR',
            'payment_capture': '1',
            'receipt': str(order.id)
        })
        logger.debug(f"Razorpay order created: {razorpay_order}")

        # Save Razorpay order ID to the Order model
        order.razorpay_order_id = razorpay_order['id']
        order.payment_status = 'Pending'  # Reset payment status to Pending
        order.save()
        return render(request, 'userprofileside/payment.html', {
            'order_id': order_id,
            'amount': order.grand_total * 100,
            'key_id': settings.RAZORPAY_KEY_ID,
            'razorpay_order_id': razorpay_order['id'],
            'currency': 'INR',
            'payment_failure_url': request.build_absolute_uri(reverse('payment_failure', args=[order.id])),
            'payment_success_url': request.build_absolute_uri(reverse('payment_success', args=[order.id])),
        })

    except Exception as e:
        logger.error(f"Error creating Razorpay order: {e}")
        return JsonResponse({'success': False, 'message': 'Could not create payment order'}, status=500)
    

    
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
import razorpay
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def payment_callback(request):
    logger.debug("Payment callback endpoint hit")

    if request.method == 'POST':
        try:
            # Parse Razorpay parameters
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            logger.debug(f"Received callback data: order_id={razorpay_order_id}, payment_id={razorpay_payment_id}, signature={razorpay_signature}")

            if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
                logger.error("Missing required Razorpay parameters.")
                return JsonResponse({'success': False, 'message': 'Missing required parameters.'}, status=400)

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            logger.debug("Payment signature verified successfully.")

            # Update order status
            try:
                with transaction.atomic():
                    order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                    logger.debug(f"Retrieved order: {order.id}, current status: {order.payment_status}")
                    order.payment_status = 'Paid'
                    order.payment_id = razorpay_payment_id
                    order.save()
                    logger.debug(f"Order {order.id} updated to 'Paid'.")

                success_url = request.build_absolute_uri(reverse('payment_success', args=[order.id]))
                return JsonResponse({'success': True, 'redirect_url': success_url})

            except Order.DoesNotExist:
                logger.error(f"Order not found for Razorpay Order ID: {razorpay_order_id}")
                return JsonResponse({'success': False, 'message': 'Order not found.'}, status=404)

        except razorpay.errors.SignatureVerificationError:
            logger.error("Payment verification failed. Invalid signature.")
            if razorpay_order_id:
                try:
                    order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                    logger.debug(f"Order {order.id} found for failed signature.")
                    order.payment_status = 'Failed'
                    order.save()
                    logger.debug(f"Order {order.id} updated to 'Failed'.")
                    failure_url = request.build_absolute_uri(reverse('payment_failure', args=[order.id]))
                    return JsonResponse({'success': False, 'redirect_url': failure_url})

                except Order.DoesNotExist:
                    logger.error(f"Order not found for Razorpay Order ID: {razorpay_order_id}")
                    return JsonResponse({'success': False, 'message': 'Order not found.'}, status=404)

        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return JsonResponse({'success': False, 'message': 'An error occurred.'}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


def payment_success(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return render(request, 'userprofileside/payment_success.html', {
            'order': order,
            'amount': order.grand_total,
            'payment_id': order.payment_id,
            #'payment_id': order.razorpay_order_id,
            
        })
    except Order.DoesNotExist:
        logger.error("Order not found for payment success.")
        return render(request, 'userprofileside/payment_error.html')

def payment_failure(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return render(request, 'userprofileside/payment_failure.html', {
            'order': order,
            'error_description': 'Payment Failed or Cancelled.',
        })
    except Order.DoesNotExist:
        logger.error("Order not found for payment failure.")
        return render(request, 'userprofileside/payment_error.html', {
            'error_description': 'Order not found.',
        })