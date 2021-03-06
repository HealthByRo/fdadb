# Generated by Django 2.1.3 on 2018-11-21 13:16

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MedicationName',
            fields=[
                ('name', models.CharField(help_text='Commercial Name (e.g. Viagra)', max_length=255, primary_key=True, serialize=False)),
                ('active_substances', django_extensions.db.fields.json.JSONField(blank=True, default=[], help_text='List of active substances')),
            ],
        ),
        migrations.CreateModel(
            name='MedicationNDC',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ndc', models.CharField(db_index=True, max_length=12, unique=True)),
                ('manufacturer', models.CharField(db_index=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='MedicationStrength',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strength', django_extensions.db.fields.json.JSONField(blank=True, default={}, help_text='For example:\n    {\n        “Sildenafil”: { “strength”: 3, “unit”: “mg/1” }\n    }\n    ')),
                ('medication_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fdadb.MedicationName')),
            ],
        ),
        migrations.AlterModelOptions(
            name='medicationname',
            options={'ordering': ('name',)},
        ),
        migrations.AddField(
            model_name='medicationndc',
            name='medication_strength',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fdadb.MedicationStrength'),
        ),
    ]
