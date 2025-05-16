from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .forms import StudySessionForm
from .forms import MultiFileUploadForm
from .models import StudySession, UploadedFile

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
    #sessions = StudySession.objects.filter(user=request.user).prefetch_related('uploaded_files')
    return render(request, 'core/dashboard.html', {'sessions': sessions})

def logout_view(request):
    logout(request)
    return redirect('home')  # after logout

@login_required
def start_session_view(request):
    if request.method == 'POST':
        session_form = StudySessionForm(request.POST)
        file_form = MultiFileUploadForm(request.POST, request.FILES)

        if session_form.is_valid() and file_form.is_valid():
            # Create the study session
            session = session_form.save(commit=False)
            session.user = request.user
            session.save()

            # Save uploaded files
            for f in request.FILES.getlist('files'):
                UploadedFile.objects.create(
                    user=request.user,
                    session=session,
                    file=f
                )

            return redirect('session_actions', session_id=session.id)
    else:
        session_form = StudySessionForm()
        file_form = MultiFileUploadForm()

    return render(request, 'core/start_session.html', {
        'session_form': session_form,
        'file_form': file_form
    })

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

def upload_files(request):
    if request.method == 'POST':
        form = MultiFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('files')
            for f in files:
                # Save each file as a new UploadedFile instance or however your model works
                UploadedFile.objects.create(file=f, user=request.user)
            return redirect('some_success_page')
    else:
        form = MultiFileUploadForm()
    return render(request, 'upload.html', {'form': form})
