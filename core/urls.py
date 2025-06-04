from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import home_view, generate_flashcards, text_to_speech, view_review, submit_followup, view_flashcard_set
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', home_view, name='home'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    path('start-session/', views.start_session_view, name='start_session'),
    path('session/<int:session_id>/upload/', views.upload_files_to_session, name='upload_files_to_session'),
    path('session/<int:session_id>/flashcards/', generate_flashcards, name='generate_flashcards'),
    path('session/<int:session_id>/tts/', views.text_to_speech, name='text_to_speech'),
    path('session/<int:session_id>/review/', views.session_review, name='session_review'),
    path('session/<int:session_id>/customize-review/', views.customize_review, name='customize_review'),
    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('sessions/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('session/<int:session_id>/debug-notes/', views.debug_extracted_notes, name='debug_extracted_notes'),
    path('session/<int:session_id>/quiz-options/', views.quiz_options_view, name='quiz_options'),
    path('quiz/<int:quiz_id>/take/', views.take_quiz_view, name='take_quiz'),
    path('quiz-attempt/<int:attempt_id>/results/', views.quiz_results_view, name='quiz_results'),
    path('reviews/<int:review_id>/', view_review, name='view_review'),
    path('reviews/<int:review_id>/followup/', submit_followup, name='submit_followup'),
    path('session/<int:session_id>/reviews/', views.session_reviews, name='session_reviews'),
    path('session/<int:session_id>/flashcards/<str:set_name>/', views.flashcard_set_detail, name='flashcard_set_detail'),
    path('flashcards/<int:set_id>/', view_flashcard_set, name='view_flashcard_set'),
    path('session/<int:session_id>/edit-title/', views.edit_session_title, name='edit_session_title'),
    path('note_audio/<int:note_id>/', views.note_audio_view, name='note_audio'),
    path('quiz/<int:quiz_id>/take/', views.take_quiz_view, name='take_quiz'),
    path('quiz/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    path('flashcard_set/<int:flashcard_set_id>/delete/', views.delete_flashcard_set, name='delete_flashcard_set'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)