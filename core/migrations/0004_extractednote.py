# Generated by Django 5.2 on 2025-05-20 02:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_studysession_uploaded_file_uploadedfile'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtractedNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='extracted_notes', to='core.studysession')),
            ],
        ),
    ]
