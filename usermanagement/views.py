# usermanagement/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from usermanagement.models import Account
from .forms import UserCreateForm, UserEditForm
from django.contrib.auth.models import User

def list_users(request):
    users = User.objects.all()
    print(users)
    return render(request, 'adminside/list_users.html', {'users': users})


def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        if user.is_active:
            # Block the user
            user.is_active = False
            messages.success(request, f'User {user.username} has been blocked.')
        else:
            # Unblock the user
            user.is_active = True
            messages.success(request, f'User {user.username} has been unblocked.')
        user.save()
        return redirect('usermanagement:list_users')

    # Ensure the GET request correctly returns the template
    return render(request, 'adminside/delete_user.html', {'user': user})

