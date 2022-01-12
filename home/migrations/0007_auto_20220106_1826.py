# Generated by Django 3.2.9 on 2022-01-06 18:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_rename_user_portfolio'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='portfolio',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='home.portfolio'),
        ),
        migrations.AddField(
            model_name='portfolio',
            name='name',
            field=models.CharField(default='name', max_length=20),
        ),
    ]
