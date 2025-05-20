from django import forms
from .models import StudySession

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultiFileUploadForm(forms.Form):
    files = forms.FileField(
        widget=MultiFileInput(attrs={'multiple': True}),
        required=False  # Optional so session can still submit with no files
    )

class StudySessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = ['title']  # No FileField here


