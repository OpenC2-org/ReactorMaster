# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-07-14 12:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Capability',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('actuator', models.CharField(max_length=200)),
                ('action', models.CharField(max_length=50)),
                ('remote_id', models.IntegerField()),
                ('remote_name', models.CharField(max_length=200)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='CybOXType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=50)),
                ('template', models.TextField(default='{}', max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_message', models.TextField(max_length=5000)),
                ('created_at', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('upstream_respond_to', models.CharField(max_length=5000, null=True)),
                ('upstream_command_ref', models.CharField(max_length=100, null=True)),
                ('capability', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reactor_master.Capability')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='JobStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='Relay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('url', models.CharField(max_length=400)),
                ('username', models.CharField(blank=True, max_length=200, null=True)),
                ('password', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_message', models.CharField(max_length=5000)),
                ('created_at', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reactor_master.Job')),
            ],
        ),
        migrations.CreateModel(
            name='Target',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=140)),
                ('raw_message', models.TextField(max_length=500)),
                ('cybox_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reactor_master.CybOXType')),
            ],
        ),
        migrations.AddField(
            model_name='job',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reactor_master.JobStatus'),
        ),
        migrations.AddField(
            model_name='job',
            name='target',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reactor_master.Target'),
        ),
        migrations.AddField(
            model_name='capability',
            name='requires',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reactor_master.CybOXType'),
        ),
        migrations.AddField(
            model_name='capability',
            name='via',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reactor_master.Relay'),
        ),
    ]
