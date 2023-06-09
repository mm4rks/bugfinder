# Generated by Django 4.2 on 2023-05-24 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('samples', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Summary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dewolf_current_commit', models.TextField(blank=True, null=True)),
                ('avg_dewolf_decompilation_time', models.FloatField(blank=True, null=True)),
                ('total_functions', models.IntegerField(blank=True, null=True)),
                ('total_errors', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'summary',
                'managed': False,
            },
        ),
    ]
