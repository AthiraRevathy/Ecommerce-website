# Generated by Django 5.1.1 on 2024-09-22 19:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_cart', '0007_cartitem_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
