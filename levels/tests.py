from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Level, LevelRating, LevelCompletion


class LevelRatingTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username='creator', password='pass12345')
        self.rater = User.objects.create_user(username='rater', password='pass12345')
        self.admin_user = User.objects.create_user(username='admin', password='pass12345', is_staff=True)

        self.level = Level.objects.create(
            name='Test Level',
            level_code='abc',
            difficulty=7,
            creator=self.creator,
        )

    def test_rating_is_single_per_user_and_overwrites(self):
        self.client.login(username='rater', password='pass12345')

        detail_url = reverse('levels:level_detail', args=[self.level.id])
        self.client.post(detail_url, {
            'action': 'rate',
            'difficulty_rating': 8,
            'quality_rating': 4,
        })
        self.client.post(detail_url, {
            'action': 'rate',
            'difficulty_rating': 11,
            'quality_rating': 5,
        })

        ratings = LevelRating.objects.filter(level=self.level, user=self.rater)
        self.assertEqual(ratings.count(), 1)

        rating = ratings.first()
        self.assertEqual(rating.difficulty_rating, 11)
        self.assertEqual(rating.quality_rating, 5)

    def test_level_aggregate_ratings_are_updated(self):
        other_rater = User.objects.create_user(username='other', password='pass12345')

        LevelRating.objects.create(level=self.level, user=self.rater, difficulty_rating=10, quality_rating=4)
        LevelRating.objects.create(level=self.level, user=other_rater, difficulty_rating=14, quality_rating=2)

        self.level.refresh_rating_averages()
        self.level.refresh_from_db()

        self.assertEqual(self.level.difficulty_rating, 12)
        self.assertEqual(self.level.quality_rating, 3)

    def test_level_list_defaults_to_difficulty_rating_sort_desc(self):
        level_b = Level.objects.create(
            name='Other Level',
            level_code='xyz',
            difficulty=2,
            creator=self.creator,
            difficulty_rating=3,
        )
        self.level.difficulty_rating = 12
        self.level.save(update_fields=['difficulty_rating'])

        response = self.client.get(reverse('levels:list'))
        page_levels = list(response.context['page_obj'])

        self.assertEqual(page_levels[0].id, self.level.id)
        self.assertEqual(page_levels[1].id, level_b.id)

    def test_upload_seeds_first_difficulty_rating(self):
        self.client.login(username='creator', password='pass12345')

        upload_url = reverse('levels:upload')
        self.client.post(upload_url, {
            'name': 'Uploaded Level',
            'level_code': 'code',
            'mod_category': 'appel',
            'difficulty': 9,
            'original_uploader': '',
            'description': 'desc',
        })

        uploaded = Level.objects.get(name='Uploaded Level')
        seeded = LevelRating.objects.get(level=uploaded, user=self.creator)

        self.assertEqual(seeded.difficulty_rating, 9)
        self.assertIsNone(seeded.quality_rating)
        self.assertEqual(uploaded.difficulty_rating, 9)

    def test_submit_level_completion_requires_login(self):
        response = self.client.get(reverse('levels:submit_level_completion', args=[self.level.id]))
        self.assertEqual(response.status_code, 302)

    def test_submit_level_completion_creates_pending_submission(self):
        self.client.login(username='rater', password='pass12345')
        response = self.client.post(
            reverse('levels:submit_level_completion', args=[self.level.id]),
            {'proof': 'Video proof link and notes'},
        )

        self.assertEqual(response.status_code, 302)
        completion = LevelCompletion.objects.get(user=self.rater, level=self.level)
        self.assertEqual(completion.status, LevelCompletion.STATUS_PENDING)
        self.assertEqual(completion.proof, 'Video proof link and notes')

    def test_approved_completion_is_added_to_profile_stats(self):
        completion = LevelCompletion.objects.create(
            user=self.rater,
            level=self.level,
            proof='Proof text',
        )

        completion.approve()
        self.rater.profile.refresh_from_db()
        completed_ids = self.rater.profile.stats.get('levels_completed', [])
        self.assertIn(self.level.id, completed_ids)

    def test_user_profile_shows_only_directly_uploaded_levels(self):
        Level.objects.create(
            name='Direct Profile Upload',
            level_code='abc',
            difficulty=3,
            creator=self.creator,
            original_uploader='',
        )
        Level.objects.create(
            name='Mirrored Profile Upload',
            level_code='def',
            difficulty=5,
            creator=self.creator,
            original_uploader='Another Creator',
        )

        response = self.client.get(reverse('levels:user_profile', args=[self.creator.username]))

        self.assertContains(response, 'Direct Profile Upload')
        self.assertNotContains(response, 'Mirrored Profile Upload')

    def test_admin_completion_triage_requires_staff(self):
        self.client.login(username='rater', password='pass12345')
        response = self.client.get(reverse('levels:admin_completion_triage'))
        self.assertEqual(response.status_code, 403)

    def test_admin_completion_triage_allows_staff_and_can_approve(self):
        completion = LevelCompletion.objects.create(
            user=self.rater,
            level=self.level,
            proof='Proof text',
            status=LevelCompletion.STATUS_PENDING,
        )

        self.client.login(username='admin', password='pass12345')
        response = self.client.post(
            reverse('levels:admin_completion_triage'),
            {
                'completion_id': completion.id,
                'decision': 'approve',
            },
        )

        self.assertEqual(response.status_code, 302)
        completion.refresh_from_db()
        self.assertEqual(completion.status, LevelCompletion.STATUS_APPROVED)
        self.rater.profile.refresh_from_db()
        self.assertIn(self.level.id, self.rater.profile.stats.get('levels_completed', []))

    def test_my_completion_submissions_shows_newest_first(self):
        old_submission = LevelCompletion.objects.create(
            user=self.rater,
            level=self.level,
            proof='Old proof',
            status=LevelCompletion.STATUS_REJECTED,
        )
        newer_level = Level.objects.create(
            name='New Level',
            level_code='zzz',
            difficulty=1,
            creator=self.creator,
        )
        new_submission = LevelCompletion.objects.create(
            user=self.rater,
            level=newer_level,
            proof='New proof',
            status=LevelCompletion.STATUS_APPROVED,
        )

        self.client.login(username='rater', password='pass12345')
        response = self.client.get(reverse('levels:my_completion_submissions'))
        submissions = list(response.context['submissions'])

        self.assertEqual(submissions[0].id, new_submission.id)
        self.assertEqual(submissions[1].id, old_submission.id)
        self.assertContains(response, 'Approved')
        self.assertContains(response, 'Rejected')

    def test_profile_edit_requires_owner(self):
        self.client.login(username='rater', password='pass12345')
        response = self.client.get(reverse('levels:edit_profile', args=[self.creator.username]))
        self.assertEqual(response.status_code, 403)

    def test_profile_edit_updates_display_name_and_bio(self):
        self.client.login(username='creator', password='pass12345')
        response = self.client.post(
            reverse('levels:edit_profile', args=[self.creator.username]),
            {
                'display_name': 'Creator Display',
                'bio': 'This is my profile bio.',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.creator.profile.refresh_from_db()
        self.assertEqual(self.creator.profile.display_name, 'Creator Display')
        self.assertEqual(self.creator.profile.bio, 'This is my profile bio.')

    def test_profile_shows_total_completions_and_completion_links(self):
        completion = LevelCompletion.objects.create(
            user=self.rater,
            level=self.level,
            proof='Proof text',
        )
        completion.approve(reviewer=self.admin_user)

        response = self.client.get(reverse('levels:user_profile', args=[self.rater.username]))

        self.assertContains(response, 'Total Completions:')
        self.assertContains(response, 'Total Completions:</strong> 1')
        self.assertContains(response, reverse('levels:level_detail', args=[self.level.id]))
        self.assertContains(response, reverse('levels:user_profile', args=[self.rater.username]))
