# Generated by Django 4.0.4 on 2022-07-25 11:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qbwc', '0003_customer__batch_id_customer__batch_status_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customer',
            old_name='_created_at',
            new_name='_time_created',
        ),
        migrations.RenameField(
            model_name='customer',
            old_name='_last_updated',
            new_name='_time_modified',
        ),
    ]
