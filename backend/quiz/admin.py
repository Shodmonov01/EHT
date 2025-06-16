from django.contrib import admin
from .models import (
    Category, Question, Answer, SubCategory,
    QuizResult, CategorySet, Quiz, Specialization
)
from nested_inline.admin import NestedStackedInline
import nested_admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.translator import translator, TranslationOptions




# --- Inline for Answers ---
class AnswerInline(nested_admin.NestedStackedInline):
    model = Answer
    extra = 1
    fk_name = 'question'

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        trans_opts = translator.get_options_for_model(self.model)
        for field in trans_opts.fields:
            if field in formset.form.base_fields:
                formset.form.base_fields.pop(field)
        return formset

# --- Admin for Questions ---
class QuestionAdmin(nested_admin.NestedModelAdmin):
    ordering = ['theme__category__name', 'theme__name', 'text']
    search_fields = ['text']
    list_per_page = 50
    list_display = ['text', "category__name", "correct_answers_count", 'get_category_sets']
    raw_id_fields = ['theme']
    inlines = [AnswerInline]

    @admin.display(description=_("Category Sets"))
    def get_category_sets(self, obj):
        return ", ".join(cs.name for cs in obj.theme.category.category_sets.all())
    

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        trans_opts = translator.get_options_for_model(self.model)
        for field in trans_opts.fields:
            form.base_fields.pop(field, None)
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.save()
        formset.save_m2m()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        question = form.instance
        correct_answers = question.answer_set.filter(is_correct=True).count()
        if correct_answers != question.correct_answers_count:
            from django.contrib import messages
            messages.warning(
                request,
                _('Number of correct answers (%(correct)s) does not match specified count (%(count)s). '
                  'The count has been automatically adjusted.') % {
                    'correct': correct_answers,
                    'count': question.correct_answers_count
                }
            )
            question.correct_answers_count = correct_answers
            question.save(update_fields=['correct_answers_count'])

# --- Admin for SubCategory ---
class SubCategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']
    ordering = ['category__name', 'name']
    list_display = ['name', 'category']
    list_per_page = 50

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        trans_opts = translator.get_options_for_model(self.model)
        for field in trans_opts.fields:
            form.base_fields.pop(field, None)
        return form

# --- Admin for CategorySet ---
@admin.register(CategorySet)
class CategorySetAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_list')
    filter_horizontal = ('categories',)

    def category_list(self, obj):
        return " + ".join(category.name for category in obj.categories.all())

# --- Admin for Category ---
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'subject_type']
    search_fields = ['name']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        trans_opts = translator.get_options_for_model(self.model)
        for field in trans_opts.fields:
            form.base_fields.pop(field, None)
        return form

# --- Admin for Answer ---
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'is_correct']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        trans_opts = translator.get_options_for_model(self.model)
        for field in trans_opts.fields:
            form.base_fields.pop(field, None)
        return form
    
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(Quiz)
admin.site.register(Specialization)
# admin.site.register(QuizResult)  # Uncomment if needed
