# Generated by Django 4.2.2 on 2023-06-12 15:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('LittleLemonAPI', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='cart',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='orderitem',
            unique_together=set(),
        ),
    ]
