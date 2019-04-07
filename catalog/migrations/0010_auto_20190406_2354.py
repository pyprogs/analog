# Generated by Django 2.1.5 on 2019-04-06 23:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0009_auto_20190406_2346'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attribute',
            name='category',
        ),
        migrations.AddField(
            model_name='category',
            name='attributes',
            field=models.ManyToManyField(blank=True, to='catalog.Attribute', verbose_name='Атрибуты'),
        ),
    ]