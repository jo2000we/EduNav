from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0011_student_password"),
    ]

    operations = [
        migrations.AddField(
            model_name="appsettings",
            name="openai_model",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="appsettings",
            name="openai_temperature",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
