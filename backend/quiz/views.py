from collections import defaultdict
from django.shortcuts import get_object_or_404
from django.utils import translation
from django.http import HttpResponse, FileResponse

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
from .utils import get_google_sheet, save_to_google_sheet, generate_pdf_content, generate_and_save_pdf

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

from django.db import transaction
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import QuizResult, Quiz, Answer, Question
from .serializers import QuizResultCreateSerializer, QuizResultDetailSerializer




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
            google_sheet = get_google_sheet()
            unique_id = str(uuid.uuid4())
            final_data_to_save = serializer.data
            print(final_data_to_save, 'final')
            category_set_id = serializer.data['category_set_id_value']
           
            quiz = Quiz.objects.create(user_token = unique_id, phone_number = final_data_to_save["phone_number"], category_set_id = category_set_id )


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
    

from django.db.models import Count, Q


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

        try:
            # You could use Celery for this in production to make it truly async
            pdf_path = generate_and_save_pdf(quiz_result, request)
        except Exception as e:
            print(f"Error generating PDF: {e}")
        
        if not pdf_path:
            # PDF generation failed, but we still return the result
            # You might want to log this error
            pass
        
        

        
        total_questions = quiz_result.total_questions or 0
        correct_answers = quiz_result.correct_answers or 0
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Step 6: Prepare response data
        response_data = {
            'result': QuizResultDetailSerializer(
                quiz_result,
                context={'request': request}
            ).data,
            'score': round(score, 2),
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'result_url': request.build_absolute_uri(
                f"/api/quiz-results/{quiz_result.id}/"
            ),
            'pdf_url': request.build_absolute_uri(
                f"/api/quiz-results/{quiz_result.id}/pdf/"
            ),
        }

        # Generate result URL
        result_url = f"/api/quiz-results/{quiz_result.id}/"
        pdf_url = f"/api/quiz-results/{quiz_result.id}/pdf/"
        print(quiz_result, 'this is quiz result--')

        # Generate PDF and save it (asynchronously if possible)
        print(serializer.validated_data, 'data validated')
        print(serializer.data, 'data')
        

        # # Save to Google Sheet
        # try:
        #     success = save_to_google_sheet(
        #         serializer.validated_data['user_token'],
        #         quiz_result.id, 
            
                

        #         score,
        #         result_url
        #     )
        # except Exception as e:
        #     success = False
        #     print(f"Error saving to Google Sheet: {e}")

        
        # Step 7: Async tasks (commented out as examples)
        # - PDF generation
        # generate_pdf_content(quiz_result.id)
        
        # - Google Sheets integration

        
        return Response({"message":"Thank you"}, status=status.HTTP_201_CREATED)



# class QuizResultCreateAPIView(APIView):
#     @extend_schema(
#         request=QuizResultCreateSerializer,  # Specifies the request body schema
#         description="Create a new quiz",
#         parameters=[
#             OpenApiParameter(
#                 name="Accept-Language",
#                 type=str,
#                 location=OpenApiParameter.HEADER,
#                 description="Select response language (ru, kz)",
#                 required=False,
#                 enum=["ru", "kz",],
#             )
#         ]
#     )
#     def post(self, request, *args, **kwargs):
#         serializer = QuizResultCreateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         quiz_result = serializer.save()

#         # Re-fetch the quiz_result with annotations
#         quiz_result = QuizResult.objects.filter(pk=quiz_result.pk).annotate(
#                 total_questions=Count('quiz__category_set__categories__questions', distinct=True),
#                 correct_answers=Count('answers', filter=Q(answers__is_correct=True))
#             ).first()

#         # Use the annotated fields
#         total_questions = quiz_result.total_questions
#         correct_answers = quiz_result.correct_answers
#         score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

#         # Generate result URL
#         result_url = f"/api/quiz-results/{quiz_result.id}/"
#         pdf_url = f"/api/quiz-results/{quiz_result.id}/pdf/"
#         print(quiz_result, 'this is quiz result--')

#         # Generate PDF and save it (asynchronously if possible)
#         # try:
#         #     # You could use Celery for this in production to make it truly async
#         #     generate_and_save_pdf(quiz_result, request)
#         # except Exception as e:
#         #     print(f"Error generating PDF: {e}")

#         # Save to Google Sheet
#         try:
#             success = save_to_google_sheet(
                
#                 quiz_result.id, 

#                 score,
#                 result_url
#             )
#         except Exception as e:
#             success = False
#             print(f"Error saving to Google Sheet: {e}")

#         response_data = {
#             'result': QuizResultDetailSerializer(quiz_result, context={'request': request}).data,
#             'score': score,
#             'total_questions': total_questions,
#             'correct_answers': correct_answers,
#             'result_url': result_url,
#             'pdf_url': pdf_url,
#             'google_sheet_saved': success
#         }
#         return Response(response_data, status=status.HTTP_201_CREATED)



class QuizResultPDFAPIView(APIView):
    """
    API endpoint to view/download generated PDF results
    """
    def get(self, request, pk):
        quiz_result = get_object_or_404(QuizResult, pk=pk)
        
        # Check if PDF already exists
        if quiz_result.pdf_file and os.path.exists(quiz_result.pdf_file.path):
            return FileResponse(
                open(quiz_result.pdf_file.path, 'rb'),
                content_type='application/pdf',
                as_attachment=True,
                filename=f'quiz_result_{pk}.pdf'
            )
        
        # Generate new PDF if it doesn't exist
        pdf_path = generate_and_save_pdf(quiz_result, request)
        
        if not pdf_path or not os.path.exists(pdf_path):
            return Response(
                {"error": "Failed to generate PDF report"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return FileResponse(
            open(pdf_path, 'rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f'quiz_result_{pk}.pdf'
        )



