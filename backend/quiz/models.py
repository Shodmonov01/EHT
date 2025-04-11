from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _  # Import translation function
from django.core.exceptions import ValidationError


CATEGORY_TYPE = (
    ('EXC', _('Exact')),
    ('NTR', _('Natural'))
)


class Category(models.Model):
    name = models.CharField(_("Category Name"), max_length=255)
    type = models.CharField(_("Type"), max_length=8, choices=CATEGORY_TYPE)

    class Meta:
        verbose_name = _("Category")  # Singular name
        verbose_name_plural = _("Categories")  # Plural name

    def __str__(self):
        return self.name


class CategorySet(models.Model):
    name = models.CharField(_("Category Set Name"), max_length=255, unique=True)
    categories = models.ManyToManyField(Category, related_name='category_sets', verbose_name=_("Categories"))

    class Meta:
        verbose_name = _("Category Set")
        verbose_name_plural = _("Category Sets")

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    name = models.TextField(_("Name"), null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_("Category"))

    class Meta:
        verbose_name = _("Subcategory")
        verbose_name_plural = _("Subcategories")

    def __str__(self):
        return self.name or "Subcategory"


class Quiz(models.Model):
    user_token = models.CharField(_("User Token"), max_length=128)
    name = models.CharField(_("Name"), max_length=255)
    parent_name = models.CharField(_("Parent Name"), max_length=255, blank=True, null=True)
    phone_number = models.CharField(_("Phone Number"), max_length=20)
    category_set = models.ForeignKey(CategorySet, on_delete=models.CASCADE, verbose_name=_("Category Set"))

    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

    def __str__(self):
        return self.name


class Question(models.Model):
    text = models.TextField(_("Question Text"))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='questions', verbose_name=_("Category"))
    theme = models.ForeignKey(SubCategory, on_delete=models.CASCADE, verbose_name=_("Theme"))
    image = models.ImageField(_("Image"), upload_to='images/questions', null=True, blank=True)

    CORRECT_ANSWERS_CHOICES = (
        (1, _('1 correct answer')),
        (2, _('2 correct answers')),
        (3, _('3 correct answers')),
    )
    correct_answers_count = models.PositiveSmallIntegerField(
        _("Correct Answers Count"),
        choices=CORRECT_ANSWERS_CHOICES,
        default=1,
        
    )

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")

    def __str__(self):
        return self.text
    
    def clean(self):
        # Remove the validation entirely from the model's clean method
        # The validation will be handled in the admin
        super().clean()
        
        # No validation here anymore



class Answer(models.Model):
    text = models.TextField(_("Answer Text"))
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name=_("Question"))
    image = models.ImageField(_("Image"), upload_to='images/answers', null=True, blank=True)
    is_correct = models.BooleanField(_("Is Correct"), default=False)

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")

    def __str__(self):
        return self.text


def quiz_result_pdf_path(instance, filename):
    return f'quiz_results/user_{instance.user_token}/{filename}'


class QuizResult(models.Model):
    user_token = models.UUIDField(_("User Token"), default=uuid.uuid4, editable=False)
    # name = models.CharField(_("Name"), max_length=255)
    # parent_name = models.CharField(_("Parent Name"), max_length=255, blank=True, null=True)
    # phone_number = models.CharField(_("Phone Number"), max_length=20)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='results', null=True, blank=True, verbose_name=_("Quiz"))
    answers = models.ManyToManyField(Answer, blank=True, verbose_name=_("Answers"))
    unanswered_questions = models.ManyToManyField(Question, blank=True, related_name='unanswered_by', verbose_name=_("Unanswered Questions"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    result_pdf = models.FileField(_("Result PDF"), upload_to='quiz_results/', null=True, blank=True)
    diagnostic_pdf = models.FileField(_("Diagnostic PDF"), upload_to='quiz_diagnostics/', null=True, blank=True)

    total_possible_points = models.PositiveIntegerField(_("Total Possible Points"), default=0)
    user_points = models.PositiveIntegerField(_("User Points"), default=0)

    class Meta:
        verbose_name = _("Quiz Result")
        verbose_name_plural = _("Quiz Results")

    def get_pdf_url(self):
        if self.result_pdf:
            return self.result_pdf.url
        return None
    
    def __str__(self):
        return f'{self.quiz.name}' 