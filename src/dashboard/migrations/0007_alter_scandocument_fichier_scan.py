# Generated by Django 5.2.1 on 2025-06-12 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0006_alter_scanpage_fichier_page'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scandocument',
            name='fichier_scan',
            field=models.ImageField(blank=True, null=True, upload_to='scans/'),
        ),
    ]
