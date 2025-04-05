from collections import defaultdict
from django.shortcuts import get_object_or_404
from django.utils import translation
from django.http import HttpResponse, FileResponse
from django.shortcuts import render
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import  Question, Answer, Category, QuizResult, SubCategory, CategorySet, Quiz
from .serializers import  QuestionSerializer, AnswerSerializer,\
                            CategorySetHomeSerializer, UserQuizStarteSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from oauth2client.service_account import ServiceAccountCredentials
from rest_framework.permissions import AllowAny
import os
from .utils import get_google_sheet, save_to_google_sheet

from datetime import datetime, timedelta
from django.db.models import Prefetch

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
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

from django.db.models import Count, Q
from .data import *

from django.db import transaction
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import QuizResult, Quiz, Answer, Question
from .serializers import QuizResultCreateSerializer, QuizResultDetailSerializer
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from typing import Dict, List
from .utils import generate_and_save_pdfs

from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
print(BASE_URL, 'base url')

_executor = ThreadPoolExecutor(max_workers=4)

def async_task(fn, *args, **kwargs):
    _executor.submit(fn, *args, **kwargs)




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
            
            unique_id = str(uuid.uuid4())
            final_data_to_save = serializer.data
            print(final_data_to_save, 'final')
            category_set_id = serializer.data['category_set_id_value']
           
            quiz = Quiz.objects.create(user_token = unique_id, phone_number = final_data_to_save["phone_number"], parent_name = final_data_to_save["parents_fullname"],
                name = final_data_to_save["name"], category_set_id = category_set_id )


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
            

            def start_get_google_sheet():
                try:
                    google_sheet = get_google_sheet()
                    google_sheet.append_row(data_to_save)
                    print("Google Sheet updated successfully")
                except Exception as e:
                    print(f"Error updating Google Sheet: {e}")
            
            # Start the Google Sheet update in a separate thread
            sheet_thread = threading.Thread(target=start_get_google_sheet)
            sheet_thread.daemon = True  # Thread won't block server shutdown
            sheet_thread.start()

            return Response({"token": f"{unique_id}", "category_set_id":f"{category_set_id}"}, status=201)
        else:
            return Response(serializer.errors, status=400)


class QuestionListAPIView(APIView):
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
         
    )
    def get(self, request, category_set_id):
        lang = request.headers.get("Accept-Language", 'ru')
        if lang not in ['kz', 'ru']:
            lang = 'ru'
        
        translation.activate(lang)
        category_set = get_object_or_404(CategorySet, id=category_set_id)
        
        questions = (
            Question.objects.filter(
                theme__category__in=category_set.categories.all()
            )
            .select_related("theme", "theme__category")
            .prefetch_related(
                Prefetch(
                    'answer_set',
                    queryset=Answer.objects.all().only("id", "text", "image")
                )
            )
            .order_by('theme__category__id', 'theme__id')
        )

        category_questions = {}

        for question in questions:
            category = question.theme.category
            if category.id not in category_questions:
                category_questions[category.id] = {
                    "category_id": category.id,
                    "category_name": category.name,
                    "questions": []
                }
            
            question_data = {
                "id": question.id,
                "text": question.text,
                "subcategory": question.theme.name,
                "image": request.build_absolute_uri(question.image.url) if question.image else None,
                "answers": [
                    {"id": a.id, "text": a.text, "image": request.build_absolute_uri(a.image.url) if a.image else None}
                    for a in question.answer_set.all()
                ]
            }
            
            category_questions[category.id]["questions"].append(question_data)

        return Response(list(category_questions.values()), status=200)
    

