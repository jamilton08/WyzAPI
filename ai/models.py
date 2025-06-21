from django.db import models
from django.contrib.postgres.fields import JSONField  # If you use PostgreSQL


class PromptDSL(models.Model):
    prompt     = models.TextField(help_text="The original text prompt sent to the OpenAI API")
    dsl        = models.JSONField(help_text="The Fabric.js–ready DSL output, stored as raw JSON")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Prompt + DSL Record"
        verbose_name_plural = "Prompt + DSL Records"

    def __str__(self):
        # show first 50 chars of prompt in the admin/list views
        snippet = (self.prompt[:47] + '...') if len(self.prompt) > 50 else self.prompt
        return f"{snippet} (#{self.pk})"


def difficulty_choices():
    return [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]


class GeneratedQuestion(models.Model):
    question_id    = models.PositiveIntegerField(help_text="Original question identifier")
    subject        = models.CharField(max_length=100, help_text="Subject name, e.g. Math")
    topic          = models.CharField(max_length=200, help_text="Main topic, e.g. Fractions basics")
    subtopic       = models.CharField(max_length=200, blank=True, help_text="Subtopic or detail hint")
    grade_level    = models.PositiveSmallIntegerField(help_text="Grade level between 1 and 12")
    question_type  = models.CharField(max_length=50, help_text="Question type, e.g. Short Answer, Word Problem")
    question_text  = models.TextField(help_text="The text of the question")
    difficulty     = models.CharField(max_length=10, choices=difficulty_choices(), help_text="Difficulty rating")
    rubric_part_1  = models.TextField(blank=True, help_text="First rubric criterion")
    rubric_part_2  = models.TextField(blank=True, help_text="Second rubric criterion")
    rubric_part_3  = models.TextField(blank=True, help_text="Third rubric criterion")
    rubric_part_4  = models.TextField(blank=True, help_text="Fourth rubric criterion")
    rubric_part_5  = models.TextField(blank=True, help_text="Fifth rubric criterion")
    jsx_code       = models.TextField(blank=True, help_text="JSXGraph code snippet, if any")
    mathjax        = models.TextField(blank=True, help_text="LaTeX representation of the question")
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Generated Question'
        verbose_name_plural = 'Generated Questions'

    def __str__(self):
        snippet = (self.question_text[:47] + '...') if len(self.question_text) > 50 else self.question_text
        return f"{self.question_id}: {snippet}"


class RubricRequest(models.Model):
    """
    Stores each rubric prompt and the generated JSON result.
    """
    prompt_text = models.TextField(help_text="User’s raw rubric prompt or existing rubric text")
    generated_rubric = models.JSONField(
        blank=True,
        null=True,
        help_text="The list of {part, weight} dicts returned by GPT"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RubricRequest #{self.id} @ {self.created_at:%Y-%m-%d %H:%M}"

class AssignmentRequest(models.Model):
    prompt_text = models.TextField()
    generated_assignment = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AssignmentRequest #{self.pk}"

class LessonPlanRequest(models.Model):
    prompt_text = models.TextField()
    generated_lessonplan = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"LessonPlanRequest #{self.pk}"