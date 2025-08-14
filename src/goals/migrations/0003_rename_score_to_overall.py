from django.db import migrations


def rename_score_to_overall(apps, schema_editor):
    Goal = apps.get_model('goals', 'Goal')
    for goal in Goal.objects.exclude(smart_score__isnull=True):
        smart = goal.smart_score
        if isinstance(smart, dict) and 'score' in smart and 'overall' not in smart:
            smart['overall'] = smart.pop('score')
            goal.smart_score = smart
            goal.save(update_fields=['smart_score'])


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0002_overallgoal'),
    ]

    operations = [
        migrations.RunPython(rename_score_to_overall, migrations.RunPython.noop),
    ]
