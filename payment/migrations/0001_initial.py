# Generated by Django 5.1.1 on 2024-09-06 19:25

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('razorpay_order_id', models.CharField(max_length=100)),
                ('razorpay_payment_id', models.CharField(blank=True, max_length=100, null=True)),
                ('razorpay_signature', models.CharField(blank=True, max_length=100, null=True)),
                ('amount', models.FloatField()),
                ('is_paid', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
