from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import SignUpForm, OTPRequestForm
from .models import OTPVerification
from .utils import send_otp
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.cache import never_cache
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from .forms import SignUpForm
from django.contrib.auth import login as auth_login
from django.conf import settings
from .forms import OTPVerificationForm
import logging
from products.models import Product
from usermanagement.models import Account
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import update_session_auth_hash
from django.views import View
from django.contrib.auth.forms import PasswordResetForm
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes, force_str
from wallet.models import Referral,WalletTransaction,Wallet
from decimal import Decimal









@never_cache
def home(request):
    featured_products = Product.objects.filter(is_featured=True)  # or other filter criteria
    return render(request, 'home.html', {'featured_products': featured_products})


def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You have been logged in!")
            return redirect('product_home')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    return render(request, 'login.html', {})


def logout_user(request):
    logout(request)
    request.session.flush()  # Clear all session data
    messages.success(request, "You have been logged out. Thank you for visiting.")
    return redirect('home')


def register_user(request):
    user = None  # Initialize user variable

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            referral_code = form.cleaned_data.get('referral_code')

            # Check if the email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, 'An account with this email already exists.')
                return render(request, 'register.html', {'form': form})

            # Create the user
            user = form.save(commit=False)
            user.email = email
            user.save()

            # Create referral instance
            referral = Referral.objects.create(user=user)

            # Ensure the user has a wallet
            wallet, created = Wallet.objects.get_or_create(user=user)

            # Handle referral code logic
            if referral_code:
                try:
                    referral = Referral.objects.get(referral_code=referral_code)

                    # Award credits to the new user and referrer
                    wallet.balance += Decimal('100.00')
                    wallet.save()

                    referrer = referral.user
                    referrer_wallet, created = Wallet.objects.get_or_create(user=referrer)
                    referrer_wallet.balance += Decimal('100.00')
                    referrer_wallet.save()

                    # Record transactions for both the user and referrer
                    WalletTransaction.objects.create(user=user, transaction_type='Credit', amount=Decimal('50.00'), description='Referral credit')
                    WalletTransaction.objects.create(user=referrer, transaction_type='Credit', amount=Decimal('50.00'), description='Referral bonus')

                    # Add the new user to the referral's list of referred friends
                    referral.referred_friends.add(user)
                    referral.save()

                    messages.success(request, f'You have been referred by {referral.user.username}!')

                except Referral.DoesNotExist:
                    messages.error(request, 'Invalid referral code.')
                    # Proceed even if the referral code is invalid

            # Ensure OTP is always sent
            send_otp(user)
            messages.success(request, 'Account created successfully! Please verify your OTP.')
            
            # Store user ID in session for OTP verification
            request.session['user_id'] = user.id
            return redirect('verify_otp')

        else:
            messages.error(request, 'Error creating account. Please correct the errors below.')

    else:
        form = SignUpForm()

    return render(request, 'register.html', {'form': form})


@login_required
def search(request):
    return render(request, 'search.html', {})


@login_required
def about(request):
    return render(request, 'about.html', {})


@never_cache
@login_required
def search(request):
    return render(request, 'search.html', {})


@never_cache
@login_required
def about(request):
    return render(request, 'about.html', {})



def request_otp_view(request):
    if request.method == 'POST':
        form = OTPRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = send_otp(email)
            if otp is None:
                messages.error(request, 'Failed to send OTP. Please try again later.')
                return render(request, 'request_otp.html', {'form': form})

            try:
                user = User.objects.get(email=email)
                request.session['user_id'] = user.id
                OTPVerification.objects.create(user=user, otp=otp)
                messages.success(request, 'OTP sent to your email. Please check your inbox.')
                return redirect('verify_otp')
            except User.DoesNotExist:
                messages.error(request, 'User not found. Please register first.')
                return redirect('register')
        else:
            messages.error(request, 'Please enter a valid email.')
    else:
        form = OTPRequestForm()
        
    return render(request, 'request_otp.html', {'form': form})

from django.contrib.auth import login
from django.conf import settings

def verify_otp_view(request):
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            user_id = request.session.get('user_id')  # Retrieve user ID from session

            if not user_id:
                messages.error(request, 'User ID not found in session. Please request OTP again.')
                
                return redirect('request_otp')

            try:
                user = User.objects.get(id=user_id)
                otp_record = OTPVerification.objects.filter(user=user, otp=otp).first()

                if otp_record and (timezone.now() - otp_record.created_at) < timedelta(minutes=5):
                    # OTP is valid and not expired
                    backend = settings.AUTHENTICATION_BACKENDS[0]  # Use the first backend
                    login(request, user, backend=backend)
                    messages.success(request, 'OTP verified. You have been logged in.')
                    
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid or expired OTP. Please try again.')
            except User.DoesNotExist:
                messages.error(request, 'User not found. Please register again.')
                
        else:
            messages.error(request, 'Invalid OTP. Please enter the OTP again.')
    else:
        form = OTPVerificationForm()

    return render(request, 'verify_otp.html', {'form': form})


#forgot password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm, PasswordResetForm

class RequestPasswordResetView(View):
    def get(self, request):
        form = PasswordResetForm()
        return render(request, 'password_reset_form.html', {'form': form})

    def post(self, request):
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = User.objects.filter(email=email)
            if associated_users.exists():
                for user in associated_users:
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    reset_link = request.build_absolute_uri(f'/reset-password/confirm/{uid}/{token}/')
                    message = render_to_string('password_reset_email.html', {
                        'user': user,
                        'reset_link': reset_link,
                    })
                    send_mail(
                        'Password Reset Request',
                        message,
                        'from@example.com',
                        [email],
                    )
            return redirect('password_reset_done')
        return render(request, 'password_reset_form.html', {'form': form})

class ConfirmPasswordResetView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                form = SetPasswordForm(user=user)
                return render(request, 'password_reset_confirm.html', {'form': form})
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            print(f"Error in get: {e}")
        return redirect('password_reset_done')

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                form = SetPasswordForm(user=user, data=request.POST)
                if form.is_valid():
                    form.save()
                    return redirect('password_reset_complete')
                else:
                    print(f"Form errors: {form.errors}")
                    return render(request, 'password_reset_confirm.html', {'form': form})
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            print(f"Error in post: {e}")
        return redirect('password_reset_done')
