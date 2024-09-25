

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
        order.save()
        return render(request, 'userprofileside/payment.html', {
            'order_id': order_id,
            'amount': order.grand_total * 100,
            'key_id': settings.RAZORPAY_KEY_ID,
            'razorpay_order_id': razorpay_order['id'],
            'currency': 'INR'
        })

    except Exception as e:
        logger.error(f"Error creating Razorpay order: {e}")
        return JsonResponse({'success': False, 'message': 'Could not create payment order'}, status=500)

@csrf_exempt
def payment_callback(request):
    logger.debug("Payment callback endpoint hit")
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.debug(f"Received callback data: {data}")

            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_signature = data.get('razorpay_signature')

            # Create Razorpay client instance
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Verify the payment signature
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            logger.debug("Payment signature verified successfully.")

            # Update order status
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            order.status = 'Paid'  # Update the order status
            order.save()
            success_url = reverse('payment_success', args=[order.id])
            logger.debug(f"Redirecting to success page for order ID: {order.id}")

            # Return success response with redirect URL
            return JsonResponse({'success': True, 'redirect_url': success_url})

        except razorpay.errors.SignatureVerificationError:
            logger.error("Payment verification failed.")
            return JsonResponse({'success': False, 'message': 'Payment verification failed.'})
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error: {e}")
            return JsonResponse({'success': False, 'message': 'Invalid JSON'})
        except Order.DoesNotExist:
            logger.error(f"Order not found for Razorpay Order ID: {razorpay_order_id}")
            return JsonResponse({'success': False, 'message': 'Order not found.'})
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return JsonResponse({'success': False, 'message': 'An error occurred.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

def payment_success(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return render(request, 'userprofileside/payment_success.html', {
            'order': order,
            'amount': order.grand_total,
            'payment_id': order.razorpay_order_id,
        })
    except Order.DoesNotExist:
        logger.error("Order not found for payment success.")
        return render(request, 'userprofileside/payment_error.html')

