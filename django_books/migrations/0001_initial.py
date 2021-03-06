# Generated by Django 4.0.4 on 2022-05-31 14:06

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('qbid', models.CharField(default=uuid.uuid4, max_length=50)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('password', models.CharField(default='test', max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='TicketQueue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticket', models.UUIDField(default=uuid.uuid4)),
                ('status', models.CharField(choices=[('1', 'Created'), ('5', 'Approved'), ('2', 'Running'), ('6', 'Error'), ('3', 'Failed'), ('4', 'Success')], default='1', max_length=15)),
                ('method', models.CharField(choices=[('POST', 'POST'), ('GET', 'GET')], default='GET', max_length=10)),
                ('model', models.CharField(max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
