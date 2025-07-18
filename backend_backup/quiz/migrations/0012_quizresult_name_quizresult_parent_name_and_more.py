# Generated by Django 5.1.7 on 2025-04-02 04:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0011_remove_quizresult_name_remove_quizresult_parent_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizresult',
            name='name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='quizresult',
            name='parent_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='quizresult',
            name='phone_number',
            field=models.CharField(default='', max_length=20),
            preserve_default=False,
        ),
    ]
