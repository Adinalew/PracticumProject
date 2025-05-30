from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.http import HttpResponse
from django import forms
from .models import StudyReview, FollowUp
from django.forms import ModelForm, Textarea
from django.views.decorators.http import require_POST
from .forms import StudySessionForm, MultiFileUploadForm
from .models import StudySession, UploadedFile, ExtractedNote
from .models import FollowUp, Flashcard
from .forms import FollowUpForm
from .utils import generate_study_review
from .utils import generate_followup_response
from django.http import JsonResponse
from .utils import get_text_from_session, generate_flashcards_from_text

from .utils import (
    extract_text_from_uploaded_file,
    extract_text_from_file,
    extract_text_from_image,
    extract_text_from_pdf,
    generate_tts_audio,
    get_text_from_session,
    generate_study_review,
)

from .models import StudySession, Quiz, Question, QuizAttempt, UserAnswer
from .forms import QuizOptionsForm
import json

# ✨ New form for customizing the AI-generated review
class ReviewCustomizationForm(forms.Form):
    LANGUAGE_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    STYLE_CHOICES = [
        ('first_grade', 'Explain it like I’m in 1st grade'),
        ('normal', 'Standard academic tone'),
        ('college', 'University-level explanation'),
    ]
    DEPTH_CHOICES = [
        ('quick', 'Quick summary'),
        ('crash', 'Crash course'),
        ('extensive', 'Extensive detailed review'),
    ]

    language_level = forms.ChoiceField(choices=LANGUAGE_LEVEL_CHOICES, label="Language Level")
    explanation_style = forms.ChoiceField(choices=STYLE_CHOICES, label="Teaching Style")
    review_depth = forms.ChoiceField(choices=DEPTH_CHOICES, label="Depth of Review")
    selected_files = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, required=False)
    additional_notes = forms.CharField(widget=forms.Textarea, required=False)



