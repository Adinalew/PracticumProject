from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .forms import StudySessionForm
from .forms import MultiFileUploadForm
from django.http import HttpResponse
from .utils import generate_tts_audio, extract_text_from_pdf, extract_text_from_uploaded_file
from .models import StudySession, UploadedFile, ExtractedNote
from django.contrib import messages
import os
from .utils import extract_text_from_image, extract_text_from_file

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
        session_form = StudySessionForm(request.POST)
        file_form = MultiFileUploadForm(request.POST, request.FILES)

        if session_form.is_valid():
            files = request.FILES.getlist('files')
            if not files:
                file_form.add_error('files', 'Please upload at least one file.')
            else:
                session = session_form.save(commit=False)
                session.user = request.user
                session.save()

                for f in files:
                    UploadedFile.objects.create(
                        user=request.user,
                        session=session,
                        file=f
                    )

                    # Decide what kind of processing to do
                    if f.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                        extracted = extract_text_from_image(f)
                        ExtractedNote.objects.create(session=session, text=extracted)

                    elif f.name.lower().endswith('.txt'):
                        content = f.read().decode('utf-8')
                        ExtractedNote.objects.create(session=session, text=content)

                return redirect('session_actions', session_id=session.id)

        # If we got here, either session_form or file_form has errors
        print("Session Form Errors:", session_form.errors)
        print("File Form Errors:", file_form.errors)
    else:
        session_form = StudySessionForm()
        file_form = MultiFileUploadForm()

    return render(request, 'core/start_session.html', {
        'session_form': session_form,
        'file_form': file_form,
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

    notes = session.extracted_notes.all()

    return render(request, 'core/session_actions.html', {
        'session': session,
        'notes': notes,
    })

@login_required
def upload_files_to_session(request, session_id):
    print(f"Starting file upload for session ID: {session_id}")
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    print(f"Session retrieved: {session}")

    if request.method == 'POST':
        form = MultiFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            print("Form is valid. Processing uploaded files...")
            for f in request.FILES.getlist('files'):
                print(f"Processing file: {f.name}")

                # Create UploadedFile instance and save it
                uploaded_file = UploadedFile.objects.create(
                    user=request.user,
                    session=session,
                    file=f
                )

                # Extract text from saved uploaded file
                extracted_text = extract_text_from_uploaded_file(uploaded_file)
                print(f"OCR extracted text for file {f.name}:\n{extracted_text}")

                if extracted_text.strip():
                    ExtractedNote.objects.create(session=session, text=extracted_text)
                    print(f"Extracted note created for file: {f.name}")
                else:
                    print(f"No text extracted from file {f.name}, skipping note creation.")

            print("All files processed successfully.")
        else:
            print("Form is invalid. Errors:", form.errors)
        return redirect('session_detail', session_id=session.id)
    else:
        form = MultiFileUploadForm()
        print("Rendering upload form.")

    return render(request, 'core/upload.html', {'form': form, 'session': session})

@login_required
def session_detail(request, session_id):
    print(f"Fetching session with ID: {session_id}")
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    print(f"Session retrieved: {session}")

    print("Fetching extracted notes...")
    notes = session.extracted_notes.all()
    print(f"Notes retrieved: {notes}")

    print("Fetching flashcards...")
    flashcards = session.flashcards.all()
    print(f"Flashcards retrieved: {flashcards}")

    print("Fetching quizzes...")
    quizzes = session.quizzes.all()
    print(f"Quizzes retrieved: {quizzes}")

    print("Fetching summaries...")
    summaries = session.summaries.all()
    print(f"Summaries retrieved: {summaries}")

    print("Rendering session_detail template...")
    return render(request, 'core/session_detail.html', {
        'session': session,
        'notes': notes,
        'flashcards': flashcards,
        'quizzes': quizzes,
        'summaries': summaries,
    })

@login_required
def delete_session(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    session.delete()
    messages.success(request, "Session deleted successfully.")
    return redirect('dashboard')  # or wherever your list lives

@login_required
def generate_flashcards(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    # Placeholder logic
    return render(request, 'core/flashcards.html', {'session': session})

@login_required
def generate_quiz(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    # Placeholder logic
    return render(request, 'core/quiz.html', {'session': session})

@login_required
def text_to_speech(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    notes = session.extracted_notes.all()
    text = " ".join(note.text for note in notes if note.text)

    if not text.strip():
        return HttpResponse("No notes available to read aloud.")

    audio = generate_tts_audio(text)
    response = HttpResponse(audio, content_type='audio/mpeg')
    response['Content-Disposition'] = 'inline; filename="session_audio.mp3"'
    return response

@login_required
def review_notes(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    files = session.uploaded_files.all()
    return render(request, 'core/review.html', {'session': session, 'files': files})


