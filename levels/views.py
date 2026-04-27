from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Level, Comment, LevelRating, LevelCompletion
from django.contrib.auth.models import User
import math
from django.urls import reverse
from .forms import (
    LevelForm,
    ProfileSettingsForm,
    LevelRatingForm,
    LevelCompletionForm,
    ProfilePublicForm,
    CaseInsensitiveUserCreationForm,
    CaseInsensitiveAuthenticationForm,
)
from django.contrib.auth.views import LoginView
import django.contrib.auth
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
import time
from .profanity import find_profanity


API_RATE_LIMIT_WINDOW_SECONDS = 60
API_RATE_LIMIT_MAX_CALLS = 60


def _client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def _allow_api_request(request, scope='global'):
    ip = _client_ip(request)
    now = time.time()
    window = int(now // API_RATE_LIMIT_WINDOW_SECONDS)
    key = f"api:rate:{scope}:{ip}:{window}"

    cache.add(key, 0, timeout=API_RATE_LIMIT_WINDOW_SECONDS + 5)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=API_RATE_LIMIT_WINDOW_SECONDS + 5)
        count = 1

    if count > API_RATE_LIMIT_MAX_CALLS:
        retry_after = int(API_RATE_LIMIT_WINDOW_SECONDS - (now % API_RATE_LIMIT_WINDOW_SECONDS))
        return False, retry_after
    return True, 0


def _serialize_level(request, level):
    creator_display_name = level.creator.profile.display_name if getattr(level.creator, 'profile', None) and level.creator.profile.display_name else level.creator.username
    return {
        'id': level.id,
        'name': level.name,
        'creator': {
            'username': level.creator.username,
            'display_name': creator_display_name,
            'profile_url': request.build_absolute_uri(reverse('levels:user_profile', args=[level.creator.username])),
        },
        'mod_category': level.mod_category,
        'mod_category_label': level.get_mod_category_display(),
        'difficulty': level.difficulty,
        'difficulty_rating': level.difficulty_rating,
        'quality_rating': level.quality_rating,
        'description': level.description,
        'original_uploader': level.original_uploader,
        'other_creators': level.other_creators,
        'url': level.url,
        'video_url': level.video_url,
        'created_at': level.created_at.isoformat() if level.created_at else None,
        'detail_url': request.build_absolute_uri(reverse('levels:level_detail', args=[level.id])),
    }


def _serialize_level_detail(request, level):
    """Serialize level with full details including level_code for detail endpoint."""
    data = _serialize_level(request, level)
    data['level_code'] = level.level_code
    return data


def _serialize_user_profile(request, user):
    profile = user.profile
    uploaded_levels = Level.objects.filter(creator=user).order_by('-created_at')
    approved_completions = LevelCompletion.objects.filter(
        user=user,
        status=LevelCompletion.STATUS_APPROVED,
    ).select_related('level').order_by('-submitted_at')

    return {
        'username': user.username,
        'display_name': profile.display_name,
        'bio': profile.bio,
        'scratch_username': profile.scratch_username,
        'date_joined': user.date_joined.isoformat() if user.date_joined else None,
        'difficulty_system': profile.difficulty_system,
        'profile_url': request.build_absolute_uri(reverse('levels:user_profile', args=[user.username])),
        'uploaded_levels_count': uploaded_levels.count(),
        'approved_completions_count': approved_completions.count(),
        'uploaded_levels': [
            {
                'id': level.id,
                'name': level.name,
                'detail_url': request.build_absolute_uri(reverse('levels:level_detail', args=[level.id])),
                'difficulty_rating': level.difficulty_rating,
                'quality_rating': level.quality_rating,
            }
            for level in uploaded_levels
        ],
        'approved_completions': [
            {
                'level_id': submission.level.id,
                'level_name': submission.level.name,
                'level_url': request.build_absolute_uri(reverse('levels:level_detail', args=[submission.level.id])),
                'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
            }
            for submission in approved_completions
        ],
    }


def api_docs(request):
    return render(request, 'levels/api_docs.html')


def api_levels(request):
    allowed, retry_after = _allow_api_request(request, scope='levels')
    if not allowed:
        return JsonResponse(
            {
                'error': 'rate_limited',
                'detail': 'Too many API requests from this IP address.',
                'retry_after_seconds': retry_after,
            },
            status=429,
        )

    levels = Level.objects.select_related('creator', 'creator__profile').order_by('-created_at')
    return JsonResponse(
        {
            'count': levels.count(),
            'results': [_serialize_level(request, level) for level in levels],
        }
    )


