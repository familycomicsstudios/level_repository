from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Level, Comment, LevelRating, LevelCompletion
from django.contrib.auth.models import User
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
from django.db.models import Q
from django.http import HttpResponseForbidden
from .profanity import find_profanity


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
    user = get_object_or_404(User, username__iexact=username)
    profile = user.profile  # Access the profile of the logged-in user
    uploaded_levels = Level.objects.filter(creator=user).filter(
        Q(original_uploader__isnull=True) | Q(original_uploader__exact='')
    ).order_by('-created_at')
    approved_submissions = LevelCompletion.objects.filter(
        user=user,
        status=LevelCompletion.STATUS_APPROVED,
    ).select_related('level', 'user').order_by('-reviewed_at', '-submitted_at')

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
    submissions = LevelCompletion.objects.filter(user=request.user).order_by('-submitted_at')
    return render(
        request,
        'levels/my_completion_submissions.html',
        {
            'submissions': submissions,
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

    submissions = LevelCompletion.objects.select_related('user', 'level', 'reviewed_by').order_by('-submitted_at')
    return render(
        request,
        'levels/admin_completion_triage.html',
        {
            'submissions': submissions,
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






