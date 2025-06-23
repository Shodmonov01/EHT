# serializers.py

from rest_framework import serializers
from .models import  Question, Answer, Category, QuizResult, SubCategory, CategorySet
from django.utils.translation import get_language

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
    image = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = ['id', 'text', 'image', 'is_correct']
    
    def get_image(self, obj):
        request = self.context.get('request')
        lang = get_language()
        
        if lang == 'kz' and obj.image_kz:
            return request.build_absolute_uri(obj.image_kz.url) if request else obj.image_kz.url
        elif lang == 'ru' and obj.image_ru:
            return request.build_absolute_uri(obj.image_ru.url) if request else obj.image_ru.url
        return None


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True, source='answer_set')
    category_name = serializers.CharField(source='theme.category.name', read_only=True)
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'image', 'theme', 'category_name', 'answers', 'correct_answers_count']
    
    def get_image(self, obj):
        request = self.context.get('request')
        lang = get_language()
        
        if lang == 'kz' and obj.image_kz:
            return request.build_absolute_uri(obj.image_kz.url) if request else obj.image_kz.url
        elif lang == 'ru' and obj.image_ru:
            return request.build_absolute_uri(obj.image_ru.url) if request else obj.image_ru.url
        return None


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
        fields = ['id', 'name', 'type', 'subject_type']


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
    correct_answers_count = serializers.IntegerField()
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'image', 'category', 'subcategory', 'correct_answers_count', 'answers']
    
    # class Meta:
    #     model = Question
    #     fields = ['id', 'text', 'image', 'category', 'subcategory']
    
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
    user_token = serializers.UUIDField(required=False)
    
    class Meta:
        model = QuizResult
        fields = ['id', 'answer_ids', 'unanswered_question_ids', "user_token"]
    
    def create(self, validated_data):
        answer_ids = validated_data.pop('answer_ids', [])
        unanswered_question_ids = validated_data.pop('unanswered_question_ids', [])
        
        # If no user_token provided, one will be generated by the model's default
        quiz_result = QuizResult.objects.create(**validated_data)
        
        if answer_ids:
            answers = Answer.objects.filter(id__in=answer_ids)
            quiz_result.answers.add(*answers)
        
        if unanswered_question_ids:
            unanswered_questions = Question.objects.filter(id__in=unanswered_question_ids)
            quiz_result.unanswered_questions.add(*unanswered_questions)
        
        return quiz_result
    

class QuizResultCreateSerializer(serializers.ModelSerializer):
    answer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )
    unanswered_question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )
    user_token = serializers.UUIDField(required=True)

    class Meta:
        model = QuizResult

        fields = ['id', 'user_token', 'answer_ids', 'unanswered_question_ids']
    
    def create(self, validated_data):
        answer_ids = validated_data.pop('answer_ids', [])
        unanswered_question_ids = validated_data.pop('unanswered_question_ids', [])
        
        # If no user_token provided, one will be generated by the model's default
        quiz_result = QuizResult.objects.create(**validated_data)
        
        if answer_ids:
            answers = Answer.objects.filter(id__in=answer_ids)
            quiz_result.answers.add(*answers)
        
        if unanswered_question_ids:
            unanswered_questions = Question.objects.filter(id__in=unanswered_question_ids)
            quiz_result.unanswered_questions.add(*unanswered_questions)
        
        return quiz_result


class QuizResultDetailSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    correct_answers = serializers.SerializerMethodField()
    category_stats = serializers.SerializerMethodField()
    
    
    class Meta:
        model = QuizResult
        fields = ['id', 'user_token', 
                  'score', 'total_questions', 'correct_answers', 'category_stats', 
                  'created_at']
    
    def get_total_questions(self, obj):
        if not obj.quiz or not obj.quiz.category_set:
            return 0
        # Get questions through: Quiz → CategorySet → Categories → SubCategories → Questions
        return Question.objects.filter(
            theme__category__in=obj.quiz.category_set.categories.all()
        ).count()
    
    def get_correct_answers(self, obj):
        return obj.answers.filter(is_correct=True).count()
    
    def get_score(self, obj):
        total = self.get_total_questions(obj)
        correct = self.get_correct_answers(obj)
        return round((correct / total) * 100, 2) if total > 0 else 0
    
    def get_category_stats(self, obj):
        if not obj.quiz or not obj.quiz.category_set:
            return []
            
        result = []
        categories = obj.quiz.category_set.categories.all()
        
        for category in categories:
            cat_data = {
                'category': category.name,
                'subcategories': []
            }
            
            subcategories = SubCategory.objects.filter(
                category=category
            )
            
            for subcategory in subcategories:
                questions = Question.objects.filter(
                    theme=subcategory
                )
                total = questions.count()
                correct = obj.answers.filter(
                    question__in=questions,
                    is_correct=True
                ).count()
                
                subcat_data = {
                    'subcategory': subcategory.name,
                    'total_questions': total,
                    'correct_questions': correct,
                    'incorrect_questions': total - correct,
                    'percentage': round((correct / total) * 100, 2) if total > 0 else 0
                }
                cat_data['subcategories'].append(subcat_data)
            
            result.append(cat_data)
        
        return result
    

#############################################
from rest_framework import serializers
from .models import QuizResult, Quiz, Category, Specialization


class SubjectScoreSerializer(serializers.Serializer):
    """Serializer for individual subject score input"""
    category_id = serializers.IntegerField()
    points = serializers.IntegerField(min_value=0)
    
    def validate_category_id(self, value):
        """Validate that category exists"""
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category does not exist")
        return value
    
    def validate(self, data):
        """Validate points based on category type"""
        try:
            category = Category.objects.get(id=data['category_id'])
            max_points = 40 if category.subject_type == 'PROFILE' else 20
            
            if data['points'] > max_points:
                raise serializers.ValidationError(
                    f"Points for {category.name} cannot exceed {max_points}"
                )
        except Category.DoesNotExist:
            raise serializers.ValidationError("Category does not exist")
        
        return data


class DiagnosticInputSerializer(serializers.Serializer):
    """Serializer for manual diagnostic input"""
    name = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=20)
    subject_scores = SubjectScoreSerializer(many=True)
    
    def validate_subject_scores(self, value):
        """Validate subject scores structure"""
        if len(value) == 0:
            raise serializers.ValidationError("At least one subject score is required")
        
        # Check for duplicate categories
        category_ids = [score['category_id'] for score in value]
        if len(category_ids) != len(set(category_ids)):
            raise serializers.ValidationError("Duplicate categories are not allowed")
        
        # Validate total points don't exceed 140
        total_points = sum(score['points'] for score in value)
        if total_points > 140:
            raise serializers.ValidationError("Total points cannot exceed 140")
        
        return value


class SubjectEvaluationSerializer(serializers.Serializer):
    """Serializer for individual subject evaluation"""
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    category_type = serializers.CharField()
    subject_type = serializers.CharField()
    points = serializers.IntegerField()
    max_points = serializers.IntegerField()
    percentage = serializers.FloatField()
    level = serializers.CharField()


class GroupEvaluationSerializer(serializers.Serializer):
    """Serializer for subject group evaluation"""
    group_name = serializers.CharField()
    group_type = serializers.CharField()  # MAIN or PROFILE
    total_points = serializers.IntegerField()
    max_points = serializers.IntegerField()
    percentage = serializers.FloatField()
    level = serializers.CharField()
    subjects_count = serializers.IntegerField()


class AdmissionProbabilitySerializer(serializers.Serializer):
    """Serializer for admission probability"""
    without_preparation = serializers.FloatField()
    with_preparation = serializers.FloatField()
    specializations = serializers.ListField(child=serializers.CharField(), required=False)


class DiagnosticResultSerializer(serializers.Serializer):
    """Serializer for diagnostic results"""
    user_token = serializers.UUIDField()
    name = serializers.CharField()
    phone_number = serializers.CharField()
    
    total_points = serializers.IntegerField()
    total_possible_points = serializers.IntegerField()
    total_percentage = serializers.FloatField()
    
    subject_evaluations = SubjectEvaluationSerializer(many=True)
    group_evaluations = GroupEvaluationSerializer(many=True)
    
    recommendations = serializers.CharField()
    admission_probability = AdmissionProbabilitySerializer()
    
    created_at = serializers.DateTimeField()

