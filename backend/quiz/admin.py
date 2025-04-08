from django.contrib import admin
from .models import Category, Question, Answer, SubCategory, QuizResult,\
                        CategorySet, Quiz
from nested_inline.admin import NestedStackedInline, NestedModelAdmin
import nested_admin
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

class AnswerInline(nested_admin.NestedStackedInline):
    model = Answer
    extra = 1
    fk_name = 'question'


class QuestionAdmin(nested_admin.NestedModelAdmin):
   
    
    ordering = [ 'theme__category__name', 'theme__name', 'text']
    search_fields = ['text',]
    list_per_page = 50
    list_display = ['text']
    raw_id_fields = ['theme']
    inlines = [AnswerInline]

    def save_model(self, request, obj, form, change):
        # Save the model without validation
        super().save_model(request, obj, form, change)
    
    def save_related(self, request, form, formsets, change):
        # Save all related objects first
        super().save_related(request, form, formsets, change)
        
        # Now check the question against its answers
        question = form.instance
        correct_answers = question.answer_set.filter(is_correct=True).count()
        
        if correct_answers != question.correct_answers_count:
            from django.contrib import messages
            messages.warning(
                request, 
                _('Question saved, but number of correct answers (%(correct)s) does not match specified count (%(count)s)') % {
                    'correct': correct_answers,
                    'count': question.correct_answers_count
                }
            )
            
            # Optional: Auto-adjust the count to match reality
            question.correct_answers_count = correct_answers
            question.save(update_fields=['correct_answers_count'])

class SubCategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']
    ordering = ['category__name', 'name']
    list_display = ['name','category']
    list_per_page = 50


@admin.register(CategorySet)
class CategorySetAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_list')
    filter_horizontal = ('categories',)

    def category_list(self, obj):
        return " + ".join(category.name for category in obj.categories.all())


admin.site.register(Category)
# admin.site.register(QuizResult)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Question, QuestionAdmin)

admin.site.register(Quiz)