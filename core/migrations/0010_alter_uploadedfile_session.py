# Generated by Django 5.2 on 2025-05-22 23:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_alter_uploadedfile_session'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadedfile',
            name='session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploaded_files', to='core.studysession'),
        ),
    ]
