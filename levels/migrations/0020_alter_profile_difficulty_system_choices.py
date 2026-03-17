from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('levels', '0019_profile_drop_scheep_choice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='difficulty_system',
            field=models.CharField(
                choices=[('punter', 'Punter'), ('michaelchan', 'Michael Chan'), ('grassy', 'Grassy')],
                default='punter',
                help_text='How to display level difficulties across the site.',
                max_length=20,
            ),
        ),
    ]
