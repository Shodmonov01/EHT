from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
     CategorySetListAPIView, StartQuizAPIView, QuestionListAPIView, QuizResultCreateAPIView, \
        table_pdf, summary_pdf, get_admin_statistics_page
)

router = DefaultRouter()

urlpatterns = [
    path('api/category-set/', CategorySetListAPIView.as_view(), name='category_set_list'),
    path('api/quizzes/start', StartQuizAPIView.as_view(), name='quiz-create'),
    path('api/quiz/questions/<int:category_set_id>/', QuestionListAPIView.as_view(), name='questions-list'),
  
    path('api/quiz/submit', QuizResultCreateAPIView.as_view(), name='quiz-result'),
 
    path('files/quiz-results/result.pdf', 
          table_pdf,
         name='download_result_pdf'),
    path('files/quiz-results/diagnostic.pdf', 
         summary_pdf, 
         name='download_diagnostic_pdf'),
     path("admin/statistics/", get_admin_statistics_page, name='admin-statistics'),

    # path('quizzes/', QuizListView.as_view(), name='quiz-list'),
    # path('quizzes/<int:quiz_id>/questions/', QuizQuestionsView.as_view(), name='quiz-questions'),
    # path('api/quizzes/<int:quiz_id>/', QuizDetailAPIView.as_view(), name='api_quiz_detail'),
    # path('api/quizzes/<int:quiz_id>/submit/', SubmitQuizAPIView.as_view(), name='api_submit_quiz'),
    # path('api/quiz_result/<int:quiz_result_id>/', QuizResultAPIView.as_view(), name='api_quiz_result'),
    # path('api/summary/<int:quiz_result_id>/', SummaryAPIView.as_view(), name='api_summary'),
    # path('api/table/<int:quiz_result_id>/', TableAPIView.as_view(), name='api_table'),
]