# Generated by Django 3.2.9 on 2022-01-07 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0012_auto_20220107_2023'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portfolio',
            name='type',
            field=models.CharField(choices=[('investment', 'Investment'), ('saving', 'Saving')], default='investment', max_length=10),
        ),
    ]
