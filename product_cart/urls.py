
from django.urls import path
from . import views

urlpatterns = [
   
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart_summary/', views.cart_summary, name='cart_summary'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('address/add/', views.add_address, name='add_address'),
    path('address/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('userprofile/', views.user_profile, name='user_profile'),
    path('order/cancel/<str:order_number>/', views.cancel_order, name='cancel_order'),
    path('address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    path('checkout/',views.checkout,name='checkout'),
    path('order-detail/<str:order_number>/', views.order_detail, name='order_detail'),
    path('order-summary/<uuid:order_number>/', views.order_summary, name='order_summary'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-success/<str:order_number>/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('profile_main/',views.profile_main,name='profile_main'),
    path('address_display/', views.address_display, name='address_display'),
    path('update_cart/', views.update_cart, name='update_cart'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/add/', views.coupon_add, name='coupon_add'),
    path('coupons/edit/<int:pk>/', views.coupon_edit, name='coupon_edit'),
    path('coupons/delete/<int:pk>/', views.coupon_delete, name='coupon_delete'),
    path('update_cart/', views.update_cart, name='update_cart'),
  
]