def api_level_detail(request, level_id):
    allowed, retry_after = _allow_api_request(request, scope='levels')
    if not allowed:
        return JsonResponse(
            {
                'error': 'rate_limited',
                'detail': 'Too many API requests from this IP address.',
                'retry_after_seconds': retry_after,
            },
            status=429,
        )

    level = get_object_or_404(Level.objects.select_related('creator', 'creator__profile'), id=level_id)
    return JsonResponse(_serialize_level_detail(request, level))


def api_profile_detail(request, username):
    allowed, retry_after = _allow_api_request(request, scope='profiles')
    if not allowed:
        return JsonResponse(
            {
                'error': 'rate_limited',
                'detail': 'Too many API requests from this IP address.',
                'retry_after_seconds': retry_after,
            },
            status=429,
        )

    user = get_object_or_404(User.objects.select_related('profile'), username__iexact=username)
    return JsonResponse(_serialize_user_profile(request, user))


def error_404(request, exception):
    return render(request, '404.html', status=404)


def error_500(request):
    return render(request, '500.html', status=500)



def level_detail(request, level_id):
    level = get_object_or_404(Level, id=level_id)  # Fetch the level by its ID
    comments = level.comments.all()
    difficulty_system = request.user.profile.difficulty_system if request.user.is_authenticated else 'punter'
    user_level_rating = None
    user_completion = None
    comment_error = None
    comment_content = ""

    if request.user.is_authenticated:
        user_level_rating = LevelRating.objects.filter(level=level, user=request.user).first()
        user_completion = LevelCompletion.objects.filter(level=level, user=request.user).first()

    rating_form = LevelRatingForm(instance=user_level_rating)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "rate":
            if not request.user.is_authenticated:
                return redirect('levels:login')

            rating_form = LevelRatingForm(request.POST, instance=user_level_rating)
            if rating_form.is_valid():
                rating = rating_form.save(commit=False)
                rating.level = level
                rating.user = request.user
                rating.save()
                level.refresh_rating_averages()
                return redirect('levels:level_detail', level_id=level_id)
        else:
            if not request.user.is_authenticated:
                return redirect('levels:login')

            content = (request.POST.get("content") or "").strip()
            comment_content = content
            if content:
                matched_word = find_profanity(content)
                if matched_word:
                    comment_error = 'Comment contains blocked language. Please update it and try again.'
                else:
                    Comment.objects.create(level=level, user=request.user, content=content)
                    return redirect('levels:level_detail', level_id=level_id)
            else:
                comment_error = 'Comment cannot be empty.'

    return render(
        request,
        'levels/level_detail.html',
        {
            'level': level,
            'comments': comments,
            'difficulty_system': difficulty_system,
            'rating_form': rating_form,
            'user_level_rating': user_level_rating,
            'user_completion': user_completion,
            'ratings_count': level.ratings.count(),
            'comment_error': comment_error,
            'comment_content': comment_content,
        },
    )


def _round_half_up(value):
    return int(math.floor(float(value) + 0.5))


def _build_distribution(values, labels, rounding=None, min_key=None, max_key=None):
    counts = {}
    for raw_value in values:
        if raw_value is None:
            continue

        key = rounding(raw_value) if rounding else int(raw_value)
        if min_key is not None:
            key = max(min_key, key)
        if max_key is not None:
            key = min(max_key, key)

        counts[key] = counts.get(key, 0) + 1

    max_count = max(counts.values(), default=0)

    distribution = []
    for key, label in labels:
        count = counts.get(key, 0)
        percent = int((count / max_count) * 100) if max_count else 0
        distribution.append({
            'label': label,
            'count': count,
            'percent': percent,
        })

    return distribution


def level_reviews(request, level_id):
    level = get_object_or_404(Level, id=level_id)
    difficulty_system = request.user.profile.difficulty_system if request.user.is_authenticated else 'punter'

    reviews = list(
        level.ratings.select_related('user', 'user__profile').order_by('-updated_at', '-created_at')
    )

    difficulty_distribution = _build_distribution(
        values=[review.difficulty_rating for review in reviews],
        labels=[(value, str(value)) for value in range(0, 16)],
        rounding=_round_half_up,
        min_key=0,
        max_key=15,
    )

    quality_distribution = _build_distribution(
        values=[review.quality_rating for review in reviews],
        labels=[(value, str(value)) for value in range(0, 6)],
        rounding=int,
        min_key=0,
        max_key=5,
    )

    return render(
        request,
        'levels/level_reviews.html',
        {
            'level': level,
            'reviews': reviews,
            'difficulty_distribution': difficulty_distribution,
            'quality_distribution': quality_distribution,
            'difficulty_system': difficulty_system,
        },
    )


