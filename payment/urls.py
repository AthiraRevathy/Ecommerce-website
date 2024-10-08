
from django.urls import path
from .views import  payment_view, payment_callback,payment_success,payment_failure

urlpatterns = [
    
    path('payment/<int:order_id>/', payment_view, name='payment_view'),
    path('payment-callback/', payment_callback, name='payment_callback'),
    path('payment-success/<int:order_id>/',payment_success,name='payment_success'),
    #path('payment/success/<int:order_id>/', payment_success, name='payment_success'),
    path('payment/failure/<int:order_id>/', payment_failure, name='payment_failure'),
]
