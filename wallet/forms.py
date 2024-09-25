from django import forms
from .models import ReturnRequest, CancellationRequest

class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = ['order', 'reason', 'status']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
            'status': forms.Select(choices=ReturnRequest.STATUS_CHOICES),
        }

class CancellationRequestForm(forms.ModelForm):
    class Meta:
        model = CancellationRequest
        fields = ['order', 'reason', 'admin_comment', 'status']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
            'admin_comment': forms.Textarea(attrs={'rows': 3}),
            'status': forms.Select(choices=CancellationRequest.STATUS_CHOICES),
        }
