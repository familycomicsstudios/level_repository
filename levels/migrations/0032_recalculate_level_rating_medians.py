from django.db import migrations


def recalculate_level_rating_medians(apps, schema_editor):
    Level = apps.get_model('levels', 'Level')

    for level in Level.objects.all():
        difficulty_values = sorted(
            float(value)
            for value in level.ratings.values_list('difficulty_rating', flat=True)
        )
        quality_values = sorted(
            float(value)
            for value in level.ratings.values_list('quality_rating', flat=True)
            if value is not None
        )

        difficulty_rating = None
        if difficulty_values:
            middle = len(difficulty_values) // 2
            if len(difficulty_values) % 2 == 1:
                difficulty_rating = difficulty_values[middle]
            else:
                difficulty_rating = (difficulty_values[middle - 1] + difficulty_values[middle]) / 2

        quality_rating = None
        if quality_values:
            middle = len(quality_values) // 2
            if len(quality_values) % 2 == 1:
                quality_rating = quality_values[middle]
            else:
                quality_rating = (quality_values[middle - 1] + quality_values[middle]) / 2

        level.difficulty_rating = difficulty_rating
        level.quality_rating = quality_rating
        level.save(update_fields=['difficulty_rating', 'quality_rating'])


class Migration(migrations.Migration):
    dependencies = [
        ('levels', '0031_alter_level_level_code_alter_level_mod_category'),
    ]

    operations = [
        migrations.RunPython(recalculate_level_rating_medians, migrations.RunPython.noop),
    ]
