from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import home_view, generate_flashcards, generate_quiz, text_to_speech
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home_view, name='home'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    path('start-session/', views.start_session_view, name='start_session'),
    path('session-actions/<int:session_id>/', views.session_action_view, name='session_actions'),
    path('session/<int:session_id>/upload/', views.upload_files_to_session, name='upload_files_to_session'),
    path('session/<int:session_id>/flashcards/', generate_flashcards, name='generate_flashcards'),
    path('session/<int:session_id>/quiz/', generate_quiz, name='generate_quiz'),
    path('session/<int:session_id>/tts/', views.text_to_speech, name='text_to_speech'),
    path('session/<int:session_id>/review/', views.session_review, name='session_review'),

    path('sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('sessions/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('session/<int:session_id>/debug-notes/', views.debug_extracted_notes, name='debug_extracted_notes'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)