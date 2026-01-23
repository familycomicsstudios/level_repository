from django import forms
from .models import Level, Profile, DIFFICULTY_SYSTEM_CHOICES

class LevelForm(forms.ModelForm):
    class Meta:
        model = Level
        fields = ['name', 'level_code', 'mod_category', 'difficulty', 'original_uploader', 'description']


class ProfileSettingsForm(forms.ModelForm):
    difficulty_system = forms.ChoiceField(
        choices=DIFFICULTY_SYSTEM_CHOICES,
        label="Preferred difficulty system",
        help_text="Used to render level difficulties across the site.",
    )
    dark_mode = forms.BooleanField(
        label="Enable dark theme",
        help_text="Use dark theme across the site.",
        required=False,
    )

    class Meta:
        model = Profile
        fields = ['difficulty_system', 'dark_mode']
