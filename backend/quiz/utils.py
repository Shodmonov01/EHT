import gspread
from drf_spectacular.utils import extend_schema, OpenApiParameter
from oauth2client.service_account import ServiceAccountCredentials
import os
from django.conf import settings
from .models import Category, SubCategory
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import QuizResult, Category, SubCategory, Question 


def get_google_sheet():
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds_path = os.path.join(settings.BASE_DIR, 'config', 'keys', 'credentials.json')
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            client = gspread.authorize(creds)

            # Откройте Google Sheet по URL
            sheet_url = "https://docs.google.com/spreadsheets/d/1FfooaDunqiVekiudUbfXE9AglxAPsOhvnfQuhERr2Lo/"
            sheet = client.open_by_url(sheet_url).sheet1

            return sheet

def save_to_google_sheet(user_token, quiz_result_id, score, result_url):
    sheet = get_google_sheet()
    
    # Check if user_token already exists in the sheet
    try:
        cell = sheet.find(str(user_token))
        row_num = cell.row
   
             
        # Update existing row
        sheet.update_cell(row_num, 2, quiz_result_id)
       
        sheet.update_cell(row_num, 6, score)
        sheet.update_cell(row_num, 7, result_url)
    except gspread.exceptions.CellNotFound:
        # Add new row
        sheet.append_row([
            str(user_token),
            quiz_result_id,
   
            score,
            result_url
        ])
    
    return True


from django.core.files.base import ContentFile
from django.db import transaction

def generate_and_save_pdf(quiz_result, request):
    """
    Generate PDF for quiz result and save it to storage
    Returns the PDF file path
    """
    # Generate the PDF
    pdf_content = generate_pdf_content(quiz_result, request)
    if not pdf_content:
        return None
    
    # Save PDF to model's FileField
    filename = f"quiz_result_{quiz_result.id}.pdf"
    
    with transaction.atomic():
        # Save to FileField
        quiz_result.pdf_file.save(filename, ContentFile(pdf_content), save=True)
    
    return quiz_result.pdf_file.path

def generate_pdf_content(quiz_result, request):
    """Generate PDF content without saving"""
    # Get all questions through the category set relationships
    questions = Question.objects.filter(
        theme__category__category_sets=quiz_result.quiz.category_set
    )
    
    total_questions = questions.count()
    correct_answers = quiz_result.answers.filter(is_correct=True).count()
    
    # Prepare context data for the template
    context = {
        'correct_questions': correct_answers,
        'total_questions': total_questions,
        'passed_date': quiz_result.created_at.strftime('%d.%m.%Y'),
        'percentage_score': round(
            (correct_answers / total_questions * 100) if total_questions > 0 else 0, 
            1
        ),
        'quiz_name': quiz_result.quiz.category_set.name if quiz_result.quiz.category_set else "Quiz",
    }
    
    # Process category stats
    categories = Category.objects.filter(
        category_sets=quiz_result.quiz.category_set
    ).distinct()
    
    category_stats = []
    
    for category in categories:
        cat_data = {
            'category': category.name,
            'subcategories': []
        }
        
        subcategories = SubCategory.objects.filter(
            category=category
        ).distinct()
        
        for subcategory in subcategories:
            subcat_questions = questions.filter(theme=subcategory)
            total = subcat_questions.count()
            correct = quiz_result.answers.filter(
                question__in=subcat_questions,
                is_correct=True
            ).count()
            
            subcat_data = {
                'subcategory': subcategory.name,
                'total_questions': total,
                'correct_questions': correct,
                'incorrect_questions': total - correct,
                'percentage': round((correct / total * 100) if total > 0 else 0, 1)
            }
            cat_data['subcategories'].append(subcat_data)
        
        category_stats.append(cat_data)
    
    context['category_stats'] = category_stats
    
    # Render template to string
    template = get_template('quiz_result_pdf.html')
    html = template.render(context)
    
    # Create PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        return result.getvalue()
    return None