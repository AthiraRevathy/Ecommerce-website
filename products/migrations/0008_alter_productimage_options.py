# Generated by Django 5.0.7 on 2024-08-31 21:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_alter_product_quantity'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productimage',
            options={'ordering': ['-is_main']},
        ),
    ]
