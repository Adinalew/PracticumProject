from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import StudySession
from django.contrib.auth import logout
from .forms import StudySessionForm

def home_view(request):
    return render(request, 'home.html')  # Render your homepage HTML

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to login page after successful registration
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def dashboard_view(request):
    sessions = StudySession.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/dashboard.html', {'sessions': sessions})

def logout_view(request):
    logout(request)
    return redirect('home')  # after logout

@login_required
def start_session_view(request):
    if request.method == 'POST':
        form = StudySessionForm(request.POST, request.FILES)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            return redirect('session_actions', session_id=session.id)
    else:
        form = StudySessionForm()
    return render(request, 'core/start_session.html', {'form': form})

@login_required
def session_action_view(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'quiz':
            return redirect('generate_quiz', session_id=session.id)
        elif action == 'flashcards':
            return redirect('generate_flashcards', session_id=session.id)
        elif action == 'tts':
            return redirect('text_to_speech', session_id=session.id)
        elif action == 'review':
            return redirect('review_notes', session_id=session.id)

    return render(request, 'core/session_actions.html', {'session': session})
