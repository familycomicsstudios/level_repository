from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('levels', '0017_profile_difficulty_system'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='dark_mode',
            field=models.BooleanField(default=False, help_text='Enable dark theme across the site.'),
        ),
    ]
