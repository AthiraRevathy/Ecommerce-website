# usermanagement/urls.py
# usermanagement/urls.py
from django.urls import path
from . import views

app_name = 'usermanagement'

urlpatterns = [
    
    path('list/', views.list_users, name='list_users'),
    path('delete/<int:user_id>/', views.delete_user, name='delete_user'),
    
]
