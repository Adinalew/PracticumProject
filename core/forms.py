from django import forms
from .models import StudySession

# ✅ Define a custom widget that allows multiple files
class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultiFileUploadForm(forms.Form):
    files = forms.FileField(
        widget=MultiFileInput(attrs={'multiple': True}),
        required=True
    )

class StudySessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = ['title']  # No FileField here
