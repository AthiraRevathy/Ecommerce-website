# Generated by Django 5.0.7 on 2024-08-17 05:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_remove_product_featured_brand_category_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='color',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='colors/'),
        ),
    ]
