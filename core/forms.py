from django import forms
from .models import StudySession, StudyReview, FollowUp

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultiFileUploadForm(forms.Form):
    files = forms.FileField(
        widget=MultiFileInput(attrs={'multiple': True}),
        required=False
    )

class StudySessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = ['title']

QUESTION_TYPE_CHOICES = [
    ('mc', 'Multiple Choice'),
    ('tf', 'True/False'),
    ('match', 'Matching'),
    ('long', 'Long Answer'),
    ('fib', 'Fill in the Blank'),
    ('short', 'Short Answer'),
]

class QuizOptionsForm(forms.Form):
    qtypes = forms.MultipleChoiceField(
        choices=QUESTION_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Select question types to include"
    )

# NEW FORM FOR REVIEW GENERATION
REVIEW_TYPE_CHOICES = [
    ('Crash Course', 'Crash Course'),
    ('Extensive', 'Extensive Review'),
    ('Beginner-Friendly', 'Beginner-Friendly'),
    ('Q&A Style', 'Q&A Style'),
    ('Summary Only', 'Summary Only'),
]

class StudyReviewForm(forms.ModelForm):
    type = forms.ChoiceField(choices=REVIEW_TYPE_CHOICES, required=False, label="Review Type")

    class Meta:
        model = StudyReview
        fields = ['type', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'AI will generate content...'})
        }

# NEW FORM FOR FOLLOW-UP QUESTIONS
class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = ['question']
        widgets = {
            'question': forms.Textarea(attrs={'placeholder': 'Ask a follow-up question...'})
        }

class FlashcardCustomizationForm(forms.Form):
    custom_prompt = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Example: Test me on coding syntax and method usage...',
            'rows': 3,
            'class': 'form-control',
        }),
        label="Customize Flashcard Prompt",
        help_text="Optional: Describe how you want your flashcards to be generated.",
    )