# serializers.py

from rest_framework import serializers
from .models import Quiz, Question, Answer, Category, QuizResult, SubCategory, CategorySet


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

class QuizSerializer(serializers.ModelSerializer):
    # Nest questions if needed. (Make sure your Quiz model has a related_name for questions, e.g. 'questions'.)
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = ['id', 'language', 'title', 'subtitle', 'grade', 'questions']

class QuizResultSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    unanswered_questions = QuestionSerializer(many=True, read_only=True)
    quiz = QuizSerializer(read_only=True)
    
    class Meta:
        model = QuizResult
        fields = [
            'id', 'phone_number', 'name', 'parent_name', 'grade',
            'quiz', 'answers', 'unanswered_questions', 'created_at'
        ]

class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'type']

class CategorySetSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = CategorySet
        fields = ['id', 'name', 'categories']

class CategorySetHomeSerializer(serializers.ModelSerializer):
    formatted_categories = serializers.SerializerMethodField()

    def get_formatted_categories(self, obj):

        return " + ".join(obj.categories.values_list("name", flat=True))

    class Meta:
        model = CategorySet
        fields = ['id', 'name', 'formatted_categories']