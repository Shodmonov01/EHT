from collections import defaultdict
from django.shortcuts import get_object_or_404
from django.utils import translation
import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Quiz, Question, Answer, Category, QuizResult, SubCategory, CategorySet
from .serializers import QuizSerializer, QuestionSerializer, AnswerSerializer, QuizResultSerializer,\
                            CategorySetHomeSerializer, UserQuizStarteSerializer
import gspread
from drf_spectacular.utils import extend_schema, OpenApiParameter
from oauth2client.service_account import ServiceAccountCredentials
from rest_framework.permissions import AllowAny
import os
from django.conf import settings
from .utils import get_google_sheet
from datetime import datetime, timedelta


class QuizDetailAPIView(APIView):
    """
    GET /api/quizzes/<quiz_id>/
    Returns a quiz and groups its questions by category.
    """
    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        questions = Question.objects.filter(quiz=quiz).order_by('theme__category__name')
        # Group questions by category name
        categories_dict = defaultdict(list)
        for question in questions:
            serialized_q = QuestionSerializer(question).data
            category = question.theme.category.name
            categories_dict[category].append(serialized_q)
            
        data = {
            'quiz': QuizSerializer(quiz).data,
            'categories': list(categories_dict.keys()),
            'questions_by_category': categories_dict
        }
        return Response(data)

class CategorySetListAPIView(APIView):
    permission_classes = [AllowAny,]
    """
    GET /api/quiz_form/<lang>/
    Returns the language (in display form) and available grades.
    """
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="Accept-Language",
                type=str,
                location=OpenApiParameter.HEADER,
                description="Select response language (ru, kz)",
                required=False,
                enum=["ru", "kz",],
            )
        ],
         responses={200: CategorySetHomeSerializer(many=True)},
         description="Returns list of category set"
    )
    def get(self, request):
        lang = request.headers.get("Accept-Language", 'ru')
        if lang not in ['kz', 'ru']:
            lang = 'ru'
        
        translation.activate(lang)

        # language = 'Русский' if lang == 'ru' else 'Қазақша' if lang == 'kz' else lang
        category_sets = CategorySet.objects.all()
        serializer = CategorySetHomeSerializer(category_sets, many=True)

        return Response(serializer.data)
    
