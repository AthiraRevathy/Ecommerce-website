# store/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm
from .models import Profile, OTPVerification
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from wallet.models import Referral

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        label="", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    first_name = forms.CharField(
        label="", 
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        label="", 
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )

    referral_code = forms.CharField(required=False, label='Referral Code',max_length=50)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


    def clean_referral_code(self):
        referral_code = self.cleaned_data.get('referral_code')
        if referral_code:
            try:
                referral = Referral.objects.get(referral_code=referral_code)
            except Referral.DoesNotExist:
                raise forms.ValidationError("Invalid referral code.")
        return referral_code

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'User Name'})
        self.fields['username'].label = ''
        self.fields['username'].help_text = '<span class="form-text text-muted"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>'
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password1'].label = ''
        self.fields['password1'].help_text = '<ul class="form-text text-muted small"><li>Your password can\'t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can\'t be a commonly used password.</li><li>Your password can\'t be entirely numeric.</li></ul>'
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
        self.fields['password2'].label = ''
        self.fields['password2'].help_text = '<span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span>'



class OTPRequestForm(forms.Form):
    otp = forms.CharField(max_length=6)  # Example field

#class OTPVerificationForm(forms.Form):
    #otp = forms.CharField(max_length=6)  # Example field

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6)
    scenario = forms.CharField(widget=forms.HiddenInput(), required=False)

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No user with this email address.")
        return email

class SetNewPasswordForm(SetPasswordForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
