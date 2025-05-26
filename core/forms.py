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