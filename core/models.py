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
    front = models.CharField(max_length=255)  # e.g. question
    back = models.TextField()                 # e.g. answer

    def __str__(self):
        return f"{self.front[:30]}..."

class QuizQuestion(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='quiz_questions')
    question = models.TextField()
    correct_answer = models.CharField(max_length=255)
    user_answer = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.question[:50]}..."

class ExtractedNote(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='extracted_notes')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:50]


