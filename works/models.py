import uuid
from django.db import models
from django.utils.text import slugify


def generate_unique_link(folder_name):
    base_slug = slugify(folder_name)
    unique_suffix = uuid.uuid4().hex  # 32 characters
    return f"{base_slug}-{unique_suffix}"

class FolderUpload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder_name = models.CharField(max_length=255)
    unique_link = models.SlugField(unique=True, blank=True)
    file_path = models.CharField(
        max_length=500,
        help_text="The location on disk (or S3, etc.) where the folder is stored."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Generate a unique link if not already set.
        if not self.unique_link:
            self.unique_link = generate_unique_link(self.folder_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.folder_name} ({self.unique_link})"

# Default functions for JSONField defaults
def default_z_indices():
    return {"codeEntry": 100, "codePreview": 100, "draggableFileStructure": 100}

def default_size():
    return {"width": 400, "height": 300}

def default_tab_state():
    return {"tabs": [{"pathTo": "", "fileName": "Untitled.html", "type": "file"}], "selectedTab": 0}

def default_position():
    return {"x": 0, "y": 0}

class CodeEditorState(models.Model):
    folder_upload = models.OneToOneField(
        FolderUpload, on_delete=models.CASCADE, related_name="code_editor_state"
    )
    tabs_orientation = models.CharField(max_length=20, default="horizontal")
    open_menu = models.CharField(max_length=50, null=True, blank=True)
    language = models.IntegerField(default=0)
    preview_modal = models.BooleanField(default=False)
    selected_editor = models.IntegerField(default=0)
    selected_item = models.JSONField(null=True, blank=True)
    active_component = models.CharField(max_length=100, blank=True, default="")
    z_indices = models.JSONField(default=default_z_indices)

    def __str__(self):
        return f"Editor State for {self.folder_upload}"

class CodeEntryState(models.Model):
    code_editor_state = models.ForeignKey(
        CodeEditorState, on_delete=models.CASCADE, related_name="code_entries"
    )
    editor_id = models.IntegerField()
    language = models.CharField(max_length=50, default="html")
    code = models.TextField(default="<h1>Hello, World!</h1>\n<p>This is an HTML editor.</p>")
    path_to = models.CharField(max_length=500, blank=True)
    show_lines = models.BooleanField(default=True)
    selected_language = models.CharField(max_length=50, default="html")
    size = models.JSONField(default=default_size)
    font_size = models.IntegerField(default=14)
    tab_state = models.JSONField(default=default_tab_state)
    scroll_top = models.IntegerField(default=0)
    position = models.JSONField(default=default_position)
    active_handle = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ("code_editor_state", "editor_id")
        ordering = ["editor_id"]

    def __str__(self):
        return f"Code Entry {self.editor_id} for {self.code_editor_state}"
