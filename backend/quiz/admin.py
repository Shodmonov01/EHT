from django.contrib import admin
from .models import Category, Question, Answer, SubCategory, QuizResult,\
                        CategorySet
from nested_inline.admin import NestedStackedInline, NestedModelAdmin
import nested_admin



class AnswerInline(nested_admin.NestedStackedInline):
    model = Answer
    extra = 1
    fk_name = 'question'


class QuestionAdmin(nested_admin.NestedModelAdmin):
    
    ordering = ['quiz__id', 'theme__category__name', 'theme__name', 'text']
    search_fields = ['text',]
    list_per_page = 50
    list_display = ['text', 'quiz_title', 'category_name']
    raw_id_fields = ['theme']
    inlines = [AnswerInline]


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
admin.site.register(QuizResult)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)
