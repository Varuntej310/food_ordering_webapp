# Generated by Django 5.0.3 on 2024-03-18 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="slug",
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="menu",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="menu_images/"),
        ),
        migrations.AlterField(
            model_name="menu",
            name="is_available",
            field=models.BooleanField(default=True),
        ),
    ]