# Generated by Django 4.2.4 on 2023-11-14 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0005_alter_examarrangement_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='examarrangement',
            name='date',
            field=models.CharField(max_length=255),
        ),
    ]
