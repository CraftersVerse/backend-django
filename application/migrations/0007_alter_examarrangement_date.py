# Generated by Django 4.2.4 on 2023-11-14 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0006_alter_examarrangement_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='examarrangement',
            name='date',
            field=models.DateField(),
        ),
    ]
