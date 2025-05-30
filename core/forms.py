from django import forms
from .models import StudySession

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