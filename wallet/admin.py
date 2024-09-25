from django.contrib import admin
from .models import Wallet, WalletTransaction, ReturnRequest, CancellationRequest

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'created_at', 'description')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__username', 'description')

@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('order__order_number', 'status')

@admin.register(CancellationRequest)
class CancellationRequestAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'requested_at')
    list_filter = ('status',)
    search_fields = ('order__order_number', 'status')
