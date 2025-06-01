import json
import openai
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .forms import StudySessionForm, MultiFileUploadForm, FollowUpForm, FlashcardCustomizationForm, QuizOptionsForm
from .models import (StudySession, UploadedFile, ExtractedNote, StudyReview, FollowUp, Flashcard, FlashcardSet,
                     Quiz, Question, QuizAttempt, UserAnswer)
from .utils import (extract_text_from_uploaded_file, extract_text_from_file, extract_text_from_image,
                    extract_text_from_pdf, generate_flashcards_from_text, generate_study_review,
                    generate_followup_response, generate_tts_audio, get_text_from_session, generate_note_audio)

QUESTION_TYPE_KEYS = {'mc', 'tf', 'match', 'long', 'fib', 'short'}

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

        # ✅ Manually fetch uploaded files
        files = request.FILES.getlist('files')

        print("FILES:", request.FILES)  # Debugging
        print("FILES.getlist('files'):", files)  # Debugging

        if session_form.is_valid():
            if not files:
                messages.error(request, "Please upload at least one file.")
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

                    # ✅ Extract text using utility function
                    extracted_text = extract_text_from_uploaded_file(uploaded_file)

                    print("🧠 OCR from view:", repr(extracted_text))  #

                    if extracted_text.strip():
                        ExtractedNote.objects.create(session=session, text=extracted_text, file=uploaded_file)

                return redirect('session_detail', session_id=session.id)

        else:
            print("Session Form Errors:", session_form.errors)

    else:
        session_form = StudySessionForm()

    return render(request, 'core/start_session.html', {
        'session_form': session_form,
    })
# Python
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

                    # Auto-detect logic: PDFs = assume handwritten
                    if f.name.lower().endswith('.pdf'):
                        extracted_text = extract_handwriting_from_pdf(f)
                    else:
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
    flashcard_sets = session.flashcard_sets.all().order_by('-created_at')
    quizzes = Quiz.objects.filter(session=session, user=request.user).order_by('-score')  # Highest score first
    summaries = session.summaries.all().order_by('-created_at')
    reviews = session.reviews.all().order_by('-created_at')

    return render(request, 'core/session_detail.html', {
        'session': session,
        'notes': notes,
        'uploaded_files': uploaded_files,
        'flashcard_sets': flashcard_sets,
        'quizzes': quizzes,
        'summaries': summaries,
        'reviews': reviews,
    })

@require_POST
@login_required
def edit_session_title(request, session_id):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)
    if request.method == 'POST':
        new_title = request.POST.get('title')
        if new_title:
            session.title = new_title
            session.save()

    # Check if there's a "next" parameter (for redirecting back to current page)
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('dashboard')