class QuizResultCreateAPIView(APIView):
    @extend_schema(
        request=QuizResultCreateSerializer,
        description="Create a new quiz result with user answers",
        parameters=[
            OpenApiParameter(
                name="Accept-Language",
                type=str,
                location=OpenApiParameter.HEADER,
                description="Language preference (ru, kz)",
                required=False,
                enum=["ru", "kz"],
            )
        ],
        responses={
            201: QuizResultDetailSerializer,
            400: {"description": "Invalid input data"},
            404: {"description": "Quiz not found"},
        }
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # Step 1: Validate and save basic result data
        serializer = QuizResultCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Step 2: Get the related quiz
        try:
            quiz = Quiz.objects.get(
                user_token=serializer.validated_data['user_token']
            )
        except Quiz.DoesNotExist:
            return Response(
                {"error": "No quiz found for this user token"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Step 3: Validate all answers belong to this quiz's questions
        answer_ids = serializer.validated_data.get('answer_ids', [])
        unanswered_question_ids = serializer.validated_data.get('unanswered_question_ids', [])
        
        # Get all question IDs for this quiz
        quiz_question_ids = set(
            Question.objects.filter(
                theme__category__category_sets=quiz.category_set
            ).values_list('id', flat=True)
        )
        print(quiz_question_ids, 'question ids')
        
        # Validate answered questions
        answer_question_ids = set(
            Answer.objects.filter(id__in=answer_ids)
            .values_list('question_id', flat=True)
        )
        if not answer_question_ids.issubset(quiz_question_ids):
            return Response(
                {"error": "Some answers don't belong to this quiz's questions"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate unanswered questions
        if not set(unanswered_question_ids).issubset(quiz_question_ids):
            return Response(
                {"error": "Some unanswered questions don't belong to this quiz"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Step 4: Create the quiz result
        quiz_result = serializer.save(quiz=quiz)
        
        # Step 5: Calculate score with optimized queries
        quiz_result = QuizResult.objects.filter(pk=quiz_result.pk).annotate(
            total_questions=Count(
                'quiz__category_set__categories__questions',
                distinct=True
            ),
            correct_answers=Count(
                'answers',
                filter=Q(answers__is_correct=True),
                distinct=True
            )
        ).first()

        # try:
        #     # You could use Celery for this in production to make it truly async
        #     pdf_path = generate_and_save_pdf(quiz_result, request)
        # except Exception as e:
        #     print(f"Error generating PDF: {e}")

        # try:
        #     pdf_path = generate_and_save_pdfs(quiz_result, request)
        # except Exception as e:
        #      print(f"Error generating PDF: {e}")
        #     # Handle error if needed

        # if not pdf_path:
        #     # PDF generation failed, but we still return the result
        #     # You might want to log this error
        #     pass
        
        

        
        total_questions = quiz_result.total_questions or 0
        correct_answers = quiz_result.correct_answers or 0
        score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Format the score display
        score_display = f"{correct_answers} из {total_questions}"
        percentage_display = f"{score_percentage:.1f}%"
        
        # Generate admin statistics URL with category set name
        category_set_name = quiz.category_set.name if quiz.category_set else ""
        admin_statistics_url = (
            f"{BASE_URL}/admin/statistics/?quiz_result_id={quiz_result.id}"
            f"&percentage={score_percentage:.1f}"
            f"&score={score_display}"
            f"&quiz_name={category_set_name}"
        )
        print(admin_statistics_url, 'admin url')
        # Update Google Sheet with quiz result data
        try:
            user_token = quiz.user_token  # Get the user_token from the quiz object
            async_task(
                save_to_google_sheet,
                user_token=user_token,
                score=round(score_percentage, 2),
                result_url=request.build_absolute_uri(admin_statistics_url)
            )
        except Exception as e:
            # Log the error but continue with the response
            print(f"Error updating Google Sheet: {e}")
        
        # Step 6: Prepare response data
        response_data = {
            'result': QuizResultDetailSerializer(
                quiz_result,
                context={'request': request}
            ).data,
            'score': round(score_percentage, 2),
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'admin_statistics_url': admin_statistics_url,
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


def summary_pdf(request):
    quiz_result_id = request.GET.get('quiz_result')
    quiz_result = get_object_or_404(QuizResult, pk=quiz_result_id)
    
    # Get base context
    context = get_quiz_result_context(quiz_result)
    
    # Get all categories in the quiz's category set
    categories = Category.objects.filter(
        category_sets=quiz_result.quiz.category_set
    ).prefetch_related(
        Prefetch('subcategory_set', queryset=SubCategory.objects.all())
    ).order_by('name')
    
    # Initialize statsint()
    exact_stats = {'categories': [], 'total_questions': 0, 'total_correct': 0}
    natural_stats = {'categories': [], 'total_questions': 0, 'total_correct': 0}
    
    for category in categories:
        category_questions = 0
        category_correct = 0
        
        for subcategory in category.subcategory_set.all():
            # Get ALL questions in this subcategory
            questions_in_subcat = Question.objects.filter(
                theme=subcategory,
                category=category
            )
            
            total_in_subcat = questions_in_subcat.count()
            
            # Count correct answers in this subcategory
            correct_in_subcat = quiz_result.answers.filter(
                question__in=questions_in_subcat,
                is_correct=True
            ).values('question').distinct().count()
            
            category_questions += total_in_subcat
            category_correct += correct_in_subcat
        
        # Add to appropriate category type
        category_data = {
            'category': category.name,
            'total_questions': category_questions,
            'correct_questions': category_correct
        }
        
        if category.type == 'EXC':
            exact_stats['categories'].append(category_data)
            exact_stats['total_questions'] += category_questions
            exact_stats['total_correct'] += category_correct
        else:
            natural_stats['categories'].append(category_data)
            natural_stats['total_questions'] += category_questions
            natural_stats['total_correct'] += category_correct
    
    # Calculate percentages
    exact_percentage = calculate_percentage(exact_stats)
    natural_percentage = calculate_percentage(natural_stats)
    total_percentage = context['percentage_score']
 

    closest_natural_value = min(natural_characterization.keys(), key=lambda x: abs(x - round(natural_percentage)))
    closest_exact_value = min(exact_characterization.keys(), key=lambda x: abs(x - round(exact_percentage)))
    summary_characterization[closest_exact_value][closest_natural_value]
    print(summary_characterization, 'summary')
    context.update({
        'exact_stats': exact_stats['categories'],
        'natural_stats': natural_stats['categories'],
        'exact_total_stats': f"{exact_stats['total_correct']}/{exact_stats['total_questions']}",
        'natural_total_stats': f"{natural_stats['total_correct']}/{natural_stats['total_questions']}",
        'recomendation': get_closest_match(recomendation, total_percentage),
        'conclusion': get_conclusion_with_score(conclusion, total_percentage),
        'natural_characterization': get_closest_match(natural_characterization, natural_percentage),
        'exact_characterization': get_closest_match(exact_characterization, exact_percentage),
        'summary_characterization': summary_characterization[closest_exact_value][closest_natural_value],
        
       
        # 'remaining_month': remaining_month.get(int(context.get('quiz_grade', 5)), 0)
    })
    print(context, 'this is context')
    
    return render(request, 'summary_pdf.html', context)


def calculate_percentage(stats: Dict) -> float:
    """Safe percentage calculation"""
    if stats['total_questions'] == 0:
        return 0.0
    return (stats['total_correct'] / stats['total_questions']) * 100

def get_closest_match(data_dict: Dict, score: float) -> str:
    """Find closest key match in a dictionary"""
    closest_key = min(data_dict.keys(), key=lambda x: abs(x - round(score)))
    return data_dict.get(closest_key, "No data available")

def get_conclusion_with_score(conclusion_dict: Dict, score: float) -> str:
    """Insert actual score into conclusion template"""
    base_text = get_closest_match(conclusion_dict, score)
    return base_text.replace("{}%", f"{round(score)}%")

def get_quiz_result_context(quiz_result):
    """
    Prepares common context data for quiz result PDFs
    Args:
        quiz_result: QuizResult model instance
    Returns:
        Dictionary of common template variables
    """
    # Get ALL questions that belong to this quiz's category set
    total_questions = Question.objects.filter(
        theme__category__category_sets=quiz_result.quiz.category_set
    ).count()

    # Calculate correct answers from the user's responses
    correct_answers = quiz_result.answers.filter(is_correct=True).count()
    
    # Calculate percentage score safely
    percentage_score = 0.0
    if total_questions > 0:
        percentage_score = (correct_answers / total_questions) * 100

    context = {
        'quiz_result': quiz_result,
        'name': quiz_result.quiz.name if quiz_result.quiz else "N/A",
        
        'quiz_name': quiz_result.quiz.category_set.name if quiz_result.quiz else "Diagnostic Quiz",
        'quiz_grade': "N/A",  # Add grade field to Quiz model if needed
        'passed_date': quiz_result.created_at.strftime('%d.%m.%Y'),
        'total_questions': total_questions,
        'correct_questions': correct_answers,
        'percentage_score': round(percentage_score, 1),
    }

    return context

def table_pdf(request) -> HttpResponse:
    quiz_result_id = request.GET.get('quiz_result')
    quiz_result = get_object_or_404(QuizResult, pk=quiz_result_id)
    context = get_quiz_result_context(quiz_result)
    
    # Get all categories in the quiz's category set
    categories = Category.objects.filter(
        category_sets=quiz_result.quiz.category_set
    ).prefetch_related(
        Prefetch('subcategory_set', queryset=SubCategory.objects.all()),
        Prefetch('questions', queryset=Question.objects.prefetch_related('answer_set'))
    ).order_by('name')
    
    category_stats = []
    total_questions = 0
    total_correct = 0
    
    for category in categories:
        subcategory_stats = []
        category_questions_count = 0
        category_correct_count = 0
        
        for subcategory in category.subcategory_set.all():
            # Get all questions in this subcategory
            questions_in_subcat = Question.objects.filter(theme=subcategory)
            total_in_subcat = questions_in_subcat.count()
            
            # Get answered questions in this subcategory
            answered_questions = quiz_result.answers.filter(
                question__theme=subcategory
            ).values_list('question', flat=True).distinct()
            
            # Count correct answers in this subcategory
            correct_in_subcat = quiz_result.answers.filter(
                question__theme=subcategory,
                is_correct=True
            ).values('question').distinct().count()
            
            incorrect_in_subcat = total_in_subcat - correct_in_subcat
            
            subcategory_stats.append({
                'subcategory': subcategory.name,
                'total_questions': total_in_subcat,
                'correct_questions': correct_in_subcat,
                'incorrect_questions': incorrect_in_subcat,
                'percentage': (correct_in_subcat / total_in_subcat * 100) if total_in_subcat > 0 else 0
            })
            
            category_questions_count += total_in_subcat
            category_correct_count += correct_in_subcat
        
        total_questions += category_questions_count
        total_correct += category_correct_count
        
        category_stats.append({
            'category': category.name,
            'subcategories': subcategory_stats,
            'total_questions': category_questions_count,
            'correct_questions': category_correct_count,
            'percentage': (category_correct_count / category_questions_count * 100) if category_questions_count > 0 else 0
        })
    
    context.update({
        'category_stats': category_stats,
        'total_questions': total_questions,
        'total_correct': total_correct,
        'total_percentage': (total_correct / total_questions * 100) if total_questions > 0 else 0,
        'quiz_name': quiz_result.quiz.category_set.name,
        'completion_date': quiz_result.created_at.strftime("%B %d, %Y, %I:%M %p")
    })
    
    return render(request, 'table_results_pdf.html', context)


from django.shortcuts import render


def get_admin_statistics_page(request):
    quiz_result = request.GET.get('quiz_result_id')


    return render(request, 'admin_statistics_page.html', context = {'quiz_result_id': quiz_result})