@login_required
def upload_level(request):
    if request.method == 'POST':
        form = LevelForm(request.POST)
        if form.is_valid():
            level = form.save(commit=False)
            level.creator = request.user
            level.save()

            first_difficulty_rating = round(float(level.difficulty), 2)
            first_difficulty_rating = max(0, min(first_difficulty_rating, 15))
            LevelRating.objects.create(
                level=level,
                user=request.user,
                difficulty_rating=first_difficulty_rating,
                quality_rating=None,
            )
            level.refresh_rating_averages()

            return redirect('levels:list')
    else:
        form = LevelForm()
    return render(request, 'levels/upload_level.html', {'form': form})

def level_list(request):
    from django.db.models import Case, When, Value, CharField
    from django.db.models.functions import Coalesce
    
    levels = Level.objects.all()

    search_query = request.GET.get('q', '').strip()
    if search_query:
        levels = levels.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(original_uploader__icontains=search_query)
            | Q(other_creators__icontains=search_query)
            | Q(mod_category__icontains=search_query)
            | Q(level_code__icontains=search_query)
            | Q(url__icontains=search_query)
            | Q(video_url__icontains=search_query)
            | Q(creator__username__icontains=search_query)
            | Q(creator__profile__display_name__icontains=search_query)
        ).distinct()

    # Sorting functionality
    sort_by = request.GET.get('sort', 'quality_rating')
    sort_direction = request.GET.get('direction', 'desc')

    if sort_by == 'creator':
        # Sort by original_uploader if it exists, otherwise by creator username
        levels = levels.annotate(
            display_creator=Case(
                When(original_uploader__isnull=False, original_uploader__gt='', then='original_uploader'),
                default='creator__username',
                output_field=CharField()
            )
        )
        if sort_direction == 'desc':
            levels = levels.order_by('-display_creator')
        else:
            levels = levels.order_by('display_creator')
    elif sort_by == 'difficulty':
        levels = levels.annotate(display_difficulty=Coalesce('difficulty_rating', 'difficulty'))
        if sort_direction == 'desc':
            levels = levels.order_by('-display_difficulty')
        else:
            levels = levels.order_by('display_difficulty')
    elif sort_by == 'quality_rating':
        # Keep unrated levels below rated ones when sorting by quality.
        levels = levels.annotate(
            has_quality=Case(
                When(quality_rating__isnull=True, then=Value(1)),
                default=Value(0),
            )
        )
        if sort_direction == 'desc':
            levels = levels.order_by('has_quality', '-quality_rating')
        else:
            levels = levels.order_by('has_quality', 'quality_rating')
    elif sort_by in ['name', 'mod_category', 'created_at']:
        if sort_direction == 'desc':
            levels = levels.order_by(f'-{sort_by}')  # Descending order
        else:
            levels = levels.order_by(sort_by)  # Ascending order

    # Pagination functionality
    paginator = Paginator(levels, 10)  # Show 10 levels per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    difficulty_system = request.user.profile.difficulty_system if request.user.is_authenticated else 'punter'

    return render(request, 'levels/level_list.html',
    {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'sort_direction': sort_direction,
        'search_query': search_query,
        'difficulty_system': difficulty_system,
    })


def home(request):
    return render(request, 'levels/home.html')

def signup(request):
    if request.method == 'POST':
        form = CaseInsensitiveUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CaseInsensitiveUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = CaseInsensitiveAuthenticationForm

def logout(request):
    django.contrib.auth.logout(request)
    return redirect('levels:home')


@login_required
def edit_level(request, level_id):
    level = get_object_or_404(Level, id=level_id, creator=request.user)  # Ensure the user owns the level

    if request.method == 'POST':
        form = LevelForm(request.POST, instance=level)
        if form.is_valid():
            form.save()
            return redirect('levels:level_detail', level_id=level.id)  # Redirect to a detail view of the level
    else:
        form = LevelForm(instance=level)

    return render(request, 'levels/edit_level.html', {'form': form, 'level': level})

@login_required
def delete_level(request, level_id):
    level = get_object_or_404(Level, id=level_id, creator=request.user)  # Ensure the user owns the level

    if request.method == 'POST':
        level.delete()
        return redirect('levels:home')  # Redirect to the home page or wherever you prefer

    return render(request, 'levels/delete_level.html', {'level': level})


def user_profile(request, username):
    from django.db.models.functions import Coalesce

    user = get_object_or_404(User, username__iexact=username)
    profile = user.profile  # Access the profile of the logged-in user
    uploaded_levels = Level.objects.filter(creator=user).filter(
        Q(original_uploader__isnull=True) | Q(original_uploader__exact='')
    ).order_by('-created_at')
    approved_submissions = LevelCompletion.objects.filter(
        user=user,
        status=LevelCompletion.STATUS_APPROVED,
    ).select_related('level', 'user', 'level__creator').annotate(
        completion_difficulty=Coalesce('level__difficulty_rating', 'level__difficulty')
    ).order_by('-completion_difficulty', 'level__name')

    total_completions = approved_submissions.count()

    return render(
        request,
        "levels/user_profile.html",
        {
            "user_profile": user,
            "profile": profile,
            "uploaded_levels": uploaded_levels,
            "approved_submissions": approved_submissions,
            "total_completions": total_completions,
        },
    )


