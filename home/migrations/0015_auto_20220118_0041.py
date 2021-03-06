# Generated by Django 3.2.9 on 2022-01-18 00:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_auto_20220115_0023'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolio',
            name='bookval',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='c_yield',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='marketval',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='net_cash',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='p_yield',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
