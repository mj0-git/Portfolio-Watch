# Generated by Django 3.2.9 on 2022-01-07 01:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0008_alter_portfolio_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='current_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]