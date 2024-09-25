    
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import get_variant_details

urlpatterns = [
    path('product_home/', views.product_home, name='product_home'),
    path('add_products/', views.add_products, name='add_products'),
    path('admin_products/', views.admin_products, name='admin_products'),
    path('edit_products/<int:pk>/', views.edit_products, name='edit_products'),
    path('delete_products/<int:pk>/', views.delete_products, name='delete_products'),
    path('category/<int:pk>/delete/', views.delete_category, name='delete_category'),
    path('categories/edit/<int:pk>/', views.edit_category, name='edit_category'),
    path('admin/categories/add/', views.add_category, name='add_category'),
    path('admin/brands/toggle/<int:pk>/', views.toggle_brand_status, name='toggle_brand_status'),
    path('single_product/<int:product_id>/', views.single_product, name='single_product'),
     path('get_variant_details/', get_variant_details, name='get_variant_details'),
    
    
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


