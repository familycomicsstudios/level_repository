from django.db import migrations


def migrate_scheep_to_punter(apps, schema_editor):
    Profile = apps.get_model('levels', 'Profile')
    Profile.objects.filter(difficulty_system='scheep').update(difficulty_system='punter')


class Migration(migrations.Migration):

    dependencies = [
        ('levels', '0018_profile_dark_mode'),
    ]

    operations = [
        migrations.RunPython(migrate_scheep_to_punter, migrations.RunPython.noop),
    ]
