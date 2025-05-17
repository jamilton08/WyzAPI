import uuid
from django.db import models

class VideoUpload(models.Model):
    unique_link = models.CharField(
        max_length=255,
        unique=True,
        blank=True  # Auto-filled on save.
    )
    shareable_link = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="A second UUID used for sharing with others."
    )
    file_path = models.CharField(max_length=255)  # e.g. S3 URL or key.
    url = models.URLField(
        max_length=2048,
        blank=True,
        null=True,
        help_text="The URL of the source page."
    )
    login_required = models.BooleanField(
        default=False,
        help_text="Determined by scanning the URL for login restrictions."
    )
    upload_date = models.DateTimeField(auto_now_add=True)

    steps = models.ManyToManyField(
        'Step',
        related_name='video_uploads',
        blank=True
    )

    recordings = models.JSONField(default=list, blank=True)

    def save(self, *args, **kwargs):
        if not self.unique_link:
            self.unique_link = str(uuid.uuid4())
        if not self.shareable_link:
            self.shareable_link = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unique_link} (Shareable: {self.shareable_link})"


class Step(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.BigIntegerField()  # e.g. timestamp in milliseconds
    end_time = models.BigIntegerField()
    thumb_start = models.TextField()       # stores URL or data URL string
    thumb_end = models.TextField()
    events = models.JSONField(blank=True, null=True)  # Stores events info as JSON data.
    order = models.IntegerField(default=0)
    # New field: link or file path to the trimmed video clip
    trimmed_video = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Stores the URL or key for the trimmed video clip."
    )
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title}: {self.start_time} - {self.end_time}"