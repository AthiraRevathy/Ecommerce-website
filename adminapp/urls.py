from django.urls import path
from . import views

app_name = 'adminlog'

urlpatterns = [
    path('admin_login/', views.admin_login, name='admin_login'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),
    path('update-order-status/', views.update_order_status, name='update_order_status'),
    path('order-list/', views.order_list, name='order_list'),  # Assuming you have an order list view
]

