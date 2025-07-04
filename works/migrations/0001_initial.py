# Generated by Django 5.1.1 on 2025-06-08 18:08

import django.core.validators
import django.db.models.deletion
import uuid
import works.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FolderUpload",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("folder_name", models.CharField(max_length=255)),
                ("unique_link", models.SlugField(blank=True, unique=True)),
                ("work_link", models.SlugField(blank=True, unique=True)),
                ("rubric", models.JSONField(blank=True, null=True)),
                (
                    "file_path",
                    models.CharField(
                        help_text="The S3 base prefix where the folder’s files are stored",
                        max_length=500,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Submission",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                (
                    "file_path",
                    models.CharField(
                        help_text="The S3 prefix (or other) for this submission’s files",
                        max_length=500,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "folder",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submissions",
                        to="works.folderupload",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Grade",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "score",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ]
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="grades",
                        to="works.submission",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CodeEntry",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("editor_id", models.PositiveIntegerField()),
                (
                    "language",
                    models.CharField(
                        default="html",
                        help_text="e.g. 'html', 'javascript', 'python', etc.",
                        max_length=50,
                    ),
                ),
                (
                    "code",
                    models.TextField(
                        default="<h1>Hello, World!</h1>\n<p>This is an HTML editor.</p>"
                    ),
                ),
                (
                    "path",
                    models.CharField(
                        blank=True,
                        help_text="Relative file path within this submission",
                        max_length=500,
                    ),
                ),
                (
                    "show_line_numbers",
                    models.BooleanField(
                        default=True,
                        help_text="Whether to display line numbers in the editor",
                    ),
                ),
                (
                    "size",
                    models.JSONField(
                        default=works.models.default_size,
                        help_text="Width/height of the editor pane",
                    ),
                ),
                (
                    "font_size",
                    models.PositiveSmallIntegerField(
                        default=14, help_text="Editor font size in px"
                    ),
                ),
                (
                    "tab_state",
                    models.JSONField(
                        default=works.models.default_tab_state,
                        help_text="Configuration of tabs (order, active tab, etc.)",
                    ),
                ),
                (
                    "scroll_top",
                    models.PositiveIntegerField(
                        default=0, help_text="Vertical scroll position"
                    ),
                ),
                (
                    "position",
                    models.JSONField(
                        default=works.models.default_position,
                        help_text="X/Y position of the pane if draggable",
                    ),
                ),
                (
                    "active_handle",
                    models.CharField(
                        blank=True,
                        help_text="Which resize handle is active, if any",
                        max_length=50,
                        null=True,
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="code_entries",
                        to="works.submission",
                    ),
                ),
            ],
            options={
                "ordering": ["editor_id"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("submission", "editor_id"),
                        name="unique_submission_editor",
                    )
                ],
            },
        ),
    ]
