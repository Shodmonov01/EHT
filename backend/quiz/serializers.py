# serializers.py

from rest_framework import serializers
from .models import  Question, Answer, Category, QuizResult, SubCategory, CategorySet


class UserQuizStarteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length = 64)
    parents_fullname = serializers.CharField(max_length=128)
    phone_number = serializers.CharField(max_length=32)
    category_set_id = serializers.PrimaryKeyRelatedField(
        queryset=CategorySet.objects.all(),
        write_only=True
    )
    formatted_categories = serializers.SerializerMethodField()  # Add this field
    is_agreed = serializers.BooleanField()
    category_set_id_value = serializers.SerializerMethodField()
    
    def get_category_set_id_value(self, obj):
        return obj['category_set_id'].id 

    def get_formatted_categories(self, obj):
        print(obj, 'this is obj')
        # Get the CategorySet object from the validated data
        category_set = obj['category_set_id']
        
        # Access the related categories through the relationship
        return " + ".join(category_set.categories.values_list("name", flat=True))
    
class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'image', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    # Include related answers; note that in your models, Question has a related_name "questions" on Quiz.
    answers = AnswerSerializer(many=True, read_only=True, source='answer_set')
    # You can add a field for the category name
    category_name = serializers.CharField(source='theme.category.name', read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'image', 'quiz', 'theme', 'category_name', 'answers']

# class QuizSerializer(serializers.ModelSerializer):
#     # Nest questions if needed. (Make sure your Quiz model has a related_name for questions, e.g. 'questions'.)
#     questions = QuestionSerializer(many=True, read_only=True)
    
#     class Meta:
#         model = Quiz
#         fields = ['id', 'title', 'subtitle', 'questions']


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'type']


class CategorySetHomeSerializer(serializers.ModelSerializer):
    formatted_categories = serializers.SerializerMethodField()

    def get_formatted_categories(self, obj):

        return " + ".join(obj.categories.values_list("name", flat=True))

    class Meta:
        model = CategorySet
        fields = ['id', 'name', 'formatted_categories']




#####################33
from rest_framework import serializers
from .models import Category, CategorySet, SubCategory,  Question, Answer, QuizResult



class CategorySetSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = CategorySet
        fields = ['id', 'name', 'categories']

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'image']
        # Note: we exclude is_correct to prevent sending correct answers to client

class QuestionSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'image', 'category', 'subcategory']
    
    def get_category(self, obj):
        return obj.theme.category.name if obj.theme and obj.theme.category else None
    
    def get_subcategory(self, obj):
        return obj.theme.name if obj.theme else None

class QuestionWithAnswersSerializer(QuestionSerializer):
    answers = AnswerSerializer(source='answer_set', many=True, read_only=True)
    
    class Meta(QuestionSerializer.Meta):
        fields = QuestionSerializer.Meta.fields + ['answers']


class QuizResultCreateSerializer(serializers.ModelSerializer):
    answer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    unanswered_question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = QuizResult
        fields = ['id', 'phone_number', 'name', 'parent_name', 'answer_ids', 'unanswered_question_ids']
    
    def create(self, validated_data):
        answer_ids = validated_data.pop('answer_ids', [])
        unanswered_question_ids = validated_data.pop('unanswered_question_ids', [])
        
        quiz_result = QuizResult.objects.create(**validated_data)
        
        if answer_ids:
            answers = Answer.objects.filter(id__in=answer_ids)
            quiz_result.answers.add(*answers)
        
        if unanswered_question_ids:
            unanswered_questions = Question.objects.filter(id__in=unanswered_question_ids)
            quiz_result.unanswered_questions.add(*unanswered_questions)
        
        return quiz_result

class QuizResultDetailSerializer(serializers.ModelSerializer):
    quiz_title = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    correct_answers = serializers.SerializerMethodField()
    
    class Meta:
        model = QuizResult
        fields = ['id', 'name', 'parent_name',  'phone_number', 'quiz', 'quiz_title', 
                  'score', 'total_questions', 'correct_answers', 'created_at']
    
    def get_quiz_title(self, obj):
        return obj.quiz.title if obj.quiz else None
    
    def get_total_questions(self, obj):
        return Question.objects.filter(quiz=obj.quiz).count()
    
    def get_correct_answers(self, obj):
        return obj.answers.filter(is_correct=True).count()
    
    def get_score(self, obj):
        total = self.get_total_questions(obj)
        correct = self.get_correct_answers(obj)
        return (correct / total * 100) if total > 0 else 0