def home_view(request):
    return render(request, 'home.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard_view(request):
    sessions = StudySession.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/dashboard.html', {'sessions': sessions})

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
                    uploaded_file = UploadedFile.objects.create(
                        user=request.user,
                        session=session,
                        file=f
                    )
                    extracted_text = extract_text_from_uploaded_file(uploaded_file)
                    if extracted_text.strip():
                        ExtractedNote.objects.create(session=session, text=extracted_text, file=uploaded_file)

                return redirect('session_detail', session_id=session.id)

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
def upload_files_to_session(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)

    if request.method == 'POST':
        form = MultiFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('files')
            if not files:
                messages.error(request, "No files selected for upload.")
            else:
                for f in files:
                    uploaded_file = UploadedFile.objects.create(
                        user=request.user,
                        session=session,
                        file=f
                    )
                    extracted_text = extract_text_from_uploaded_file(uploaded_file)
                    if extracted_text.strip():
                        ExtractedNote.objects.create(session=session, text=extracted_text, file=uploaded_file)

                messages.success(request, "Files uploaded successfully!")
        else:
            messages.error(request, "Error in file upload form.")

        return redirect('session_detail', session_id=session.id)
    else:
        form = MultiFileUploadForm()

    uploaded_files = session.uploaded_files.all()

    return render(request, 'core/upload.html', {
        'form': form,
        'session': session,
        'uploaded_files': uploaded_files
    })

# ✨ Update session_detail to show reviews
@login_required
def session_detail(request, session_id):
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
            return redirect('customize_review', session_id=session.id)

    notes = session.extracted_notes.all()
    uploaded_files = session.uploaded_files.all()
    flashcards = session.flashcards.all()
    quizzes = session.quizzes.all()
    summaries = session.summaries.all().order_by('-created_at')
    reviews = session.reviews.all().order_by('-created_at')  # ✅ add this line

    return render(request, 'core/session_detail.html', {
        'session': session,
        'notes': notes,
        'uploaded_files': uploaded_files,
        'flashcards': flashcards,
        'quizzes': quizzes,
        'summaries': summaries,
        'reviews': reviews,  # ✅ add this to the context
    })
@login_required
def delete_session(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    session.delete()
    messages.success(request, "Session deleted successfully.")
    return redirect('dashboard')

@login_required
def generate_flashcards(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)


    if request.method == 'POST' and request.POST.get('action') == 'regenerate':
        # Delete old flashcards and regenerate
        session.flashcards.all().delete()
        text = get_text_from_session(session)
        flashcard_data = generate_flashcards_from_text(text)
        for question, answer in flashcard_data:
            Flashcard.objects.create(session=session, question=question, answer=answer)

    # If flashcards don't exist yet, generate once
    elif session.flashcards.count() == 0:
        text = get_text_from_session(session)
        flashcard_data = generate_flashcards_from_text(text)
        for question, answer in flashcard_data:
            Flashcard.objects.create(session=session, question=question, answer=answer)

    flashcards = session.flashcards.all()

    return render(request, 'core/flashcards.html', {
        'session': session,
        'flashcards': flashcards
    })
@login_required
def text_to_speech(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    notes = session.extracted_notes.all()
    text = " ".join(note.text for note in notes if note.text)

    if not text.strip():
        return HttpResponse("No notes available to read aloud.")

    try:
        audio = generate_tts_audio(text)
        response = HttpResponse(audio, content_type='audio/mpeg')
        response['Content-Disposition'] = 'inline; filename="session_audio.mp3"'
        return response
    except Exception as e:
        print(f"Error generating TTS audio: {e}")
        return HttpResponse("An error occurred while generating the audio.", status=500)

# ✨ NEW: Customization form before review generation
@login_required
def customize_review(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    uploaded_files = session.uploaded_files.all()
    file_choices = [(str(f.id), f.file.name) for f in uploaded_files]

    if request.method == 'POST':
        form = ReviewCustomizationForm(request.POST)
        form.fields['selected_files'].choices = file_choices
        if form.is_valid():
            request.session['review_options'] = form.cleaned_data
            return redirect('session_review', session_id=session.id)
    else:
        form = ReviewCustomizationForm()
        form.fields['selected_files'].choices = file_choices

    return render(request, 'core/customize_review.html', {
        'form': form,
        'session': session,
    })

@login_required
def session_review(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    options = request.session.get('review_options')

    if not options:
        return redirect('customize_review', session_id=session.id)

    selected_file_ids = options.get('selected_files', [])
    selected_files = UploadedFile.objects.filter(id__in=selected_file_ids)
    combined_text = ""
    for file in selected_files:
        combined_text += extract_text_from_uploaded_file(file) + "\n\n"

    if not combined_text.strip():
        return HttpResponse("No notes available for review.")

    try:
        review_text = generate_study_review(combined_text, options)
    except Exception as e:
        print(f"Error generating study review: {e}")
        return HttpResponse("An error occurred while generating the review.", status=500)

    # Save review to DB
    review = StudyReview.objects.create(
        session=session,
        type=options.get('review_depth'),
        content=review_text
    )
    # Clear review options so they don't affect future sessions
    del request.session['review_options']

    # ✅ Redirect to the newly created review page
    return redirect('view_review', review_id=review.id)

# ✨ New view to submit follow-up Qs
@login_required
@require_POST
def submit_followup(request, review_id):
    review = get_object_or_404(StudyReview, id=review_id, session__user=request.user)
    form = FollowUpForm(request.POST)
    if form.is_valid():
        question = form.cleaned_data['question']
        options = request.session.get('review_options')
        try:
            answer = generate_followup_response(question, review.content, options)
        except Exception as e:
            answer = "There was an error generating an answer."

        followup = FollowUp.objects.create(review=review, question=question, answer=answer)

        # Return JSON instead of redirect
        return JsonResponse({
            "question": followup.question,
            "answer": followup.answer
        })

    return JsonResponse({"error": "Invalid form submission"}, status=400)

@login_required
def debug_extracted_notes(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    notes = ExtractedNote.objects.filter(session=session)

    if not notes.exists():
        print(f"No ExtractedNote objects found for session ID: {session_id}")
    else:
        for note in notes:
            print(f"- Note ID: {note.id}, Text Preview: {note.text[:100]}")

    return HttpResponse("Debugging complete. Check the server logs for details.")

@login_required
def quiz_options_view(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)

    if request.method == 'POST':
        form = QuizOptionsForm(request.POST)
        if form.is_valid():
            qtypes = form.cleaned_data['qtypes']

            # TODO: Call OpenAI API here with qtypes and session content to generate questions.
            # For now, create an empty Quiz for demonstration:
            quiz = Quiz.objects.create(session=session)

            # You should parse OpenAI response and save Question objects here.
            # Example placeholder:
            # Question.objects.create(quiz=quiz, question_type='mc', text='Example question?', options=['A', 'B', 'C'], correct_answer='A')

            return redirect('take_quiz', quiz_id=quiz.id)
    else:
        form = QuizOptionsForm()

    return render(request, 'core/quiz_options.html', {'form': form, 'session': session})

@login_required
def take_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, session__user=request.user)
    questions = Question.objects.filter(quiz=quiz)

    if request.method == 'POST':
        # Process submitted answers and grade
        attempt = QuizAttempt.objects.create(quiz=quiz, user=request.user, score=0)
        total_questions = questions.count()
        correct_count = 0

        for question in questions:
            user_answer = request.POST.get(f'question_{question.id}')
            # TODO: Adjust parsing for complex types (JSON, lists) as needed.

            # Simple correctness check (expand logic per question_type)
            is_correct = False
            if question.question_type in ['mc', 'tf', 'fib', 'short']:
                # For JSONField answers, parse string user_answer to comparable format if needed
                correct = question.correct_answer
                if isinstance(correct, list):
                    is_correct = user_answer in correct
                else:
                    is_correct = (str(user_answer).strip().lower() == str(correct).strip().lower())
            elif question.question_type == 'long':
                # Optional: manual grading or AI grading
                is_correct = False
            elif question.question_type == 'match':
                # Implement matching logic here
                is_correct = False

            UserAnswer.objects.create(
                attempt=attempt,
                question=question,
                answer=user_answer,
                is_correct=is_correct
            )

            if is_correct:
                correct_count += 1

        score = (correct_count / total_questions) * 100 if total_questions else 0
        attempt.score = score
        attempt.save()

        return redirect('quiz_results', attempt_id=attempt.id)

    return render(request, 'core/take_quiz.html', {'quiz': quiz, 'questions': questions})

@login_required
def quiz_results_view(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    user_answers = UserAnswer.objects.filter(attempt=attempt).select_related('question')

    return render(request, 'core/quiz_results.html', {
        'attempt': attempt,
        'user_answers': user_answers,
    })

@login_required
def view_review(request, review_id):
    review = get_object_or_404(StudyReview, id=review_id)
    session = review.session
    followups = review.followups.all().order_by('-created_at')

    if request.method == 'POST':
        form = FollowUpForm(request.POST)
        if form.is_valid():
            followup = form.save(commit=False)
            followup.review = review

            options = request.session.get('review_options')  # might be None if expired
            try:
                followup.answer = generate_followup_response(
                    followup.question,
                    review.content,
                    options
                )
            except Exception as e:
                print(f"❌ Error generating follow-up: {e}")
                followup.answer = "There was an error generating an answer."

            followup.save()
            return redirect('view_review', review_id=review.id)
    else:
        form = FollowUpForm()

    return render(request, 'core/view_review.html', {
        'review': review,
        'session': session,
        'form': form,
        'followups': followups,
    })

@login_required
def session_reviews(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    reviews = session.reviews.all().order_by('-created_at')

    return render(request, 'core/session_reviews.html', {
        'session': session,
        'reviews': reviews,
    })