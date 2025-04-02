from django.db import models
import uuid
    
CATEGORY_TYPE = (
    ('EXC', 'Exact'),
    ('NTR', 'Natural')
)


class Category(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=8, choices=CATEGORY_TYPE)

    def __str__(self):
        return self.name

class CategorySet(models.Model):
    name = models.CharField(max_length=255, unique=True)  
    categories = models.ManyToManyField(Category, related_name='category_sets')  

    def __str__(self):
        return self.name
    

class SubCategory(models.Model):
    name = models.TextField(null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Quiz(models.Model):
    user_token = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=20)
    category_set = models.OneToOneField(CategorySet, on_delete=models.CASCADE)

    def __str__(self):
        return self.phone_number

class Question(models.Model):
    text = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='questions')
    theme = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    
    def quiz_title(self):
        return self.category.name

    def category_name(self):
        return self.theme.category.name

    def __str__(self):
        return self.text

class Answer(models.Model):
    text = models.TextField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


def quiz_result_pdf_path(instance, filename):
    """Generate path for storing quiz result PDFs"""
    return f'quiz_results/user_{instance.user_token}/{filename}'


class QuizResult(models.Model):
    user_token = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE, related_name='results', null=True, blank=True)
    answers = models.ManyToManyField('Answer', blank=True)
    unanswered_questions = models.ManyToManyField('Question', blank=True, related_name='unanswered_by')
    created_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to=quiz_result_pdf_path, blank=True, null=True)
    
    # def __str__(self):
    #     return f"{self.name}'s result for"
    
    def get_pdf_url(self):
        if self.pdf_file:
            return self.pdf_file.url
        return None

