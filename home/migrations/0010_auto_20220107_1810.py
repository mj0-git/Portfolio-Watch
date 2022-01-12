# Generated by Django 3.2.9 on 2022-01-07 18:10

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0009_asset_current_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='option_expiry',
            field=models.DateField(blank=True, default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='asset',
            name='option_strike',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='asset',
            name='option_type',
            field=models.CharField(choices=[('call', 'Call'), ('put', 'Put')], default='call', max_length=10),
        ),
        migrations.AlterField(
            model_name='asset',
            name='purchase_date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='asset',
            name='stop_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='asset',
            name='target_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='asset',
            name='type',
            field=models.CharField(choices=[('crypto', 'Crypto'), ('equity', 'Equity'), ('option', 'Option')], default='equity', max_length=10),
        ),
    ]
