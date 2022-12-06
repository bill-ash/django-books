# Generated by Django 4.0.4 on 2022-12-01 05:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('file_path', models.CharField(blank=True, max_length=90, null=True)),
                ('app_url', models.CharField(blank=True, max_length=90, null=True)),
                ('qbid', models.CharField(default=uuid.uuid4, max_length=50)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('password', models.CharField(default='test', max_length=30)),
                ('is_active', models.BooleanField(default=True)),
                ('config', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TicketQueue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticket', models.CharField(default=uuid.uuid4, max_length=123)),
                ('status', models.CharField(choices=[('1', 'Created'), ('2', 'Approved'), ('3', 'Processing'), ('4', 'Success'), ('5', 'Error'), ('6', 'Failed')], default='1', max_length=5)),
                ('method', models.CharField(choices=[('GET', 'GET'), ('POST', 'POST'), ('PATCH', 'PATCH')], default='GET', max_length=5)),
                ('model', models.CharField(max_length=63)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
