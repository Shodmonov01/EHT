from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
     CategorySetListAPIView, StartQuizAPIView, QuizViewSet,  QuizResultViewSet
)

router = DefaultRouter()
router.register(r'questions', QuizViewSet)
router.register(r'quiz-results', QuizResultViewSet)

urlpatterns = [
    path('api/category-set/', CategorySetListAPIView.as_view(), name='category_set_list'),
    path('api/quizzes/start', StartQuizAPIView.as_view(), name='quiz-create'),
    path('api/quizzes/', include(router.urls))
    # path('api/quizzes/<int:quiz_id>/', QuizDetailAPIView.as_view(), name='api_quiz_detail'),
    # path('api/quizzes/<int:quiz_id>/submit/', SubmitQuizAPIView.as_view(), name='api_submit_quiz'),
    # path('api/quiz_result/<int:quiz_result_id>/', QuizResultAPIView.as_view(), name='api_quiz_result'),
    # path('api/summary/<int:quiz_result_id>/', SummaryAPIView.as_view(), name='api_summary'),
    # path('api/table/<int:quiz_result_id>/', TableAPIView.as_view(), name='api_table'),
]