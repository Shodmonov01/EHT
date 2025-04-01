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
           
            # quiz = Quiz.objects.create(user_token = unique_id, phone_number = final_data_to_save["phone_number"], category_set_id = category_set_id )


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
            # categories = Category.objects.filter(categoryset=category_set)

            questions = (
                    Question.objects.filter(category__in=category_set.categories.all())
                    .select_related("category", "theme", "theme__category")
                    .prefetch_related(
                        Prefetch(
                            "answer_set",
                            queryset=Answer.objects.filter(is_correct=False).only("id", "text", "image")
                        )
                    )
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
                answers = Answer.objects.filter(question=question).values("id", "text", "image")
                question_data = {
                    "id": question.id,
                    "text": question.text,
                    "category": question.theme.category.name,
                    "subcategory": question.theme.name,
                    "image": request.build_absolute_uri(question.image.url) if question.image and question.image.url else None,
                    "annwers" : answers
                }
                
                category_questions[category_id]["questions"].append(question_data)

            return Response(list(category_questions.values()), status=200)


from django.db.models import Count, Q


class QuizResultCreateAPIView(APIView):
    @extend_schema(
        request=QuizResultCreateSerializer,  # Specifies the request body schema
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
    def post(self, request, *args, **kwargs):
        serializer = QuizResultCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz_result = serializer.save()

        # Re-fetch the quiz_result with annotations
        quiz_result = QuizResult.objects.filter(pk=quiz_result.pk).annotate(
                total_questions=Count('quiz__category_set__categories__questions', distinct=True),
                correct_answers=Count('answers', filter=Q(answers__is_correct=True))
            ).first()

        # Use the annotated fields
        total_questions = quiz_result.total_questions
        correct_answers = quiz_result.correct_answers
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

        # Generate result URL
        result_url = f"/api/quiz-results/{quiz_result.id}/"
        pdf_url = f"/api/quiz-results/{quiz_result.id}/pdf/"
        print(quiz_result, 'this is quiz result--')

        # Generate PDF and save it (asynchronously if possible)
        # try:
        #     # You could use Celery for this in production to make it truly async
        #     generate_and_save_pdf(quiz_result, request)
        # except Exception as e:
        #     print(f"Error generating PDF: {e}")

        # Save to Google Sheet
        try:
            success = save_to_google_sheet(
                
                quiz_result.id, 

                score,
                result_url
            )
        except Exception as e:
            success = False
            print(f"Error saving to Google Sheet: {e}")

        response_data = {
            'result': QuizResultDetailSerializer(quiz_result, context={'request': request}).data,
            'score': score,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'result_url': result_url,
            'pdf_url': pdf_url,
            'google_sheet_saved': success
        }
        return Response(response_data, status=status.HTTP_201_CREATED)



class QuizResultPDFAPIView(APIView):
    """Serve PDF report for quiz results"""
    
    
    def get(self, request, pk, *args, **kwargs):
        try:
            quiz_result = QuizResult.objects.get(pk=pk)
        except QuizResult.DoesNotExist:
            return Response(
                {"error": "Quiz result not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if PDF already exists
        if quiz_result.pdf_file and os.path.exists(quiz_result.pdf_file.path):
            # Serve existing PDF
            response = FileResponse(
                open(quiz_result.pdf_file.path, 'rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="quiz_result_{quiz_result.id}.pdf"'
            return response
        
        # If PDF doesn't exist, generate it
        try:
            pdf_path = generate_and_save_pdf(quiz_result, request)
            if not pdf_path or not os.path.exists(pdf_path):
                return Response(
                    {"error": "Error generating PDF"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Serve the newly generated PDF
            response = FileResponse(
                open(pdf_path, 'rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="quiz_result_{quiz_result.id}.pdf"'
            return response
            
        except Exception as e:
            return Response(
                {"error": f"Error generating PDF: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