@login_required
def view_flashcard_set(request, set_id):
    flashcard_set = get_object_or_404(FlashcardSet, id=set_id, session__user=request.user)
    flashcards = flashcard_set.cards.all().order_by('id')  # or any preferred order

    return render(request, 'core/flashcard_set_detail.html', {
        'flashcard_set': flashcard_set,
        'flashcards': flashcards,
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

    # ✅ Clear unrelated messages from previous views (like "Session deleted")
    list(messages.get_messages(request))  # accessing clears them

    form = FlashcardCustomizationForm(request.POST or None)
    flashcard_sets = session.flashcard_sets.all().order_by('-created_at')
    flashcards = []

    if flashcard_sets.exists():
        latest_set = flashcard_sets.first()
        flashcards = latest_set.cards.all().order_by('created_at')
    else:
        messages.info(request, "No flashcards yet for this session. Try generating some below!")

    if request.method == 'POST' and 'generate_flashcards' in request.POST:
        if form.is_valid():
            custom_prompt = form.cleaned_data['custom_prompt']
            title = custom_prompt.strip() if custom_prompt.strip() else "Default"

            combined_text = ""
            for uploaded_file in session.uploaded_files.all():
                for note in uploaded_file.notes.all():
                    combined_text += note.text + "\n"

            try:
                card_pairs = generate_flashcards_from_text(combined_text, custom_prompt)

                if card_pairs:
                    flashcard_set = FlashcardSet.objects.create(session=session, title=title)
                    for q, a in card_pairs:
                        Flashcard.objects.create(flashcard_set=flashcard_set, question=q, answer=a)
                    messages.success(request, "Flashcards generated successfully!")
                    flashcards = flashcard_set.cards.all().order_by('created_at')
                else:
                    messages.error(request, "No flashcards were generated. Try a different prompt.")
            except Exception as e:
                print(f"Flashcard generation failed: {e}")
                messages.error(request, "An error occurred while generating flashcards.")
        else:
            messages.error(request, "Please fix the errors in the form.")

    return render(request, 'core/flashcards.html', {
        'session': session,
        'flashcard_sets': flashcard_sets,
        'form': form,
        'flashcards': flashcards,
    })

@login_required
def flashcard_set_detail(request, session_id, set_name):
    session = get_object_or_404(StudySession, id=session_id, user=request.user)

    flashcards = Flashcard.objects.filter(session=session, name=set_name).order_by('created_at')

    return render(request, 'core/flashcard_set_detail.html', {
        'session': session,
        'flashcard_set': {
            'name': set_name,
            'session': session
        },
        'flashcards': flashcards,
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
            print("Form is valid")
            qtypes = form.cleaned_data['qtypes']
            session_text = get_combined_session_text(session)

            if not session_text.strip():
                messages.error(request, "No study material found for this session.")
                return redirect('quiz_options', session_id=session.id)

            quiz = Quiz.objects.create(session=session, user=request.user)
            questions_data = generate_quiz_questions(session_text, qtypes)
            print("Returned from OpenAI:", questions_data)

            if not questions_data:
                messages.error(request, "Failed to generate questions. Try again later.")
                quiz.delete()
                return redirect('quiz_options', session_id=session.id)

            for q in questions_data:
                Question.objects.create(
                    quiz=quiz,
                    question_type=q['type'],
                    text=q['text'],
                    options=q.get('options', None),
                    correct_answer=q['correct_answer'],
                    explanation=q.get('explanation', '')
                )

            return redirect('take_quiz', quiz_id=quiz.id)

        else:
            print("Form errors:", form.errors)
    else:
        form = QuizOptionsForm()

    return render(request, 'core/quiz_options.html', {
        'form': form,
        'session': session
    })

def generate_quiz_questions(text, qtypes):
    prompt = f"""
    Based on the following study material, generate 5 questions of each of the following types: {', '.join(qtypes)}.
    
    Study material:
    {text}
    
    Provide output in this JSON format:
    [
      {{
        "type": "mc",
        "text": "What is X?",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "A",
        "explanation": "A is correct because..."
      }},
      ...
    ]
    
    For matching questions, return a list like:
    Match the term with its correct definition:

    Terms:
    - Term1
    - Term2
    - Term3

    Definitions:
    - Def1
    - Def2
    - Def3

    Only return valid JSON.
    """

    try:
        openai.api_key = settings.OPENAI_API_KEY

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        result = response.choices[0].message.content
        print("OpenAI raw response:", result)

        questions = json.loads(result)
        print("Parsed questions:", questions)

        valid_questions = []
        for q in questions:
            if q.get("type") in QUESTION_TYPE_KEYS and q.get("text") and q.get("correct_answer"):
                valid_questions.append(q)
            else:
                print("Invalid question skipped:", q)

        if not valid_questions:
            print("No valid questions generated.")
        print("Valid questions:", valid_questions)
        return valid_questions

    except json.JSONDecodeError as json_err:
        print("JSON decoding error:", json_err)
        print("Response content was:", result)
        return []

    except Exception as e:
        print("OpenAI API or other error:", e)
        return []

def get_combined_session_text(session):
    texts = []

    # Use ExtractedNote model which stores all extracted notes linked to the session
    extracted_notes = session.extracted_notes.all()

    if extracted_notes.exists():
        for note in extracted_notes:
            print("Notes were extracted")
            texts.append(note.text)
    else:
        print("No extracted notes found for this session.")

    combined = "\n".join(texts)
    return combined

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

        score = int((correct_count / total_questions) * 100) if total_questions else 0
        attempt.score = score
        attempt.save()

        return redirect('quiz_results', attempt_id=attempt.id)

    return render(request, 'core/take_quiz.html', {'quiz': quiz, 'questions': questions})

def submit_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, user=request.user)
    questions = quiz.question_set.all()

    score = 0
    for question in questions:
        user_answer = request.POST.get(f'question_{question.id}')
        if user_answer == question.correct_answer:
            score += 1

    total_questions = questions.count()

    if total_questions == 0:
        percentage = 0
    else:
        percentage = round((score / total_questions) * 100)

    # Save only if better or if no score
    if quiz.score is None or percentage > quiz.score:
        quiz.score = percentage
        quiz.save()

    percentage = int((score / total_questions) * 100) if total_questions > 0 else 0
    if quiz.score is None or percentage > quiz.score:
        quiz.score = percentage
        quiz.save()

    return render(request, 'core/quiz_results.html', {
        'quiz': quiz,
        'score': percentage,
        'questions': questions,
    })

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

@login_required
def note_audio_view(request, note_id):
    """
    Returns MP3 audio for a given ExtractedNote.
    If audio doesn't exist, generate it using AI voice.
    """
    note = get_object_or_404(ExtractedNote, id=note_id, session__user=request.user)

    # If audio already exists, serve it
    if hasattr(note, 'audio') and note.audio.audio_file:
        return redirect(note.audio.audio_file.url)

    # Otherwise, generate it
    audio_obj = generate_note_audio(note)
    if audio_obj:
        return redirect(audio_obj.audio_file.url)
    else:
        return HttpResponse("Error generating audio.", status=500)