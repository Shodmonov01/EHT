from collections import defaultdict
from django.shortcuts import get_object_or_404
from django.utils import translation
import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import  Question, Answer, Category, QuizResult, SubCategory, CategorySet, Quiz
from .serializers import  QuestionSerializer, AnswerSerializer,\
                            CategorySetHomeSerializer, UserQuizStarteSerializer
import gspread
from drf_spectacular.utils import extend_schema, OpenApiParameter
from oauth2client.service_account import ServiceAccountCredentials
from rest_framework.permissions import AllowAny
import os
from django.conf import settings
from .utils import get_google_sheet
from datetime import datetime, timedelta



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
            category_set = serializer.validated_data['category_set_id']
            category_set_id = category_set.id
            quiz = Quiz.objects.create(user_token = unique_id, phone_number = final_data_to_save["phone_number"], category_set = category_set )


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
            # google_sheet.append_row(data_to_save)

            return Response({"token": f"{unique_id}", "category_set_id":f"{category_set_id}"}, status=201)
        else:
            return Response(serializer.errors, status=400)


class QuestionListAPIView(APIView):
    def get(self, request, category_set_id):
            category_set = get_object_or_404(CategorySet, id=category_set_id)
            categories = Category.objects.filter(categoryset=category_set)

            questions = (
                    Question.objects.filter(category__in=categories)
                    .select_related("category", "theme", "theme__category") 
                )
            category_questions = {}

            for question in questions:
                category_id = question.category.id
                if category_id not in category_questions:
                    category_questions[category_id] = {
                        "category_id": category_id,
                        "category_name": question.category.name,
                       
                        "questions": []
                    }
                
                question_data = {
                    "id": question.id,
                    "text": question.text,
                    "category": question.theme.category.name,
                    "subcategory": question.theme.name,
                    "image": request.build_absolute_uri(question.image.url) if question.image and question.image.url else None,
                }
                
                category_questions[category_id]["questions"].append(question_data)

            return Response(list(category_questions.values()), status=200)


# class SubmitQuizAPIView(APIView):
#     """
#     POST /api/quizzes/<quiz_id>/submit/
    
#     Expected POST data:
#       - For each question, a key like "question<id>" with the selected answer id.
#       - Additional fields: parent, name, phone, grade, language, location.
    
#     Returns the created QuizResult and score information.
#     """
#     def post(self, request, quiz_id):
#         quiz = get_object_or_404(Quiz, id=quiz_id)
#         questions = Question.objects.filter(quiz=quiz)
#         total_questions = questions.count()
#         correct_answers_by_category = defaultdict(int)
#         selected_answers = {}
#         unanswered_questions_ids = []
        
#         for question in questions:
#             answer_id = request.data.get(f'question{question.id}')
#             if answer_id:
#                 try:
#                     answer = Answer.objects.get(id=answer_id)
#                     selected_answers[question.id] = answer
#                     if answer.is_correct:
#                         correct_answers_by_category[question.theme.name] += 1
#                 except Answer.DoesNotExist:
#                     unanswered_questions_ids.append(question.id)
#             else:
#                 unanswered_questions_ids.append(question.id)
                
#         score = sum(correct_answers_by_category.values())
#         percentage_score = (score / total_questions * 100) if total_questions > 0 else 0

#         # Get additional data from request
#         parent_name = request.data.get('parent', 'Unknown Parent')
#         name = request.data.get('name', 'Anonym')
#         phone_number = request.data.get('phone', 'Unknown Phone')
#         grade = request.data.get('grade', 'Unknown Grade')
#         language = request.data.get('language', 'ru')
#         location = request.data.get('location', 'Unknown')
        
#         # Create the QuizResult instance
#         quiz_result = QuizResult.objects.create(
#             quiz=quiz,
#             phone_number=phone_number,
#             name=name,
#             parent_name=parent_name,
#             grade=grade,
#         )
#         # Set many-to-many relationships
#         quiz_result.answers.set(selected_answers.values())
#         quiz_result.unanswered_questions.set(questions.filter(id__in=unanswered_questions_ids))
        
