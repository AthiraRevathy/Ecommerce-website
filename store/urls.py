from django.urls import path
from . import views
from .views import request_otp_view, verify_otp_view,RequestPasswordResetView, ConfirmPasswordResetView

from django.views.generic import TemplateView



urlpatterns = [
    
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('accounts/login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('search/',views.search,name='search'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('request-otp/', views.request_otp_view, name='request_otp'),
    path('reset-password/', RequestPasswordResetView.as_view(), name='password_reset_request'),
    path('reset-password/confirm/<uidb64>/<token>/', ConfirmPasswordResetView.as_view(), name='password_reset_confirm'),
    path('reset-password/done/', TemplateView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset-password/complete/', TemplateView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    # Other URL patterns...
]
