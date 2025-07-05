import uuid
from django.db import models
from django.utils.text import slugify
from django.db.models import JSONField
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import secrets

def generate_unique_link(folder_name):
    base_slug = slugify(folder_name)
    unique_suffix = uuid.uuid4().hex  # 32 characters
    return f"{base_slug}-{unique_suffix}"




class FolderUpload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder_name = models.CharField(max_length=255)

    # the “manager” link
    unique_link = models.SlugField(unique=True, blank=True)

    # the “student” link
    work_link = models.SlugField(unique=True, blank=True)

    # later you can fill this with your rubric JSON
    rubric = JSONField(null=True, blank=True)

    file_path = models.CharField(
        max_length=500,
        help_text="The S3 base prefix where the folder’s files are stored"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # ensure both links are generated
        if not self.unique_link:
            self.unique_link = generate_unique_link(self.folder_name)
        if not self.work_link:
            # you can pass a different seed if you like
            self.work_link = generate_unique_link(self.folder_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.folder_name} (manage={self.unique_link}, work={self.work_link})"


# Default functions for JSONField defaults
def default_z_indices():
    return {"codeEntry": 100, "codePreview": 100, "draggableFileStructure": 100}

def default_size():
    return {"width": 400, "height": 300}

def default_tab_state():
    return {"tabs": [{"pathTo": "", "fileName": "Untitled.html", "type": "file"}], "selectedTab": 0}

def default_position():
    return {"x": 0, "y": 0}



class Submission(models.Model):
    """
    Represents one student’s “snapshot” of a FolderUpload.
    """
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False)
    # link back to the master folder
    folder = models.ForeignKey(
        FolderUpload,
        on_delete=models.CASCADE,
        related_name="submissions"
    )
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)

    # this lets you save a separate S3 prefix or local path
    file_path = models.CharField(
        max_length=500,
        help_text="The S3 prefix (or other) for this submission’s files"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} – {self.folder.folder_name}"


class Grade(models.Model):
    """
    A time-stamped numeric grade (0–100) for one Submission.
    """
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False)
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="grades"
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.submission}: {self.score}"

class CodeEntry(models.Model):
    """
    A single editor pane’s state for one Submission.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="code_entries"
    )
    editor_id = models.PositiveIntegerField()
    language = models.CharField(
        max_length=50,
        default="html",
        help_text="e.g. 'html', 'javascript', 'python', etc."
    )
    code = models.TextField(
        default="<h1>Hello, World!</h1>\n<p>This is an HTML editor.</p>"
    )
    path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Relative file path within this submission"
    )
    show_line_numbers = models.BooleanField(
        default=True,
        help_text="Whether to display line numbers in the editor"
    )
    size = models.JSONField(
        default=default_size,
        help_text="Width/height of the editor pane"
    )
    font_size = models.PositiveSmallIntegerField(
        default=14,
        help_text="Editor font size in px"
    )
    tab_state = models.JSONField(
        default=default_tab_state,
        help_text="Configuration of tabs (order, active tab, etc.)"
    )
    scroll_top = models.PositiveIntegerField(
        default=0,
        help_text="Vertical scroll position"
    )
    position = models.JSONField(
        default=default_position,
        help_text="X/Y position of the pane if draggable"
    )
    active_handle = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Which resize handle is active, if any"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "editor_id"],
                name="unique_submission_editor"
            )
        ]
        ordering = ["editor_id"]

    def __str__(self):
        return f"Entry {self.editor_id} for {self.submission}"
    

class Form(models.Model):
    topic           = models.CharField(max_length=255, blank=True)
    description     = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    manage_token    = models.CharField(max_length=64, unique=True, editable=False)
    access_token    = models.CharField(max_length=64, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.manage_token:
            # 32 bytes → ~43 chars of URL-safe text
            self.manage_token = secrets.token_urlsafe(32)
        if not self.access_token:
            self.access_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

class CompletedField(models.Model):
    form = models.ForeignKey(Form, related_name="completed_fields", on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ("order",)
