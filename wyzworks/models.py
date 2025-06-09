import uuid
from django.db import models
from django.utils.text import slugify
from django.db.models import JSONField, Q
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


def generate_unique_link(folder_name):
    base_slug = slugify(folder_name)
    unique_suffix = uuid.uuid4().hex  # 32 characters
    return f"{base_slug}-{unique_suffix}"



class Device(models.Model):
    """
    A client device (identified by a UUID the client generates
    and persists in localStorage or a cookie).
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)
    
class FolderUpload(models.Model):
    ASSIGNMENT_DEVICE = "device"
    ASSIGNMENT_LINK   = "link"
    ASSIGNMENT_BOTH   = "both"
    ASSIGNMENT_CHOICES = [
        (ASSIGNMENT_DEVICE, "Device Only"),
        (ASSIGNMENT_LINK,   "Link Only"),
        (ASSIGNMENT_BOTH,   "Both"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder_name = models.CharField(max_length=255)

    # the “manager” link
    unique_link = models.SlugField(unique=True, blank=True)

    # the “student” link
    work_link = models.SlugField(unique=True, blank=True)

    # later you can fill this with your rubric JSON
    rubric = JSONField(null=True, blank=True)

    # how students may submit this assignment
    assignment_mode = models.CharField(
        max_length=10,
        choices=ASSIGNMENT_CHOICES,
        default=ASSIGNMENT_BOTH,
        help_text="Allow students to submit via device, link, or both"
    )

    file_path = models.CharField(
        max_length=500,
        help_text="The S3 base prefix where the folder’s files are stored"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.unique_link:
            self.unique_link = generate_unique_link(self.folder_name)
        if not self.work_link:
            self.work_link = generate_unique_link(self.folder_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.folder_name} "
            f"(manage={self.unique_link}, work={self.work_link}, "
            f"mode={self.assignment_mode})"
        )

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
    A student’s submission for one FolderUpload, identified by:
      - device: a client-stored UUID  (mode="device")
      - exchange_uuid: a server-generated UUID (mode="link")
    """
    MODE_DEVICE = "device"
    MODE_LINK   = "link"
    MODE_CHOICES = [
        (MODE_DEVICE, "Device"),
        (MODE_LINK,   "Link"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    folder = models.ForeignKey(
        FolderUpload,
        on_delete=models.CASCADE,
        related_name="submissions"
    )

    # 1) How this submission was created:
    submission_mode = models.CharField(
        max_length=10,
        choices=(
            (MODE_DEVICE, "Device"),
            (MODE_LINK,   "Link"),
        ),
    )

    # 2a) For device-mode:
    device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="submissions",
        help_text="Client device UUID (if mode=device)"
    )

    # 2b) For link-mode we give each submission its own exchange UUID:
    exchange_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        null=True, blank=True,
        editable=False,
        help_text="Server-generated link ID (if mode=link)"
    )

    # where to store this student’s files
    file_path = models.CharField(
        max_length=500,
        help_text="The S3 prefix (or other) for this submission’s files"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # one submission per folder+device when in device mode
        constraints = [
            models.UniqueConstraint(
                fields=["folder", "device"],
                name="unique_folder_device",
                condition=Q(submission_mode="device")
            ),
            # one submission per folder+exchange_uuid when in link mode
            models.UniqueConstraint(
                fields=["folder", "exchange_uuid"],
                name="unique_folder_exchange",
                condition=Q(submission_mode="Link")
            ),
        ]
        ordering = ["created_at"]

    def clean(self):
        super().clean()
        folder_mode = self.folder.assignment_mode

        # First validate the normal “one or the other” logic
        if self.submission_mode == self.MODE_DEVICE:
            if not self.device or self.exchange_uuid:
                raise ValidationError("Device mode requires `device` only.")
        else:  # link mode
            if not self.exchange_uuid or self.device:
                raise ValidationError("Link mode requires `exchange_uuid` only.")

        # Then enforce what FolderUpload allows
        if folder_mode == FolderUpload.ASSIGNMENT_DEVICE and self.submission_mode != self.MODE_DEVICE:
            raise ValidationError("This assignment accepts device-only submissions.")
        if folder_mode == FolderUpload.ASSIGNMENT_LINK and self.submission_mode != self.MODE_LINK:
            raise ValidationError("This assignment accepts link-only submissions.")

    def __str__(self):
        if self.submission_mode == self.MODE_DEVICE:
            return f"Submission by device {self.device} for {self.folder}"
        return f"Link submission {self.exchange_uuid} for {self.folder}"


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