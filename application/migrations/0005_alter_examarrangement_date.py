# Generated by Django 4.2.4 on 2023-11-14 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0004_alter_examarrangement_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='examarrangement',
            name='date',
            field=models.DateField(),
        ),
    ]