from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lessons", "0003_classroom"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="klassengruppe",
        ),
        migrations.AddField(
            model_name="user",
            name="classroom",
            field=models.ForeignKey(null=True, blank=True, on_delete=models.SET_NULL, to="lessons.classroom"),
        ),
    ]

