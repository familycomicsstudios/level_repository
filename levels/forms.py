from django import forms
from .models import Level

class LevelForm(forms.ModelForm):
    class Meta:
        model = Level
        fields = ['name', 'level_code', 'mod_category', 'difficulty', 'original_uploader', 'description']
