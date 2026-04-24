from django import forms
from decimal import Decimal, ROUND_HALF_UP
from .models import Level, Profile, LevelRating, LevelCompletion, DIFFICULTY_SYSTEM_CHOICES

class LevelForm(forms.ModelForm):
    difficulty = forms.DecimalField(
        max_digits=7,
        decimal_places=2,
        min_value=0,
        max_value=99999,
        label="Difficulty",
        help_text="Use up to 2 decimal places.",
        widget=forms.NumberInput(attrs={"step": "any", "inputmode": "decimal"}),
    )

    def clean_difficulty(self):
        value = self.cleaned_data["difficulty"]
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    class Meta:
        model = Level
        fields = ['name', 'level_code', 'mod_category', 'difficulty', 'original_uploader', 'description']


class LevelRatingForm(forms.ModelForm):
    class Meta:
        model = LevelRating
        fields = ['difficulty_rating', 'quality_rating']

    difficulty_rating = forms.DecimalField(
        max_digits=4,
        decimal_places=2,
        min_value=0,
        max_value=15,
        label="Difficulty rating (Punter scale 0-15)",
        widget=forms.NumberInput(attrs={"step": "any", "inputmode": "decimal"}),
    )
    quality_rating = forms.ChoiceField(
        choices=[(i, f"{i} star{'s' if i != 1 else ''}") for i in range(0, 6)],
        label="Quality rating (0-5 stars)",
    )


class ProfileSettingsForm(forms.ModelForm):
    difficulty_system = forms.ChoiceField(
        choices=DIFFICULTY_SYSTEM_CHOICES,
        label="Preferred difficulty system",
        help_text="Used to render level difficulties across the site.",
    )
    class Meta:
        model = Profile
        fields = ['difficulty_system']


class LevelCompletionForm(forms.ModelForm):
    class Meta:
        model = LevelCompletion
        fields = ['proof']

    proof = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 8, 'maxlength': 5000}),
        max_length=5000,
        label='Proof',
        help_text='Provide proof for this completion (max 5000 characters).',
    )


class ProfilePublicForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name', 'bio']

    display_name = forms.CharField(
        required=False,
        max_length=100,
        label='Display name',
        help_text='Optional public display name shown on your profile.',
    )
    bio = forms.CharField(
        required=False,
        max_length=2000,
        label='Bio',
        help_text='Tell others about yourself (max 2000 characters).',
        widget=forms.Textarea(attrs={'rows': 5, 'maxlength': 2000}),
    )
