from django import forms
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
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
        fields = ['display_name', 'scratch_username', 'bio']

    display_name = forms.CharField(
        required=False,
        max_length=100,
        label='Display name',
        help_text='Optional public display name shown on your profile.',
    )
    scratch_username = forms.CharField(
        required=False,
        max_length=100,
        label='Scratch username',
        help_text='Used to load your Scratch profile picture.',
    )
    bio = forms.CharField(
        required=False,
        max_length=2000,
        label='Bio',
        help_text='Tell others about yourself (max 2000 characters).',
        widget=forms.Textarea(attrs={'rows': 5, 'maxlength': 2000}),
    )


class CaseInsensitiveUserCreationForm(UserCreationForm):
    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('A user with that username already exists.')
        return username


class CaseInsensitiveAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = (self.cleaned_data.get('username') or '').strip()
        password = self.cleaned_data.get('password')

        if username and password:
            canonical_user = User.objects.filter(username__iexact=username).first()
            auth_username = canonical_user.username if canonical_user else username
            self.user_cache = authenticate(self.request, username=auth_username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
