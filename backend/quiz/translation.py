from modeltranslation.translator import translator, TranslationOptions
from .models import  Category, SubCategory, Question, Answer



class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

class SubCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)

class QuestionTranslationOptions(TranslationOptions):
    fields = ('text',)

class AnwerTranslationOptions(TranslationOptions):
    fields = ("text", )

translator.register(Category, CategoryTranslationOptions)
translator.register(SubCategory, SubCategoryTranslationOptions)
translator.register(Question, QuestionTranslationOptions)
translator.register(Answer, AnwerTranslationOptions)
