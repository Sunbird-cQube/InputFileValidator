# Generated by Django 4.1.6 on 2023-04-22 11:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('file_validator', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='podcast',
            name='album',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='podcasts', to='file_validator.album'),
        ),
    ]