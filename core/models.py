from django.db import models
from django.contrib.auth.models import User

class StudySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='uploaded_files')
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class Flashcard(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='flashcards')
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.question[:30]}..."

class Quiz(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title[:50]}..."

class ExtractedNote(models.Model):
    session = models.ForeignKey(StudySession, related_name='extracted_notes', on_delete=models.CASCADE)
    text = models.TextField()
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:50]

class TextToSpeechAudio(models.Model):
    session = models.OneToOneField(StudySession, on_delete=models.CASCADE, related_name='tts_audio')
    audio_file = models.FileField(upload_to='tts_audio/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.audio_file[:50]

class Summary(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='summaries')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content[:50]