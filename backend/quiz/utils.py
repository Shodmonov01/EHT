import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from django.conf import settings
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import  Question 


def get_google_sheet():
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds_path = os.path.join(settings.BASE_DIR, 'config', 'keys', 'credentials.json')
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            client = gspread.authorize(creds)

            # Откройте Google Sheet по URL
            sheet_url = "https://docs.google.com/spreadsheets/d/1FfooaDunqiVekiudUbfXE9AglxAPsOhvnfQuhERr2Lo/"
            sheet = client.open_by_url(sheet_url).sheet1

            return sheet

def save_to_google_sheet(user_token, score, result_url):
    sheet = get_google_sheet()

    try:
        cell = sheet.find(str(user_token))
        row_num = cell.row
        sheet.update_cell(row_num, 8, score)
        sheet.update_cell(row_num, 7, result_url)
    except Exception:
        # Add new row
        sheet.append_row([
            str(user_token),
   
            score,
            result_url
        ])
    
    return True


from django.core.files.base import ContentFile
from django.db import transaction

def generate_and_save_pdfs(quiz_result, request):
    """
    Generate both PDF types and save them to storage
    Returns tuple of (result_pdf_path, diagnostic_pdf_path)
    """
    with transaction.atomic():
        # Generate and save Result PDF
        result_pdf_content = generate_result_pdf_content(quiz_result, request)
        result_filename = f"result_{quiz_result.id}.pdf"
        quiz_result.result_pdf.save(
            result_filename, 
            ContentFile(result_pdf_content), 
            save=False
        )
        
        # Generate and save Diagnostic PDF
        diagnostic_pdf_content = generate_diagnostic_pdf_content(quiz_result, request)
        diagnostic_filename = f"diagnostic_{quiz_result.id}.pdf"
        quiz_result.diagnostic_pdf.save(
            diagnostic_filename, 
            ContentFile(diagnostic_pdf_content), 
            save=False
        )
        
        quiz_result.save()
    
    return quiz_result.result_pdf.url, quiz_result.diagnostic_pdf.url


def generate_result_pdf_content(quiz_result, request):
    """Generate content for the standard result PDF"""
    context = get_base_context(quiz_result)
    context.update({
        'template_name': 'quiz_result_pdf.html',
        # Add any result-specific context here
    })
    return render_pdf(context)

def generate_diagnostic_pdf_content(quiz_result, request):
    """Generate content for the diagnostic PDF"""
    context = get_base_context(quiz_result)
    context.update({
        'template_name': 'quiz_diagnostic_pdf.html',
        # Add diagnostic-specific context here
        # 'conclusion': get_diagnostic_conclusion(quiz_result),
        # 'recommendations': get_recommendations(quiz_result),
    })
    return render_pdf(context)

def get_base_context(quiz_result):
    """Shared context for both PDF types"""
    questions = Question.objects.filter(
        theme__category__category_sets=quiz_result.quiz.category_set
    )
    total_questions = questions.count()
    correct_answers = quiz_result.answers.filter(is_correct=True).count()
    
    return {
        'quiz_result': quiz_result,
        'correct_questions': correct_answers,
        'total_questions': total_questions,
        'percentage_score': round(
            (correct_answers / total_questions * 100) if total_questions > 0 else 0, 
            1
        ),
        # Add other shared context data
    }

def render_pdf(context):
    """Generic PDF rendering function"""
    template = get_template(context['template_name'])
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    return result.getvalue() if not pdf.err else None


# def generate_and_store_pdfs(quiz_result, request):
#     """
#     Generate and store both PDFs during quiz submission
#     """
#     with transaction.atomic():
#         # Generate PDF content
#         result_content = generate_summary_pdf_content(quiz_result, request)
#         table_content = generate_table_pdf_content(quiz_result, request)
        
#         # Save to model fields
#         quiz_result.result_pdf.save(
#             f"result_{quiz_result.id}.pdf", 
#             ContentFile(result_content),
#             save=False
#         )
#         quiz_result.diagnostic_pdf.save(
#             f"diagnostic_{quiz_result.id}.pdf",
#             ContentFile(table_content),
#             save=False
#         )
#         quiz_result.save()
        