class StartQuizAPIView(APIView):
    
    @extend_schema(
        request=UserQuizStarteSerializer,  # Specifies the request body schema
        responses={201: UserQuizStarteSerializer, 400: None},  # Expected responses
        description="Create a new quiz",
        parameters=[
            OpenApiParameter(
                name="Accept-Language",
                type=str,
                location=OpenApiParameter.HEADER,
                description="Select response language (ru, kz)",
                required=False,
                enum=["ru", "kz",],
            )
        ]
    )
    def post(self, request):
        lang = request.headers.get("Accept-Language", 'ru')
        if lang not in ['kz', 'ru']:
            lang = 'ru'

        serializer = UserQuizStarteSerializer(data=request.data)
        if serializer.is_valid():
            print(serializer.data, 'data ')
            print(serializer.validated_data, 'valid data')
            google_sheet = get_google_sheet()
            unique_id = str(uuid.uuid4())
            final_data_to_save = serializer.data
            print(final_data_to_save, 'final')
            
            current_time = (datetime.utcnow() + timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S')
            data_to_save = [
                current_time,
                final_data_to_save["parents_fullname"],
                final_data_to_save["name"],
                final_data_to_save["phone_number"],
                final_data_to_save['formatted_categories'],
                lang,
                '',
                '',
                '',
                unique_id, 
            ]
            print(data_to_save, 'data')
            google_sheet.append_row(data_to_save)

            return Response({"token": f"{unique_id}"}, status=201)
        else:
            return Response(serializer.errors, status=400)



class SubmitQuizAPIView(APIView):
    """
    POST /api/quizzes/<quiz_id>/submit/
    
    Expected POST data:
      - For each question, a key like "question<id>" with the selected answer id.
      - Additional fields: parent, name, phone, grade, language, location.
    
    Returns the created QuizResult and score information.
    """
    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        questions = Question.objects.filter(quiz=quiz)
        total_questions = questions.count()
        correct_answers_by_category = defaultdict(int)
        selected_answers = {}
        unanswered_questions_ids = []
        
        for question in questions:
            answer_id = request.data.get(f'question{question.id}')
            if answer_id:
                try:
                    answer = Answer.objects.get(id=answer_id)
                    selected_answers[question.id] = answer
                    if answer.is_correct:
                        correct_answers_by_category[question.theme.name] += 1
                except Answer.DoesNotExist:
                    unanswered_questions_ids.append(question.id)
            else:
                unanswered_questions_ids.append(question.id)
                
        score = sum(correct_answers_by_category.values())
        percentage_score = (score / total_questions * 100) if total_questions > 0 else 0

        # Get additional data from request
        parent_name = request.data.get('parent', 'Unknown Parent')
        name = request.data.get('name', 'Anonym')
        phone_number = request.data.get('phone', 'Unknown Phone')
        grade = request.data.get('grade', 'Unknown Grade')
        language = request.data.get('language', 'ru')
        location = request.data.get('location', 'Unknown')
        
        # Create the QuizResult instance
        quiz_result = QuizResult.objects.create(
            quiz=quiz,
            phone_number=phone_number,
            name=name,
            parent_name=parent_name,
            grade=grade,
        )
        # Set many-to-many relationships
        quiz_result.answers.set(selected_answers.values())
        quiz_result.unanswered_questions.set(questions.filter(id__in=unanswered_questions_ids))
        
        response_data = {
            'quiz_result_id': quiz_result.id,
            'percentage_score': percentage_score,
            'total_questions': total_questions,
            'score': score,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

class QuizResultAPIView(APIView):
    """
    GET /api/quiz_result/<quiz_result_id>/
    Returns the details of a quiz result.
    """
    def get(self, request, quiz_result_id):
        quiz_result = get_object_or_404(QuizResult, id=quiz_result_id)
        serializer = QuizResultSerializer(quiz_result)
        return Response(serializer.data)

class SummaryAPIView(APIView):
    """
    GET /api/summary/<quiz_result_id>/
    
    Returns a summary context for the quiz result.
    You can extend this view with additional logic (e.g. including recommendations, characterizations).
    """
    def get(self, request, quiz_result_id):
        quiz_result = get_object_or_404(QuizResult, id=quiz_result_id)
        total_questions = quiz_result.quiz.questions.count()
        correct_questions = quiz_result.answers.filter(is_correct=True).count()
        percentage_score = (correct_questions / total_questions * 100) if total_questions > 0 else 0
        
        data = {
            'quiz_result_id': quiz_result.id,
            'quiz_title': quiz_result.quiz.title,
            'quiz_grade': quiz_result.quiz.grade,
            'total_questions': total_questions,
            'correct_questions': correct_questions,
            'percentage_score': round(percentage_score, 1),
            # Additional fields (e.g., recommendations) can be added here.
        }
        return Response(data)

class TableAPIView(APIView):
    """
    GET /api/table/<quiz_result_id>/
    
    Returns detailed statistics (grouped by category and subcategory) for the quiz result.
    """
    def get(self, request, quiz_result_id):
        quiz_result = get_object_or_404(QuizResult, id=quiz_result_id)
        categories = Category.objects.all().order_by('name')
        category_stats = []
        
        for category in categories:
            subcategories = SubCategory.objects.filter(category=category).order_by('name')
            subcategory_stats = []
            for subcategory in subcategories:
                sub_answers = quiz_result.answers.filter(question__theme__name=subcategory.name)
                total = sub_answers.count()
                if total == 0:
                    continue
                correct = sub_answers.filter(is_correct=True).count()
                subcategory_stats.append({
                    'subcategory': subcategory.name,
                    'total_questions': total,
                    'correct_questions': correct,
                    'incorrect_questions': total - correct
                })
            if subcategory_stats:
                category_stats.append({
                    'category': category.name,
                    'subcategories': subcategory_stats
                })
        data = {
            'quiz_result_id': quiz_result.id,
            'category_stats': category_stats
        }
        return Response(data)
