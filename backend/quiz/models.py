from django.db import models

    
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

class QuizResult(models.Model):
    phone_number = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    parent_name = models.CharField(max_length=100)  # Добавьте это поле
    answers = models.ManyToManyField(Answer)
    unanswered_questions = models.ManyToManyField(Question, related_name='unaswered_questions',  blank=True, null=True)

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)


    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}'s Quiz Result"
    