@login_required
def edit_profile(request, username):
    if request.user.username.lower() != username.lower():
        return HttpResponseForbidden('You can only edit your own profile.')

    profile = request.user.profile

    if request.method == 'POST':
        form = ProfilePublicForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('levels:user_profile', username=request.user.username)
    else:
        form = ProfilePublicForm(instance=profile)

    return render(
        request,
        'levels/edit_profile.html',
        {
            'form': form,
            'user_profile': request.user,
        },
    )


@login_required
def submit_level_completion(request, level_id):
    level = get_object_or_404(Level, id=level_id)
    completion, _ = LevelCompletion.objects.get_or_create(
        level=level,
        user=request.user,
        defaults={
            'proof': '',
            'status': LevelCompletion.STATUS_PENDING,
            'reviewed_at': None,
            'reviewed_by': None,
        },
    )

    if request.method == 'POST':
        form = LevelCompletionForm(request.POST, instance=completion)
        if form.is_valid():
            completion = form.save(commit=False)
            completion.user = request.user
            completion.level = level

            if float(level.difficulty) < 5:
                completion.status = LevelCompletion.STATUS_APPROVED
                completion.reviewed_at = None
                completion.reviewed_by = None
                completion.save()
                completion.approve(reviewer=None)
            else:
                completion.status = LevelCompletion.STATUS_PENDING
                completion.reviewed_at = None
                completion.reviewed_by = None
                completion.save()

            return redirect('levels:level_detail', level_id=level.id)
    else:
        form = LevelCompletionForm(instance=completion)

    return render(
        request,
        'levels/submit_level_completion.html',
        {
            'level': level,
            'completion': completion,
            'form': form,
        },
    )


@login_required
def my_completion_submissions(request):
    submissions_qs = LevelCompletion.objects.filter(user=request.user).order_by('-submitted_at')
    paginator = Paginator(submissions_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'levels/my_completion_submissions.html',
        {
            'submissions': page_obj,
            'page_obj': page_obj,
        },
    )


@login_required
def admin_completion_triage(request):
    if not request.user.is_staff:
        return HttpResponseForbidden('Admin access required.')

    if request.method == 'POST':
        completion_id = request.POST.get('completion_id')
        decision = request.POST.get('decision')
        completion = get_object_or_404(LevelCompletion, id=completion_id)

        if decision == 'approve':
            completion.approve(reviewer=request.user)
        elif decision == 'reject':
            completion.reject(reviewer=request.user)

        return redirect('levels:admin_completion_triage')

    submissions_qs = LevelCompletion.objects.select_related('user', 'level', 'reviewed_by').order_by('-submitted_at')
    paginator = Paginator(submissions_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'levels/admin_completion_triage.html',
        {
            'submissions': page_obj,
            'page_obj': page_obj,
        },
    )

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    # Check if the logged-in user is the author of the comment
    if comment.user != request.user:
        return redirect('levels:level_detail', level_id=comment.level.id)  # Redirect if not the owner

    if request.method == 'POST':
        content = (request.POST.get('content') or '').strip()
        if content:
            matched_word = find_profanity(content)
            if matched_word:
                return render(
                    request,
                    'levels/edit_comment.html',
                    {
                        'comment': comment,
                        'comment_error': 'Comment contains blocked language. Please update it and try again.',
                        'comment_content': content,
                    },
                )

            comment.content = content
            comment.save()
            return redirect('levels:level_detail', level_id=comment.level.id)

        return render(
            request,
            'levels/edit_comment.html',
            {
                'comment': comment,
                'comment_error': 'Comment cannot be empty.',
                'comment_content': content,
            },
        )

    return render(request, 'levels/edit_comment.html', {'comment': comment})

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    # Check if the logged-in user is the author of the comment
    if comment.user == request.user:
        level_id = comment.level.id  # Save the level ID for redirection
        comment.delete()
        return redirect('levels:level_detail', level_id=level_id)

    return redirect('levels:level_detail', level_id=comment.level.id)

def info_page(request):
    return render(request, 'levels/info.html')


@login_required
def user_settings(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileSettingsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('levels:user_settings')
    else:
        form = ProfileSettingsForm(instance=profile)

    return render(
        request,
        'levels/user_settings.html',
        {
            'form': form,
            'difficulty_system': profile.difficulty_system,
        },
    )






