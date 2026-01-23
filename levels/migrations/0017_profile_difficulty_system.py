from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('levels', '0016_alter_level_difficulty'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='difficulty_system',
            field=models.CharField(choices=[('punter', 'Punter'), ('michaelchan', 'Michael Chan'), ('scheep', 'Scheep')], default='punter', help_text='How to display level difficulties across the site.', max_length=20),
        ),
    ]