#         response_data = {
#             'quiz_result_id': quiz_result.id,
#             'percentage_score': percentage_score,
#             'total_questions': total_questions,
#             'score': score,
#         }
#         return Response(response_data, status=status.HTTP_201_CREATED)

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


from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
import gspread
from google.oauth2.service_account import Credentials
from django.shortcuts import get_object_or_404
from datetime import datetime

from .models import Category, CategorySet, SubCategory,  Question, Answer, QuizResult
from .serializers import (
    CategorySerializer, CategorySetSerializer, SubCategorySerializer,
     QuestionSerializer, AnswerSerializer,
    QuizResultCreateSerializer, QuizResultDetailSerializer
)

# class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer

# class CategorySetViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = CategorySet.objects.all()
#     serializer_class = CategorySetSerializer
    
#     @action(detail=True, methods=['get'])
#     def quiz(self, request, pk=None):
#         """Get the quiz associated with this category set"""
#         category_set = self.get_object()
#         try:
#             quiz = Quiz.objects.get(category_set=category_set)
#             return Response(QuizSerializer(quiz).data)
#         except Quiz.DoesNotExist:
#             return Response(
#                 {"error": "No quiz found for this category set"}, 
#                 status=status.HTTP_404_NOT_FOUND
#             )
    
#     @action(detail=True, methods=['get'])
#     def questions(self, request, pk=None):
#         """Get questions for the quiz associated with this category set"""
#         category_set = self.get_object()
#         try:
#             quiz = Quiz.objects.get(category_set=category_set)
#             questions = Question.objects.filter(quiz=quiz).select_related('theme', 'theme__category')
#             return Response(QuestionSerializer(questions, many=True).data)
#         except Quiz.DoesNotExist:
#             return Response(
#                 {"error": "No quiz found for this category set"}, 
#                 status=status.HTTP_404_NOT_FOUND
#             )

# class QuizListView(APIView):
#     def get(self, request):
#         """Get list of all quizzes"""
#         quizzes = Quiz.objects.all()
#         serializer = QuizSerializer(quizzes, many=True)
#         return Response(serializer.data)




class QuizResultViewSet(viewsets.ModelViewSet):
    queryset = QuizResult.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return QuizResultCreateSerializer
        return QuizResultDetailSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz_result = serializer.save()
        
        # Calculate score for the response
        total_questions = Question.objects.filter(quiz=quiz_result.quiz).count()
        correct_answers = quiz_result.answers.filter(is_correct=True).count()
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Generate result URL
        result_url = f"/api/quiz-results/{quiz_result.id}/"
        
        # Save to Google Sheet
        try:
            success = save_to_google_sheet(
                quiz_result.id, 
                quiz_result.name, 
                quiz_result.parent_name, 
                quiz_result.grade, 
                quiz_result.phone_number, 
                score,
                result_url
            )
        except Exception as e:
            success = False
            print(f"Error saving to Google Sheet: {e}")
        
        # Return response with details
        return Response(
            {
                'result': QuizResultDetailSerializer(quiz_result).data,
                'score': score,
                'total_questions': total_questions,
                'correct_answers': correct_answers,
                'result_url': result_url,
                'google_sheet_saved': success
            },
            status=status.HTTP_201_CREATED
        )
    

def save_to_google_sheet(result_id, name, parent_name, grade, phone_number, score, result_url):
    # Set up credentials
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_file(
        'path/to/your-service-account-key.json',
        scopes=scopes
    )
    
    # Connect to Google Sheets
    client = gspread.authorize(credentials)
    
    # Open the Google Sheet by its title
    sheet = client.open('Quiz Results').sheet1
    
    # Append the data to the sheet
    sheet.append_row([
        result_id,
        name,
        parent_name,
        grade,
        phone_number,
        f"{score:.2f}%",
        result_url,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ])
    
    return True

