from __future__ import annotations

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("lessons", "0002_lessonsession_use_ai"),
    ]

    operations = [
        migrations.CreateModel(
            name="Classroom",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ("name", models.CharField(max_length=200)),
                ("code", models.CharField(max_length=50, blank=True, null=True, unique=True)),
                ("use_ai", models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name="lessonsession",
            name="classroom",
            field=models.ForeignKey(null=True, blank=True, on_delete=models.SET_NULL, to="lessons.classroom"),
        ),
        migrations.AlterField(
            model_name="lessonsession",
            name="use_ai",
            field=models.BooleanField(null=True, blank=True),
        ),
    ]

