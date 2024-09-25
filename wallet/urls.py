from django.urls import path
from . import views

urlpatterns = [
    path('my-wallet/', views.my_wallet, name='my_wallet'),
   path('order/<str:order_number>/request-return/', views.request_return, name='request_return'),
    path('admin/return-requests/', views.admin_return_requests, name='admin_return_requests'),
    path('admin/return-request/<int:return_request_id>/confirm/', views.admin_confirm_return, name='admin_confirm_return'),
    path('admin/return-request/<int:return_request_id>/reject/', views.admin_reject_return, name='admin_reject_return'),
    path('referral/', views.referral_page, name='referral_page'),
    path('order/<str:order_number>/request-cancel/', views.request_cancel_order, name='request_cancel_order'),
    path('admin/review-cancellation-requests/', views.review_cancellation_requests, name='review_cancellation_requests'),
    path('admin/process-cancellation-request/<int:request_id>/<str:action>/', views.process_cancellation_request, name='process_cancellation_request'),
    path('order/<str:order_number>/wallet_payment/', views.wallet_payment, name='wallet_payment'),
]
