# usermanagement/forms.py
from django import forms
from .models import Account

class UserCreateForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_blocked']
        widgets = {
            'is_blocked': forms.CheckboxInput(),
        }

class UserEditForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email',]
