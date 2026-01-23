from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Level, Comment
from django.contrib.auth.models import User
from .forms import LevelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
import django.contrib.auth
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator



def level_detail(request, level_id):
    level = get_object_or_404(Level, id=level_id)  # Fetch the level by its ID
    comments = level.comments.all()

    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            Comment.objects.create(level=level, user=request.user, content=content)
            return redirect('levels:level_detail', level_id=level_id)

    return render(request, 'levels/level_detail.html', {'level': level, 'comments': comments})


@login_required
def upload_level(request):
    if request.method == 'POST':
        form = LevelForm(request.POST)
        if form.is_valid():
            level = form.save(commit=False)
            level.creator = request.user
            level.save()
            return redirect('levels:list')
    else:
        form = LevelForm()
    return render(request, 'levels/upload_level.html', {'form': form})

def level_list(request):
    from django.db.models import Case, When, Value, CharField
    from django.db.models.functions import Coalesce
    
    levels = Level.objects.all()

    # Sorting functionality
    sort_by = request.GET.get('sort', 'name')  # Default sorting by name
    sort_direction = request.GET.get('direction', 'asc')  # Default sorting direction

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
    elif sort_by in ['name', 'difficulty', 'rated_difficulty', 'mod_category']:
        if sort_direction == 'desc':
            levels = levels.order_by(f'-{sort_by}')  # Descending order
        else:
            levels = levels.order_by(sort_by)  # Ascending order

    # Pagination functionality
    paginator = Paginator(levels, 10)  # Show 10 levels per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'levels/level_list.html',
    {
        'page_obj': page_obj,
        'sort_by': sort_by,
        'sort_direction': sort_direction,
    })


def home(request):
    return render(request, 'levels/home.html')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

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
    user = get_object_or_404(User, username=username)
    profile = user.profile  # Access the profile of the logged-in user
    return render(request, "levels/user_profile.html", {"user_profile": user, "profile": profile})

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    # Check if the logged-in user is the author of the comment
    if comment.user != request.user:
        return redirect('levels:level_detail', level_id=comment.level.id)  # Redirect if not the owner

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment.content = content
            comment.save()
            return redirect('levels:level_detail', level_id=comment.level.id)

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






