from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from decimal import Decimal
from django.db.models import Q
from django.core.paginator import Paginator
from product_cart.models import Order
from .models import CancellationRequest, WalletTransaction, ReturnRequest, Wallet
from usermanagement.models import Account
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Wallet, WalletTransaction,Referral
from decimal import Decimal

@login_required
def my_wallet(request):
    user = request.user
    
    # Handle the case where the user may not have a wallet
    try:
        wallet = Wallet.objects.get(user=user)
        wallet_balance = wallet.balance
    except Wallet.DoesNotExist:
        wallet = None
        wallet_balance = Decimal('0.00')


    # Debugging output


    # Debugging output (remove in production)
    print(f"User: {user}, Wallet Balance: {wallet_balance}")

    # Fetch transactions for the user
    transactions = WalletTransaction.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'wallet': wallet,
        'wallet_balance': wallet_balance,
        'transactions': transactions,
    }
    
    return render(request, 'userprofileside/my_wallet.html', context)





def request_return(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    # Handle POST request (form submission)
    if request.method == 'POST':
        if order.status == 'Delivered' and not hasattr(order, 'return_request'):
            # Get the reason from the form submission
            reason = request.POST.get('return_reason')

            # Ensure the reason is provided
            if not reason:
                messages.error(request, 'Please provide a reason for your return request.')
                return redirect('request_return', order_number=order_number)

            # Create the return request
            ReturnRequest.objects.create(
                order=order,
                reason=reason,
                status='Requested'
            )
            messages.success(request, 'Return request has been submitted.')
            return redirect('order_detail', order_number=order_number)
        else:
            messages.error(request, 'Return requests can only be made for delivered orders or a request already exists.')

    # Handle GET request (display the form)
    #return render(request, 'return_request_form.html', {'order': order})



def admin_confirm_return(request, return_request_id):
    return_request = get_object_or_404(ReturnRequest, id=return_request_id)
    order = return_request.order

    if return_request.status == 'Requested':
        # Start a transaction to ensure atomic operations
        with transaction.atomic():
            # Confirm the return request
            return_request.status = 'Confirmed'
            return_request.save()

            # Update order status
            order.status = 'Returned'
            order.payment_status = 'Refunded'
            order.save()

            # Get the user associated with the order
            user = order.user
            if user:
                # Try to get or create the user's wallet
                wallet, created = Wallet.objects.get_or_create(user=user)

                # Ensure wallet balance is a Decimal
                wallet_balance = wallet.balance if wallet else Decimal('0.00')

                # Calculate the refund amount after deducting the shipping fee
                refund_amount = Decimal(order.grand_total) - Decimal(order.shipping_fee)

                # Credit the wallet
                wallet.balance = wallet_balance + refund_amount
                wallet.save()

                # Record the wallet transaction
                WalletTransaction.objects.create(
                    user=user,
                    amount=refund_amount,
                    transaction_type='Credit',
                    description=f'Refund for order {order.order_number}'
                )

                # Update product quantities
                for item in order.items.all():
                    product = item.product
                    product.quantity += item.quantity
                    product.save()

                # Show success message
                messages.success(request, 'Return request confirmed, wallet credited, and product quantities updated.')
            else:
                messages.error(request, 'User does not exist.')

    else:
        messages.error(request, 'Return request cannot be confirmed.')

    return redirect('order_detail', order_number=order.order_number)


def admin_reject_return(request, return_request_id):
    return_request = get_object_or_404(ReturnRequest, id=return_request_id)

    if return_request.status == 'Requested':
        # Reject the return request
        return_request.status = 'Rejected'
        return_request.save()

        messages.success(request, 'Return request rejected.')
    else:
        messages.error(request, 'Return request cannot be rejected.')

    return redirect('admin_return_requests')


def admin_return_requests(request):
    search_query = request.GET.get('search', '')

    # Filter return requests based on search query
    return_requests = ReturnRequest.objects.all()
    if search_query:
        return_requests = return_requests.filter(
            Q(order__order_number__icontains=search_query) |
            Q(reason__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    return_requests = return_requests.order_by('-created_at')
    
    # Paginate the return requests
    paginator = Paginator(return_requests, 10)  # Show 10 return requests per page
    page_number = request.GET.get('page')
    return_requests_page = paginator.get_page(page_number)

    return render(request, 'adminside/admin_return_requests.html', {
        'return_requests': return_requests_page,
        'search_query': search_query
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Order, CancellationRequest

@login_required
def request_cancel_order(request, order_number):
    if request.method == 'POST':
        # Get the cancellation reason from the POST data
        reason = request.POST.get('reason', None)

        # Fetch the order for the current user
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        
        if order.status not in ['Cancelled', 'Delivered']:
            # Create a cancellation request, allowing reason to be None
            cancellation_request, created = CancellationRequest.objects.get_or_create(
                order=order, 
                defaults={'reason': reason, 'status': 'Pending'}  # Allow reason to be None
            )
            if created:
                messages.success(request, "Cancellation request submitted successfully. The admin will review it.")
            else:
                messages.info(request, "A cancellation request for this order already exists.")
        else:
            messages.info(request, "Order is already cancelled or delivered.")
    
    return redirect('order_detail', order_number=order_number)


@user_passes_test(lambda u: u.is_superuser)
def review_cancellation_requests(request):
    requests = CancellationRequest.objects.filter(status='Pending')
    return render(request, 'adminside/review_cancellation_requests.html', {'requests': requests})


@user_passes_test(lambda u: u.is_superuser)
def process_cancellation_request(request, request_id, action):
    cancellation_request = get_object_or_404(CancellationRequest, id=request_id)
    order = cancellation_request.order

    if action == 'approve':
        # Update order and cancellation request statuses
        order.status = 'Cancelled'
        order.payment_status = 'Refunded'
        order.save()
        cancellation_request.status = 'Confirmed'
        
        # Restore product quantities
        for item in order.items.all():
            product = item.product
            product.quantity += item.quantity
            product.save()
        
        # Process the wallet refund
        user = order.user
        wallet, created = Wallet.objects.get_or_create(user=user)

        # Ensure wallet balance is a Decimal
        wallet_balance = wallet.balance if wallet else Decimal('0.00')
        refund_amount = Decimal(order.grand_total)

        wallet.balance = wallet_balance + refund_amount
        wallet.save()

        # Log the wallet transaction
        WalletTransaction.objects.create(
            user=user,
            transaction_type='Credit',
            amount=refund_amount,
            description=f'Refund for cancelled order {order.order_number}'
        )
        
        messages.success(request, "Cancellation request approved and order cancelled.")
    elif action == 'reject':
        cancellation_request.status = 'Rejected'
        messages.success(request, "Cancellation request rejected.")
    
    # Save the updated cancellation request status
    cancellation_request.save()

    # Store details in the session to display after redirect
    request.session['cancellation_details'] = {
        'order_number': str(order.order_number),
        'requested_at': cancellation_request.requested_at.strftime("%Y-%m-%d %H:%M"),
        'status': cancellation_request.status,
        'admin_comment': cancellation_request.admin_comment,
        'reason': cancellation_request.reason,
    }

    # Redirect to the order detail page
    return redirect('order_detail', order_number=order.order_number)


@login_required
def wallet_payment(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    user = request.user

    wallet = Wallet.objects.filter(user=user).first()
    wallet_balance = wallet.balance if wallet else Decimal('0.00')

    if wallet_balance < Decimal(order.grand_total):
        return JsonResponse({'status': 'error', 'message': 'Insufficient wallet balance.'})

    # Deduct from wallet
    wallet.balance = wallet_balance - Decimal(order.grand_total)
    wallet.save()

    # Update order status
    order.payment_status = 'Completed'
    order.status = 'Ordered'
    order.save()

    # Log wallet transaction
    WalletTransaction.objects.create(
        user=user,
        transaction_type='Debit',
        amount=Decimal(order.grand_total),
        description=f'Payment for Order {order_number}'
    )

    messages.success(request, 'Payment completed successfully with wallet.')
    return JsonResponse({'status': 'success', 'message': 'Payment successful.'})


from django.shortcuts import render, redirect
from .models import Referral

def referral_page(request):
    # Check if the user is logged in
    if request.user.is_authenticated:
        # Fetch the referral object related to the logged-in user
        referral = Referral.objects.filter(user=request.user).first()

        # Prepare context
        context = {
            'referral': referral,
            'friends': referral.referred_friends.all() if referral else [],  # Include referred friends
        }

        # Check if a referral was found
        if referral:
            return render(request, 'userprofileside/referral_page.html', context)
        else:
            return render(request, 'userprofileside/referral_page.html', {'message': 'No referral found for your account.'})
    else:
        return redirect('login')  # Redirect to the login page if not authenticated
