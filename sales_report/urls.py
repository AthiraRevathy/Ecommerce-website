from django.urls import path
from . import views

urlpatterns = [
    path('sale-report/', views.sale_report_view, name='sale_report'),
    path('sales_report/pdf/', views.pdf_report_view, name='sales_report_pdf'),
    path('sales_report/download-excel/', views.download_sales_report_excel, name='sales_report_excel'),
     path('invoice/<str:order_number>/', views.generate_invoice, name='generate_invoice'),

]