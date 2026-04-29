import json
import logging
import os

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from urllib import request as urlrequest, error as urlerror


DIFFICULTY_SYSTEM_CHOICES = [
    ("punter", "Punter"),
    ("michaelchan", "Michael Chan"),
    ("grassy", "Grassy"),
]


def _median_value(values):
    if not values:
        return None

    sorted_values = sorted(values)
    count = len(sorted_values)
    middle = count // 2

    if count % 2 == 1:
        return sorted_values[middle]

    return (sorted_values[middle - 1] + sorted_values[middle]) / 2


def default_profile_stats():
    return {
        "levelpoints": 0,
        "levels_completed": [],
    }


logger = logging.getLogger(__name__)


def _send_completion_approved_webhook(completion):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("WEBHOOK_URL")
    if not webhook_url:
        return

    role_id = "1499065510866714644"
    mention_role = float(completion.level.difficulty) >= 5

    creator_name = completion.level.creator.username if completion.level.creator else 'Deleted user'

    ping_prefix = f"<@&{role_id}> " if mention_role else ""

    content_str = (
        f"{ping_prefix}**{completion.user.username}** has completed the level "
        f"**{completion.level.name}** by {creator_name} (Difficulty: {completion.level.difficulty})."
    )

    payload_obj = {"content": content_str}
    if mention_role:
        # Explicitly allow the role to be mentioned to avoid permission stripping.
        payload_obj["allowed_mentions"] = {"roles": [role_id]}

    payload = json.dumps(payload_obj).encode("utf-8")
    request = urlrequest.Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AppelWorkshop/1.0 (+https://workshop.appelgame.net)",
            "Connection": "close",
        },
        method="POST",
    )

    try:
        with urlrequest.urlopen(request, timeout=5) as resp:
            return
    except urlerror.HTTPError as exc:
        # Read response body for debugging
        try:
            body = exc.read().decode('utf-8', errors='replace')
        except Exception:
            body = '<unreadable response body>'
        logger.exception("Completion webhook HTTPError for %s: %s", completion.id, exc)
        print(
            f"[completion webhook] HTTPError for {completion.level.name} by {completion.user.username}: {exc.code} {exc.reason} - {body}"
        )
        return
    except Exception as exc:
        logger.exception("Completion webhook failed for %s", completion.id)
        print(
            f"[completion webhook] failed for {completion.level.name} by {completion.user.username}: {exc}"
        )
        return

class Level(models.Model):

    MOD_CHOICES = [
        ('appel', 'Appel'),
        ('appelp', 'Appel+'),
        ('appelm', 'Appel Multiplayer'),
        ('sheepel', 'Sheepel'),
        ('appel-playground', "Appel Playground"),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=100)
    level_code = models.TextField(max_length=10000, blank=True, default="")
    description = models.TextField(null=True, blank=True, default="", max_length=2000)
    original_uploader = models.CharField(null=True, blank=True, default="", max_length=100, help_text="The original creator of the level. Leave blank if this was you.")
    other_creators = models.TextField(blank=True, default="", help_text="Optional: comma-separated usernames or names.")
    url = models.URLField(blank=True, default="")
    video_url = models.URLField(blank=True, default="", help_text="Optional YouTube link.")
    difficulty = models.FloatField(default=0, help_text="The difficulty (in the Punter scale, more info <a href='https://appel.miraheze.org/wiki/Difficulty'>here</a>)")
    difficulty_rating = models.FloatField(null=True, blank=True)
    quality_rating = models.FloatField(null=True, blank=True)
    level_ratings = models.JSONField(default=list, blank=True)
    mod_category = models.CharField(max_length=50, choices=MOD_CHOICES, default='appel')

    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="levels")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        creator_name = self.creator.username if self.creator else 'Deleted user'
        return f"{self.name} - {creator_name}"

    def refresh_rating_averages(self):
        difficulty_values = [
            float(value)
            for value in self.ratings.values_list('difficulty_rating', flat=True)
        ]
        quality_values = [
            float(value)
            for value in self.ratings.values_list('quality_rating', flat=True)
            if value is not None
        ]

        self.difficulty_rating = _median_value(difficulty_values)
        self.quality_rating = _median_value(quality_values)
        self.save(update_fields=['difficulty_rating', 'quality_rating'])


class LevelRating(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='level_ratings')
    difficulty_rating = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(15)],
    )
    quality_rating = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['level', 'user'], name='unique_level_rating_per_user')
        ]

    def __str__(self):
        return f"{self.user.username} rating for {self.level.name}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    stats = models.JSONField(default=default_profile_stats)
    display_name = models.CharField(max_length=100, blank=True, default='')
    scratch_username = models.CharField(max_length=100, blank=True, default='')
    bio = models.TextField(max_length=2000, blank=True, default='')
    difficulty_system = models.CharField(
        max_length=20,
        choices=DIFFICULTY_SYSTEM_CHOICES,
        default="punter",
        help_text="How to display level difficulties across the site.",
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Comment(models.Model):
    level = models.ForeignKey('Level', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.level.name}"


class LevelCompletion(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='level_completions')
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='completion_submissions')
    proof = models.TextField(max_length=5000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_level_completions',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'level'], name='unique_completion_per_user_level')
        ]

    def __str__(self):
        return f"{self.user.username} completion for {self.level.name} ({self.status})"

    def _add_level_to_profile_completion_stats(self):
        profile = self.user.profile
        stats = profile.stats or {}
        levels_completed = stats.get('levels_completed', [])
        if self.level_id not in levels_completed:
            levels_completed.append(self.level_id)
            stats['levels_completed'] = levels_completed
            profile.stats = stats
            profile.save(update_fields=['stats'])

    def approve(self, reviewer=None):
        self.status = self.STATUS_APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])
        self._add_level_to_profile_completion_stats()
        _send_completion_approved_webhook(self)

    def reject(self, reviewer=None):
        self.status = self.STATUS_REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])

