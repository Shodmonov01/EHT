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
                            CategorySetHomeSerializer, UserQuizStarteSerializer,\
                                  DiagnosticInputSerializer, DiagnosticResultSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from oauth2client.service_account import ServiceAccountCredentials
from rest_framework.permissions import AllowAny
import os
from .utils import get_google_sheet, save_to_google_sheet

from datetime import datetime, timedelta
from django.db.models import Prefetch
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
                enum=["ru", "kz"],
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
                    queryset=Answer.objects.all().only("id", "text", "image_ru", "image_kz", "is_correct")
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
            
            # Get appropriate image based on language
            question_image = question.image_ru if lang == 'ru' else question.image_kz
            question_image_url = request.build_absolute_uri(question_image.url) if question_image else None
            
            answers_data = []
            for answer in question.answer_set.all():
                answer_image = answer.image_ru if lang == 'ru' else answer.image_kz
                answer_image_url = request.build_absolute_uri(answer_image.url) if answer_image else None
                
                answers_data.append({
                    "id": answer.id,
                    "text": answer.text,
                    "image": answer_image_url,
                    "is_correct": answer.is_correct
                })
            
            question_data = {
                "id": question.id,
                "text": question.text,
                'correct_answers_count': question.correct_answers_count,
                "subcategory": question.theme.name,
                "image": question_image_url,
                "answers": answers_data
            }
            
            category_questions[category.id]["questions"].append(question_data)

        return Response(list(category_questions.values()), status=200)
    

    
