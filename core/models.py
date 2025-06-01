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

class FlashcardSet(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='flashcard_sets')
    title = models.CharField(max_length=200, default="Default")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.session.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class Flashcard(models.Model):
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE, related_name='cards', null=True, blank=True)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.question[:30]}..."


class Quiz(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name="quizzes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quizzes", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user[:50]}..."

class ExtractedNote(models.Model):
    session = models.ForeignKey(StudySession, related_name='extracted_notes', on_delete=models.CASCADE)
    file = models.ForeignKey('UploadedFile', null=True, blank=True, on_delete=models.SET_NULL, related_name='notes')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:50] or "<empty>"

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

class Question(models.Model):
    QUESTION_TYPES = [
        ('mc', 'Multiple Choice'),
        ('tf', 'True/False'),
        ('match', 'Matching'),
        ('long', 'Long Answer'),
        ('fib', 'Fill in the Blank'),
        ('short', 'Short Answer'),
    ]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    text = models.TextField()
    options = models.JSONField(blank=True, null=True)  # for MC, matching, FIB options etc.
    correct_answer = models.JSONField()  # answer(s) in JSON format (string/list/dict)
    explanation = models.TextField(blank=True)

class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.FloatField()
    taken_at = models.DateTimeField(auto_now_add=True)

class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.JSONField()  # user submitted answer (string/list/dict)
    is_correct = models.BooleanField()

class StudyReview(models.Model):
    session = models.ForeignKey(StudySession, related_name='reviews', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=100, blank=True)  # e.g., Crash Course, Extensive, etc.

    def __str__(self):
        return f"Review ({self.type}) for Session {self.session.id}"

class FollowUp(models.Model):
    review = models.ForeignKey(StudyReview, related_name='followups', on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q: {self.question[:30]}..."

class NoteAudio(models.Model):
    note = models.OneToOneField('ExtractedNote', on_delete=models.CASCADE, related_name='audio')
    audio_file = models.FileField(upload_to='note_audio/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Audio for note {self.note.id}"