from collections import defaultdict
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
        quiz_questions = Question.objects.filter(
            theme__category__category_sets=quiz.category_set
        ).prefetch_related('answer_set')
        quiz_question_ids = set(quiz_questions.values_list('id', flat=True))
        
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
        
        # Step 5: Calculate score with new scoring system
        selected_answers = quiz_result.answers.all().select_related('question')
        answers_by_question = defaultdict(list)
        for answer in selected_answers:
            answers_by_question[answer.question_id].append(answer)

        total_possible = 0
        total_user_points = 0
        question_stats = []

        for question in quiz_questions:
            correct_needed = question.correct_answers_count
            max_possible = 2 if correct_needed in [2, 3] else 1
            total_possible += max_possible

            selected = answers_by_question.get(question.id, [])
            selected_correct = sum(1 for a in selected if a.is_correct)
            selected_incorrect = len(selected) - selected_correct

            # Calculate points based on question type
            if correct_needed == 1:
                points = 1 if (selected_correct == 1 and selected_incorrect == 0) else 0
            elif correct_needed == 2:
                if selected_correct == 2 and selected_incorrect == 0:
                    points = 2
                elif (selected_correct >= 1) and (selected_incorrect == 0 or selected_correct == 2):
                    points = 1
                else:
                    points = 0
            elif correct_needed == 3:
                if selected_correct == 3 and selected_incorrect == 0:
                    points = 2
                elif selected_correct >= 2:
                    points = 1
                else:
                    points = 0
            
            total_user_points += points
            question_stats.append({
                'question_id': question.id,
                'correct_needed': correct_needed,
                'selected_correct': selected_correct,
                'selected_incorrect': selected_incorrect,
                'points_earned': points
            })

        # Save scoring metrics
        quiz_result.total_possible_points = total_possible
        quiz_result.user_points = total_user_points
        quiz_result.save()

        # Calculate percentage score
        percentage_score = (total_user_points / total_possible * 100) if total_possible > 0 else 0
        
        # Generate admin statistics URL
        category_set_name = quiz.category_set.name if quiz.category_set else ""
        admin_statistics_url = (
            f"{BASE_URL}/quiz/admin/statistics/?quiz_result_id={quiz_result.id}"
            f"&percentage={percentage_score:.1f}"
            f"&score={total_user_points}/{total_possible}"
            f"&quiz_name={category_set_name}"
        )
        
        # Update Google Sheet with quiz result data
        try:
            async_task(
                save_to_google_sheet,
                user_token=quiz.user_token,
                score=round(percentage_score, 2),
                result_url=request.build_absolute_uri(admin_statistics_url)
            )
        except Exception as e:
            print(f"Error updating Google Sheet: {e}")
        
        # Step 6: Prepare response data
        response_data = {
            'result': QuizResultDetailSerializer(
                quiz_result,
                context={
                    'request': request,
                    'question_stats': question_stats
                }
            ).data,
            'score': round(percentage_score, 2),
            'total_possible_points': total_possible,
            'user_points': total_user_points,
            'admin_statistics_url': admin_statistics_url,
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


def summary_pdf(request):
    quiz_result_id = request.GET.get('quiz_result')
    quiz_result = get_object_or_404(QuizResult, pk=quiz_result_id)
    context = get_quiz_result_context(quiz_result)
    
    categories = Category.objects.filter(
        category_sets=quiz_result.quiz.category_set
    ).prefetch_related(
        Prefetch('subcategory_set', queryset=SubCategory.objects.all())
    ).order_by('name')
    
    exact_stats = {'categories': [], 'total_possible': 0, 'user_points': 0}
    natural_stats = {'categories': [], 'total_possible': 0, 'user_points': 0}
    
    for category in categories:
        category_possible = 0
        category_points = 0
        
        for subcategory in category.subcategory_set.all():
            questions = Question.objects.filter(
                theme=subcategory,
                category=category
            )
            
            # Calculate possible points for this subcategory
            subcat_possible = sum(
                2 if q.correct_answers_count in [2,3] else 1 
                for q in questions
            )
            
            # Calculate earned points for this subcategory
            subcat_points = 0
            for q in questions:
                correct_answers = quiz_result.answers.filter(
                    question=q,
                    is_correct=True
                ).count()
                incorrect_answers = quiz_result.answers.filter(
                    question=q,
                    is_correct=False
                ).count()
                
                if q.correct_answers_count == 1:
                    subcat_points += 1 if (correct_answers == 1 and incorrect_answers == 0) else 0
                elif q.correct_answers_count == 2:
                    if correct_answers == 2 and incorrect_answers == 0:
                        subcat_points += 2
                    elif (correct_answers >= 1) and (incorrect_answers == 0 or correct_answers == 2):
                        subcat_points += 1
                elif q.correct_answers_count == 3:
                    if correct_answers == 3 and incorrect_answers == 0:
                        subcat_points += 2
                    elif correct_answers >= 2:
                        subcat_points += 1
            
            category_possible += subcat_possible
            category_points += subcat_points
        
        category_data = {
            'category': category.name,
            'total_possible': category_possible,
            'user_points': category_points
        }
        
        if category.type == 'EXC':
            exact_stats['categories'].append(category_data)
            exact_stats['total_possible'] += category_possible
            exact_stats['user_points'] += category_points
        else:
            natural_stats['categories'].append(category_data)
            natural_stats['total_possible'] += category_possible
            natural_stats['user_points'] += category_points
    print(natural_stats, 'nat')
    # Calculate percentages
    exact_percentage = (exact_stats['user_points'] / exact_stats['total_possible'] * 100) if exact_stats['total_possible'] > 0 else 0
    natural_percentage = (natural_stats['user_points'] / natural_stats['total_possible'] * 100) if natural_stats['total_possible'] > 0 else 0
    
    closest_natural = min(natural_characterization.keys(), key=lambda x: abs(x - round(natural_percentage)))
    closest_exact = min(exact_characterization.keys(), key=lambda x: abs(x - round(exact_percentage)))
    
    
    context.update({
        'exact_stats': exact_stats['categories'],
        'natural_stats': natural_stats['categories'],
        'exact_total_stats': f"{exact_stats['user_points']}/{exact_stats['total_possible']}",
        'natural_total_stats': f"{natural_stats['user_points']}/{natural_stats['total_possible']}",
        'exact_percentage': round(exact_percentage, 2),
        'natural_percentage': round(natural_percentage, 2),
        'recomendation': get_closest_match(recomendation, context['percentage_score']),
        'conclusion': get_conclusion_with_score(conclusion, context['percentage_score']),
        'natural_characterization': get_closest_match(natural_characterization, natural_percentage),
        'exact_characterization': get_closest_match(exact_characterization, exact_percentage),
        'summary_characterization': summary_characterization[closest_exact][closest_natural],
    })
    
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
    Updated to use points system instead of simple correct counts
    """
    context = {
        'quiz_result': quiz_result,
        'name': quiz_result.quiz.name if quiz_result.quiz else "N/A",
        'quiz_name': quiz_result.quiz.category_set.name if quiz_result.quiz else "Diagnostic Quiz",
        'passed_date': quiz_result.created_at.strftime('%d.%m.%Y'),
        'total_possible': quiz_result.total_possible_points,
        'user_points': quiz_result.user_points,
        'percentage_score': round(
            (quiz_result.user_points / quiz_result.total_possible_points * 100) 
            if quiz_result.total_possible_points > 0 else 0,
            2
        )
    }
    return context


def table_pdf(request) -> HttpResponse:
    quiz_result_id = request.GET.get('quiz_result')
    quiz_result = get_object_or_404(QuizResult, pk=quiz_result_id)
    context = get_quiz_result_context(quiz_result)
    
    categories = Category.objects.filter(
        category_sets=quiz_result.quiz.category_set
    ).prefetch_related(
        Prefetch('subcategory_set', queryset=SubCategory.objects.all()),
        Prefetch('questions', queryset=Question.objects.prefetch_related('answer_set'))
    ).order_by('name')
    
    category_stats = []
    total_questions = 0
    correct_questions = 0
    total_possible = 0
    total_points = 0
    
    for category in categories:
        subcategory_stats = []
        category_possible = 0
        category_points = 0
        category_total_questions = 0
        category_correct_questions = 0
        
        for subcategory in category.subcategory_set.all():
            questions = Question.objects.filter(theme=subcategory)
            subcat_possible = 0
            subcat_points = 0
            total_subcategory_questions = questions.count()
            correct_subcategory_questions = 0
            
            for q in questions:
                # Calculate possible points for this question
                q_possible = 2 if q.correct_answers_count in [2, 3] else 1
                subcat_possible += q_possible
                
                # Calculate earned points
                correct_answers = quiz_result.answers.filter(
                    question=q,
                    is_correct=True
                ).count()
                incorrect_answers = quiz_result.answers.filter(
                    question=q,
                    is_correct=False
                ).count()
                
                points_earned = 0
                if q.correct_answers_count == 1:
                    points_earned = 1 if (correct_answers == 1 and incorrect_answers == 0) else 0
                elif q.correct_answers_count == 2:
                    if correct_answers == 2 and incorrect_answers == 0:
                        points_earned = 2
                    elif (correct_answers >= 1) and (incorrect_answers == 0 or correct_answers == 2):
                        points_earned = 1
                elif q.correct_answers_count == 3:
                    if correct_answers == 3 and incorrect_answers == 0:
                        points_earned = 2
                    elif correct_answers >= 2:
                        points_earned = 1
                
                subcat_points += points_earned
                
                # For backward compatibility - count questions as correct if any points were earned
                if points_earned > 0:
                    correct_subcategory_questions += 1
            
            subcategory_stats.append({
                'subcategory': subcategory.name,
                'total_questions': total_subcategory_questions,
                'correct_questions': correct_subcategory_questions,
                'incorrect_questions': total_subcategory_questions - correct_subcategory_questions,
                'total_possible': subcat_possible,
                'user_points': subcat_points,
                'percentage': (subcat_points / subcat_possible * 100) if subcat_possible > 0 else 0
            })
            
            category_possible += subcat_possible
            category_points += subcat_points
            category_total_questions += total_subcategory_questions
            category_correct_questions += correct_subcategory_questions
        
        total_possible += category_possible
        total_points += category_points
        total_questions += category_total_questions
        correct_questions += category_correct_questions
        
        category_stats.append({
            'category': category.name,
            'subcategories': subcategory_stats,
            'total_questions': category_total_questions,
            'correct_questions': category_correct_questions,
            'incorrect_questions': category_total_questions - category_correct_questions,
            'total_possible': category_possible,
            'user_points': category_points,
            'percentage': (category_points / category_possible * 100) if category_possible > 0 else 0
        })
    
    context.update({
        'category_stats': category_stats,
        'total_questions': total_questions,
        'correct_questions': correct_questions,
        'total_possible': total_possible,
        'total_points': total_points,
        'total_percentage': (total_points / total_possible * 100) if total_possible > 0 else 0,
        'completion_date': quiz_result.created_at.strftime("%B %d, %Y, %I:%M %p")
    })
    
    return render(request, 'table_results_pdf.html', context)



from django.shortcuts import render


def get_admin_statistics_page(request):
    quiz_result = request.GET.get('quiz_result_id')
    print(quiz_result, 'quiz result')
    return render(request, 'admin_statistics_page.html', context = {'quiz_result_id': quiz_result})

##############################33




SUBJECT_EVALUATIONS = {
    'reading_literacy': {
        'low': "По грамотности чтения показан низкий результат. Необходимо уделить больше внимания развитию навыков понимания текста, анализу информации и критическому мышлению. Рекомендуется регулярное чтение различных типов текстов и выполнение упражнений на понимание прочитанного.",
        'medium': "По грамотности чтения показан средний результат. У вас есть базовые навыки работы с текстом, но есть потенциал для улучшения. Рекомендуется практиковать анализ сложных текстов и работу с различными типами информации.",
        'high': "Отличный результат по грамотности чтения! Вы демонстрируете высокий уровень понимания текста и способность к анализу информации. Продолжайте развивать эти навыки для поддержания высокого уровня."
    },
    'math_literacy': {
        'low': "Математическая грамотность требует серьезного внимания. Необходимо укрепить базовые математические концепции и развить навыки решения практических задач. Рекомендуется систематическое изучение основных тем и регулярная практика.",
        'medium': "Средний уровень математической грамотности. Базовые навыки присутствуют, но требуется дополнительная работа над сложными задачами. Сосредоточьтесь на развитии логического мышления и практическом применении математических знаний.",
        'high': "Превосходный результат по математической грамотности! Вы показываете отличное понимание математических концепций и умение применять их на практике. Продолжайте развивать аналитические способности."
    },
    'history_kazakhstan': {
        'low': "Знания по истории Казахстана нуждаются в значительном улучшении. Рекомендуется систематическое изучение ключевых исторических периодов, важных событий и личностей. Уделите особое внимание современной истории Казахстана.",
        'medium': "Удовлетворительные знания по истории Казахстана. Основные факты известны, но требуется более глубокое понимание исторических процессов. Рекомендуется изучение дополнительных источников и анализ причинно-следственных связей.",
        'high': "Отличные знания по истории Казахстана! Вы демонстрируете глубокое понимание исторических процессов и их влияния на современность. Продолжайте изучать детали и различные интерпретации исторических событий."
    },
    'profile_subject': {
        'low': "Результат по профильному предмету {subject_name} требует серьезной работы. Это критически важный предмет для вашей будущей специальности. Рекомендуется интенсивная подготовка с репетитором и дополнительное изучение материала.",
        'medium': "Средний результат по профильному предмету {subject_name}. Есть базовые знания, но для успешного поступления требуется значительное улучшение. Сосредоточьтесь на изучении сложных тем и решении практических задач.",
        'high': "Превосходный результат по профильному предмету {subject_name}! Это дает вам значительное преимущество при поступлении. Продолжайте углублять знания и поддерживать высокий уровень подготовки."
    }
}

GROUP_EVALUATIONS = {
    'general_subjects': {
        'low': "Общие предметы (грамотность чтения, математическая грамотность, история Казахстана) требуют комплексной подготовки. Эти предметы формируют основу академических знаний. Рекомендуется составить детальный план подготовки и уделять равное внимание всем трем направлениям.",
        'medium': "По общим предметам показаны удовлетворительные результаты. Есть хорошая база, но необходимо усилить подготовку для достижения более высоких результатов. Особое внимание уделите предметам с наиболее низкими показателями.",
        'high': "Отличные результаты по общим предметам! Вы демонстрируете высокий уровень общей академической подготовки. Это создает прочную основу для дальнейшего обучения. Поддерживайте достигнутый уровень."
    },
    'profile_subjects': {
        'low': "Профильные предметы показывают низкий результат, что критично для поступления по выбранной специальности. Необходима интенсивная подготовка с акцентом на эти дисциплины. Рассмотрите возможность занятий с репетитором и дополнительных курсов.",
        'medium': "Средние результаты по профильным предметам. Есть потенциал для значительного улучшения. Профильные предметы имеют особое значение для поступления, поэтому рекомендуется усилить подготовку именно по этим дисциплинам.",
        'high': "Превосходные результаты по профильным предметам! Это дает вам отличные шансы на поступление по выбранной специальности. Продолжайте углублять знания в профильных областях."
    }
}

ADMISSION_PROBABILITY_COMMENTS = {
    'low': "Низкий шанс поступления. Требуется серьезная подготовка для повышения конкурентоспособности.",
    'medium': "Средний шанс поступления. При должной подготовке есть хорошие перспективы для успешного поступления.",
    'high': "Высокий шанс поступления. Отличные результаты дают вам значительные преимущества."
}

def get_subject_evaluation_level(percentage):
    """Determine evaluation level based on percentage"""
    if percentage < 50:
        return 'low'
    elif percentage <= 70:
        return 'medium'
    else:
        return 'high'

def get_subject_detailed_analysis(quiz_result):
    """Generate detailed analysis for each subject"""
    categories = Category.objects.filter(
        category_sets=quiz_result.quiz.category_set
    ).prefetch_related(
        Prefetch('subcategory_set', queryset=SubCategory.objects.all())
    ).order_by('name')
    
    subject_analysis = {}
    general_subjects = []
    profile_subjects = []
    
    for category in categories:
        category_possible = 0
        category_points = 0
        
        # Calculate points for this category (same logic as your original)
        for subcategory in category.subcategory_set.all():
            questions = Question.objects.filter(
                theme=subcategory,
                category=category
            )
            
            subcat_possible = sum(
                2 if q.correct_answers_count in [2,3] else 1 
                for q in questions
            )
            
            subcat_points = 0
            for q in questions:
                correct_answers = quiz_result.answers.filter(
                    question=q,
                    is_correct=True
                ).count()
                incorrect_answers = quiz_result.answers.filter(
                    question=q,
                    is_correct=False
                ).count()
                
                if q.correct_answers_count == 1:
                    subcat_points += 1 if (correct_answers == 1 and incorrect_answers == 0) else 0
                elif q.correct_answers_count == 2:
                    if correct_answers == 2 and incorrect_answers == 0:
                        subcat_points += 2
                    elif (correct_answers >= 1) and (incorrect_answers == 0 or correct_answers == 2):
                        subcat_points += 1
                elif q.correct_answers_count == 3:
                    if correct_answers == 3 and incorrect_answers == 0:
                        subcat_points += 2
                    elif correct_answers >= 2:
                        subcat_points += 1
            
            category_possible += subcat_possible
            category_points += subcat_points
        
        # Calculate percentage for this category
        category_percentage = (category_points / category_possible * 100) if category_possible > 0 else 0
        evaluation_level = get_subject_evaluation_level(category_percentage)
        
        # Determine subject type and get appropriate evaluation text
        if category.subject_type == 'MAIN':
            # Map category names to evaluation keys
            if 'чтение' in category.name.lower() or 'грамотность чтения' in category.name.lower():
                evaluation_text = SUBJECT_EVALUATIONS['reading_literacy'][evaluation_level]
                subject_key = 'reading_literacy'
            elif 'математ' in category.name.lower():
                evaluation_text = SUBJECT_EVALUATIONS['math_literacy'][evaluation_level]
                subject_key = 'math_literacy'
            elif 'история' in category.name.lower():
                evaluation_text = SUBJECT_EVALUATIONS['history_kazakhstan'][evaluation_level]
                subject_key = 'history_kazakhstan'
            else:
                evaluation_text = SUBJECT_EVALUATIONS['profile_subject'][evaluation_level].format(
                    subject_name=category.name
                )
                subject_key = 'general_other'
            
            general_subjects.append({
                'name': category.name,
                'points': category_points,
                'possible': category_possible,
                'percentage': round(category_percentage, 2),
                'evaluation_level': evaluation_level,
                'evaluation_text': evaluation_text
            })
        else:  # PROFILE
            evaluation_text = SUBJECT_EVALUATIONS['profile_subject'][evaluation_level].format(
                subject_name=category.name
            )
            
            profile_subjects.append({
                'name': category.name,
                'points': category_points,
                'possible': category_possible,
                'percentage': round(category_percentage, 2),
                'evaluation_level': evaluation_level,
                'evaluation_text': evaluation_text
            })
    
    return {
        'general_subjects': general_subjects,
        'profile_subjects': profile_subjects
    }

def get_group_analysis(subjects_data):
    """Generate group analysis for general and profile subjects"""
    if not subjects_data:
        return {
            'average_percentage': 0,
            'evaluation_level': 'low',
            'evaluation_text': "Нет данных для анализа"
        }
    
    # Calculate average percentage
    total_points = sum(s['points'] for s in subjects_data)
    total_possible = sum(s['possible'] for s in subjects_data)
    average_percentage = (total_points / total_possible * 100) if total_possible > 0 else 0
    
    evaluation_level = get_subject_evaluation_level(average_percentage)
    
    return {
        'average_percentage': round(average_percentage, 2),
        'evaluation_level': evaluation_level,
        'total_points': total_points,
        'total_possible': total_possible
    }

def calculate_admission_probability(total_percentage):
    """Calculate admission probability with and without preparation"""
    import random
    
    # Base probability without preparation
    if total_percentage >= 80:
        base_prob = random.randint(75, 90)
    elif total_percentage >= 60:
        base_prob = random.randint(45, 70)
    elif total_percentage >= 40:
        base_prob = random.randint(20, 50)
    else:
        base_prob = random.randint(5, 25)
    
    # Probability with preparation (30-40% improvement, but capped)
    improvement = random.randint(30, 40)
    with_prep_prob = min(base_prob + improvement, 94)  # Cap at 94% to avoid 95%+
    
    # Ensure we don't show 0%
    base_prob = max(base_prob, 1)
    with_prep_prob = max(with_prep_prob, 1)
    
    # Get evaluation comments
    base_comment = ADMISSION_PROBABILITY_COMMENTS[
        'high' if base_prob >= 70 else 'medium' if base_prob >= 40 else 'low'
    ]
    prep_comment = ADMISSION_PROBABILITY_COMMENTS[
        'high' if with_prep_prob >= 70 else 'medium' if with_prep_prob >= 40 else 'low'
    ]
    
    return {
        'without_preparation': {
            'percentage': base_prob,
            'comment': base_comment
        },
        'with_preparation': {
            'percentage': with_prep_prob,
            'comment': prep_comment
        },
        'improvement_potential': with_prep_prob - base_prob
    }

def get_quiz_result_context_v2(quiz_result):
    """
    Enhanced version with detailed subject analysis and admission probability
    """
    # Get subject analysis
    subject_analysis = get_subject_detailed_analysis(quiz_result)
    
    # Get group analysis
    general_analysis = get_group_analysis(subject_analysis['general_subjects'])
    profile_analysis = get_group_analysis(subject_analysis['profile_subjects'])
    
    # Add group evaluation texts
    general_analysis['evaluation_text'] = GROUP_EVALUATIONS['general_subjects'][general_analysis['evaluation_level']]
    profile_analysis['evaluation_text'] = GROUP_EVALUATIONS['profile_subjects'][profile_analysis['evaluation_level']]
    
    # Calculate overall percentage
    overall_percentage = round(
        (quiz_result.user_points / quiz_result.total_possible_points * 100) 
        if quiz_result.total_possible_points > 0 else 0,
        2
    )
    
    # Calculate admission probability
    admission_probability = calculate_admission_probability(overall_percentage)
    
    context = {
        'quiz_result': quiz_result,
        'name': quiz_result.quiz.name if quiz_result.quiz else "N/A",
        'quiz_name': quiz_result.quiz.category_set.name if quiz_result.quiz else "Diagnostic Quiz",
        'passed_date': quiz_result.created_at.strftime('%d.%m.%Y'),
        'total_possible': quiz_result.total_possible_points,
        'user_points': quiz_result.user_points,
        'percentage_score': overall_percentage,
        
        # New detailed analysis
        'subject_analysis': subject_analysis,
        'general_subjects_analysis': general_analysis,
        'profile_subjects_analysis': profile_analysis,
        'admission_probability': admission_probability,
        
        # Summary statistics
        'total_subjects': len(subject_analysis['general_subjects']) + len(subject_analysis['profile_subjects']),
        'subjects_passed': len([s for s in subject_analysis['general_subjects'] + subject_analysis['profile_subjects'] if s['percentage'] >= 50]),
    }
    
    return context

from .models import Specialization

def summary_pdf_v2(request):
    """Updated summary_pdf function with enhanced context"""
    quiz_result_id = request.GET.get('quiz_result')
    print(quiz_result_id, 'quiz result id ')
    quiz_result = get_object_or_404(QuizResult, pk=quiz_result_id)

    related_specializations = Specialization.objects.filter(
   
    categories=quiz_result.quiz.category_set
        ).distinct()
    
    print(related_specializations, 'related specialities')
    context = get_quiz_result_context_v2(quiz_result)
    
    subject_analysis = context['subject_analysis']
    print(subject_analysis, 'subject analysiz')

    specialization_probabilities = []

    for specialization in related_specializations:
        print(specialization, 'specialization  ----')
        # Find categories in this specialization
        spec_categories = specialization.categories.all()
        print(spec_categories, 'spec categorieis')
        new_data = []
        for d in spec_categories:
            print(d, 'nameeee')
            new_data.append(Category.objects.filter())

        
        # Filter subject_analysis to only include subjects in this specialization
        total_points = 0
        total_possible = 0
        
        for subject in subject_analysis['general_subjects'] + subject_analysis['profile_subjects']:
            if any(c.name == subject['name'] for c in spec_categories):
                total_points += subject['points']
                total_possible += subject['possible']
    
    # Calculate percentage
        percentage = (total_points / total_possible * 100) if total_possible > 0 else 0
        admission = calculate_admission_probability(percentage)

        specialization_probabilities.append({
            'name': specialization.name,
            'percentage': round(percentage, 2),
            'admission': admission
        })

    
    # Get enhanced context
    context = get_quiz_result_context_v2(quiz_result)
    context.update({
        'specializations': related_specializations
    })

    print(context['specializations'], 'speciallll')
    
    # Keep your existing exact/natural stats logic if needed
    categories = Category.objects.filter(
        category_sets=quiz_result.quiz.category_set
    ).prefetch_related(
        Prefetch('subcategory_set', queryset=SubCategory.objects.all())
    ).order_by('name')
    
    exact_stats = {'categories': [], 'total_possible': 0, 'user_points': 0}
    natural_stats = {'categories': [], 'total_possible': 0, 'user_points': 0}
    
    for category in categories:
        category_possible = 0
        category_points = 0
        
        for subcategory in category.subcategory_set.all():
            questions = Question.objects.filter(
                theme=subcategory,
                category=category
            )
            
            subcat_possible = sum(
                2 if q.correct_answers_count in [2,3] else 1 
                for q in questions
            )
            
            subcat_points = 0
            for q in questions:
                correct_answers = quiz_result.answers.filter(
                    question=q,
                    is_correct=True
                ).count()
                incorrect_answers = quiz_result.answers.filter(
                    question=q,
                    is_correct=False
                ).count()
                
                if q.correct_answers_count == 1:
                    subcat_points += 1 if (correct_answers == 1 and incorrect_answers == 0) else 0
                elif q.correct_answers_count == 2:
                    if correct_answers == 2 and incorrect_answers == 0:
                        subcat_points += 2
                    elif (correct_answers >= 1) and (incorrect_answers == 0 or correct_answers == 2):
                        subcat_points += 1
                elif q.correct_answers_count == 3:
                    if correct_answers == 3 and incorrect_answers == 0:
                        subcat_points += 2
                    elif correct_answers >= 2:
                        subcat_points += 1
            
            category_possible += subcat_possible
            category_points += subcat_points
        
        category_data = {
            'category': category.name,
            'total_possible': category_possible,
            'user_points': category_points,
            'percentage': round((category_points / category_possible * 100) if category_possible > 0 else 0, 2)
        }
        
        if category.type == 'EXC':
            exact_stats['categories'].append(category_data)
            exact_stats['total_possible'] += category_possible
            exact_stats['user_points'] += category_points
        else:
            natural_stats['categories'].append(category_data)
            natural_stats['total_possible'] += category_possible
            natural_stats['user_points'] += category_points
    
    # Calculate percentages
    exact_percentage = (exact_stats['user_points'] / exact_stats['total_possible'] * 100) if exact_stats['total_possible'] > 0 else 0
    natural_percentage = (natural_stats['user_points'] / natural_stats['total_possible'] * 100) if natural_stats['total_possible'] > 0 else 0
    
    # Add existing characterizations if you have them
    # closest_natural = min(natural_characterization.keys(), key=lambda x: abs(x - round(natural_percentage)))
    # closest_exact = min(exact_characterization.keys(), key=lambda x: abs(x - round(exact_percentage)))
    
    context.update({
        'exact_stats': exact_stats['categories'],
        'natural_stats': natural_stats['categories'],
        'exact_total_stats': f"{exact_stats['user_points']}/{exact_stats['total_possible']}",
        'natural_total_stats': f"{natural_stats['user_points']}/{natural_stats['total_possible']}",
        'exact_percentage': round(exact_percentage, 2),
        'natural_percentage': round(natural_percentage, 2),
        'current_year' : datetime.now().year,
            'specialization_probabilities': specialization_probabilities,
        # Add your existing characterizations here if available
        # 'recomendation': get_closest_match(recomendation, context['percentage_score']),
        # 'conclusion': get_conclusion_with_score(conclusion, context['percentage_score']),
        # 'natural_characterization': get_closest_match(natural_characterization, natural_percentage),
        # 'exact_characterization': get_closest_match(exact_characterization, exact_percentage),
        # 'summary_characterization': summary_characterization[closest_exact][closest_natural],
    })

    print(context, 'this is context----')
    print(
        'this iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii'
    )
    return render(request, 'summary.html', context)

from rest_framework import generics

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


##################################
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from django.db import transaction
import uuid
from datetime import datetime


class DiagnosticService:
    """Service class for diagnostic calculations and evaluations"""
    
    TOTAL_MAX_POINTS = 140
    
    @staticmethod
    def get_max_points_for_category(category):
        """Get max points based on category subject type"""
        return 40 if category.subject_type == 'PROFILE' else 20
    
    @staticmethod
    def calculate_percentage(points, max_points):
        """Calculate percentage"""
        return (points / max_points) * 100 if max_points > 0 else 0
    
    @staticmethod
    def get_level(percentage):
        """Determine level based on percentage"""
        if percentage >= 70:
            return "высокий"
        elif percentage >= 50:
            return "средний"
        else:
            return "низкий"
    
    @staticmethod
    def evaluate_subject(category, points):
        """Evaluate individual subject"""
        max_points = DiagnosticService.get_max_points_for_category(category)
        percentage = DiagnosticService.calculate_percentage(points, max_points)
        level = DiagnosticService.get_level(percentage)
        
        return {
            'category_id': category.id,
            'category_name': category.name,
            'category_type': category.type,
            'subject_type': category.subject_type,
            'points': points,
            'max_points': max_points,
            'percentage': round(percentage, 2),
            'level': level
        }
    
    @staticmethod
    def evaluate_groups(subject_evaluations):
        """Evaluate groups of subjects by subject_type"""
        groups = {}
        
        # Group subjects by subject_type
        for subject in subject_evaluations:
            group_type = subject['subject_type']
            if group_type not in groups:
                groups[group_type] = {
                    'subjects': [],
                    'total_points': 0,
                    'max_points': 0
                }
            
            groups[group_type]['subjects'].append(subject)
            groups[group_type]['total_points'] += subject['points']
            groups[group_type]['max_points'] += subject['max_points']
        
        # Calculate group evaluations
        group_evaluations = []
        for group_type, group_data in groups.items():
            percentage = DiagnosticService.calculate_percentage(
                group_data['total_points'], 
                group_data['max_points']
            )
            level = DiagnosticService.get_level(percentage)
            
            group_name = "Основные предметы" if group_type == 'MAIN' else "Профильные предметы"
            
            group_evaluations.append({
                'group_name': group_name,
                'group_type': group_type,
                'total_points': group_data['total_points'],
                'max_points': group_data['max_points'],
                'percentage': round(percentage, 2),
                'level': level,
                'subjects_count': len(group_data['subjects'])
            })
        
        return group_evaluations
    
    @staticmethod
    def generate_recommendations(subject_evaluations, group_evaluations, total_percentage):
        """Generate detailed recommendations"""
        recommendations = []
        
        # Overall assessment
        if total_percentage < 50:
            recommendations.append(
                "Общий уровень подготовки требует значительного улучшения. "
                "Рекомендуется комплексная подготовка по всем предметам."
            )
        elif total_percentage < 70:
            recommendations.append(
                "Уровень подготовки средний. Есть потенциал для улучшения результатов "
                "с целенаправленной подготовкой."
            )
        else:
            recommendations.append(
                "Хороший уровень подготовки. Рекомендуется поддерживать текущий уровень "
                "и работать над слабыми местами."
            )
        
        # Group-specific recommendations
        for group in group_evaluations:
            if group['level'] == 'низкий':
                if group['group_type'] == 'MAIN':
                    recommendations.append(
                        f"Основные предметы ({group['percentage']:.1f}%): "
                        "Необходимо усилить подготовку по базовым дисциплинам. "
                        "Рекомендуются дополнительные занятия и повторение основных тем."
                    )
                else:
                    recommendations.append(
                        f"Профильные предметы ({group['percentage']:.1f}%): "
                        "Требуется интенсивная подготовка по специализированным дисциплинам. "
                        "Рекомендуется работа с преподавателем и решение практических задач."
                    )
        
        # Subject-specific recommendations
        weak_subjects = [s for s in subject_evaluations if s['level'] == 'низкий']
        if weak_subjects:
            subject_names = [s['category_name'] for s in weak_subjects]
            recommendations.append(
                f"Слабые предметы: {', '.join(subject_names)}. "
                "Рекомендуется уделить этим предметам особое внимание."
            )
        
        return " ".join(recommendations)
    
    @staticmethod
    def calculate_admission_probability(total_percentage, subject_evaluations):
        """Calculate admission probability"""
        # Basic probability calculation based on total percentage
        base_probability = min(total_percentage / 100, 0.95)
        
        # Adjust based on profile subjects performance
        profile_subjects = [s for s in subject_evaluations if s['subject_type'] == 'PROFILE']
        if profile_subjects:
            profile_avg = sum(s['percentage'] for s in profile_subjects) / len(profile_subjects)
            profile_factor = profile_avg / 100
            base_probability = (base_probability + profile_factor) / 2
        
        without_prep = max(0.05, min(0.95, base_probability))
        with_prep = max(0.1, min(0.98, base_probability + 0.3))
        
        return {
            'without_preparation': round(without_prep * 100, 1),
            'with_preparation': round(with_prep * 100, 1)
        }


class DiagnosticCreateView(APIView):
    """API endpoint for creating diagnostic results"""
    @extend_schema(
        request=DiagnosticInputSerializer,  # Specifies the request body schema

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
        serializer = DiagnosticInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        try:
            with transaction.atomic():
                # Get categories for the provided scores
                category_ids = [score['category_id'] for score in validated_data['subject_scores']]
                categories = Category.objects.filter(id__in=category_ids)
                
                if len(categories) != len(category_ids):
                    return Response(
                        {'error': 'Some categories not found'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create category lookup
                category_lookup = {cat.id: cat for cat in categories}
                
                # Evaluate subjects
                subject_evaluations = []
                total_points = 0
                
                for score_data in validated_data['subject_scores']:
                    category = category_lookup[score_data['category_id']]
                    points = score_data['points']
                    total_points += points
                    
                    evaluation = DiagnosticService.evaluate_subject(category, points)
                    subject_evaluations.append(evaluation)
                
                # Evaluate groups
                group_evaluations = DiagnosticService.evaluate_groups(subject_evaluations)
                
                # Calculate total percentage
                total_percentage = DiagnosticService.calculate_percentage(
                    total_points, 
                    DiagnosticService.TOTAL_MAX_POINTS
                )
                
                # Generate recommendations
                recommendations = DiagnosticService.generate_recommendations(
                    subject_evaluations, 
                    group_evaluations, 
                    total_percentage
                )
                
                # Calculate admission probability
                admission_probability = DiagnosticService.calculate_admission_probability(
                    total_percentage, 
                    subject_evaluations
                )
                
                # Create QuizResult record
                user_token = uuid.uuid4()
                quiz_result = QuizResult.objects.create(
                    user_token=user_token,
                    total_possible_points=DiagnosticService.TOTAL_MAX_POINTS,
                    user_points=total_points
                )
                
                # Prepare response data
                result_data = {
                    'user_token': user_token,
                    'name': validated_data['name'],
                    'phone_number': validated_data['phone_number'],
                    'total_points': total_points,
                    'total_possible_points': DiagnosticService.TOTAL_MAX_POINTS,
                    'total_percentage': round(total_percentage, 2),
                    'subject_evaluations': subject_evaluations,
                    'group_evaluations': group_evaluations,
                    'recommendations': recommendations,
                    'admission_probability': admission_probability,
                    'created_at': quiz_result.created_at
                }
                
                response_serializer = DiagnosticResultSerializer(result_data)
                return Response(
                    response_serializer.data, 
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            return Response(
                {'error': f'An error occurred: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoriesListView(APIView):
    """API endpoint to get available categories for diagnostic"""
    
    def get(self, request):
        categories = Category.objects.all().values(
            'id', 'name', 'type', 'subject_type'
        )
        
        # Add max_points to each category
        categories_with_points = []
        for category in categories:
            cat_obj = Category.objects.get(id=category['id'])
            category['max_points'] = DiagnosticService.get_max_points_for_category(cat_obj)
            categories_with_points.append(category)
        
        return Response({
            'categories': categories_with_points,
            'total_max_points': DiagnosticService.TOTAL_MAX_POINTS
        })


class DiagnosticResultView(APIView):
    """API endpoint to retrieve diagnostic result by token"""
    
    def get(self, request, token):
        try:
            quiz_result = QuizResult.objects.get(user_token=token)
            
            # For this endpoint, you might want to reconstruct the evaluation
            # or store it in the database. For now, return basic info
            return Response({
                'user_token': quiz_result.user_token,
                'total_points': quiz_result.user_points,
                'total_possible_points': quiz_result.total_possible_points,
                'created_at': quiz_result.created_at,
                'pdf_url': quiz_result.get_pdf_url()
            })
            
        except QuizResult.DoesNotExist:
            return Response(
                {'error': 'Diagnostic result not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ListProfileSubjectsView(generics.ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        qs = Category.objects.filter(subject_type="PROFILE")[:2]
        return qs
    

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import EntDiagnosisInputSerializer

# --- Utility functions (copied from previous step) ---
def calculate_subject_level(score, max_score):
    p = (score / max_score) * 100
    return "низкий" if p < 50 else "средний" if p <= 70 else "высокий"

def calculate_group_level(scores, max_scores):
    total = sum(scores)
    total_max = sum(max_scores)
    p = (total / total_max) * 100
    return "низкий" if p < 50 else "средний" if p <= 70 else "высокий"

def get_subject_recommendation(subject, level):
    rec = {
        "reading_literacy": {
            "низкий": "Трудности с пониманием текстов.",
            "средний": "Базовое понимание есть.",
            "высокий": "Хорошие навыки."
        },
        "math_literacy": {
            "низкий": "Сложно применять математику.",
            "средний": "Понимание есть, но есть пробелы.",
            "высокий": "Уверенные знания."
        },
        "history_kazakhstan": {
            "низкий": "Фрагментарные знания истории.",
            "средний": "База есть, ошибки в деталях.",
            "высокий": "Системные знания."
        },
        "profile": {
            "низкий": "Серьёзные пробелы в знаниях.",
            "средний": "Нужно уверенность в сложных задачах.",
            "высокий": "Хорошие знания."
        }
    }
    return rec.get(subject, rec["profile"])[level]

def get_group_recommendation(group, level):
    rec = {
        "general": {
            "низкий": "Нужна комплексная работа.",
            "средний": "Надо улучшать слабые места.",
            "высокий": "Хороший уровень подготовки."
        },
        "profile": {
            "низкий": "Нужен индивидуальный план.",
            "средний": "Нужна систематизация знаний.",
            "высокий": "Готов к поступлению."
        }
    }
    return rec[group][level]

def calculate_admission_probability(percentage):
    if percentage >= 85:
        return {"without_preparation": "85", "with_preparation": "95"}
    elif percentage >= 70:
        return {"without_preparation": "60", "with_preparation": "80"}
    elif percentage >= 50:
        return {"without_preparation": "25", "with_preparation": "65"}
    else:
        return {"without_preparation": "15", "with_preparation": "35%"}

from drf_spectacular.utils import extend_schema, OpenApiExample

@extend_schema(
    request=EntDiagnosisInputSerializer,
    
    examples=[
        OpenApiExample(
            name="Пример запроса",
            value={
                "name": "Али",
                "phone": "+998901234567",
                "history_kazakhstan": 33,
                "math_literacy": 30,
                "reading_literacy": 38,
                "profile_subject_1": {
                    "name": "Физика",
                    "score": 45
                },
                "profile_subject_2": {
                    "name": "Математика",
                    "score": 47
                }
            },
            request_only=True
        )
    ],
    description="Рассчитывает результаты диагностики по ЕНТ и возвращает анализ"
)
@api_view(['POST'])
def ent_diagnosis_analysis(request):
    serializer = EntDiagnosisInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    total_score = (
        data['history_kazakhstan'] +
        data['math_literacy'] +
        data['reading_literacy'] +
        data['profile_subject_1']['score'] +
        data['profile_subject_2']['score']
    )
    max_score = 140
    percentage = (total_score / max_score) * 100

    # Levels
    reading_level = calculate_subject_level(data['reading_literacy'], 40)
    math_level = calculate_subject_level(data['math_literacy'], 40)
    history_level = calculate_subject_level(data['history_kazakhstan'], 40)
    profile1_level = calculate_subject_level(data['profile_subject_1']['score'], 50)
    profile2_level = calculate_subject_level(data['profile_subject_2']['score'], 50)

    general_level = calculate_group_level(
        [data['history_kazakhstan'], data['math_literacy'], data['reading_literacy']], [40, 40, 40]
    )
    profile_level = calculate_group_level(
        [data['profile_subject_1']['score'], data['profile_subject_2']['score']], [50, 50]
    )

    response_data = {
        "name": data['name'],
        "phone": data['phone'],
        "total_score": total_score,
        "percentage": round(percentage, 2),
        "subject_analysis": {
            "reading_literacy": {
                "score": data['reading_literacy'],
                "level": reading_level,
                "recommendation": get_subject_recommendation("reading_literacy", reading_level)
            },
            "math_literacy": {
                "score": data['math_literacy'],
                "level": math_level,
                "recommendation": get_subject_recommendation("math_literacy", math_level)
            },
            "history_kazakhstan": {
                "score": data['history_kazakhstan'],
                "level": history_level,
                "recommendation": get_subject_recommendation("history_kazakhstan", history_level)
            },
            "profile_subject_1": {
                "name": data['profile_subject_1']['name'],
                "score": data['profile_subject_1']['score'],
                "level": profile1_level,
                "recommendation": get_subject_recommendation("profile", profile1_level)
            },
            "profile_subject_2": {
                "name": data['profile_subject_2']['name'],
                "score": data['profile_subject_2']['score'],
                "level": profile2_level,
                "recommendation": get_subject_recommendation("profile", profile2_level)
            }
        },
        "group_analysis": {
            "general_subjects": {
                "level": general_level,
                "recommendation": get_group_recommendation("general", general_level)
            },
            "profile_subjects": {
                "level": profile_level,
                "recommendation": get_group_recommendation("profile", profile_level)
            }
        },
        "admission_probability": calculate_admission_probability(percentage)
    }

    return Response(response_data, status=status.HTTP_200_OK)