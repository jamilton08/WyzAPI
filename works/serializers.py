# yourapp/serializers.py

from rest_framework import serializers
from .models import Assignment, Submission
from .models import Form, CompletedField

class AssignmentCreateSerializer(serializers.ModelSerializer):
    folder_link = serializers.CharField(write_only=True)
    rubric       = serializers.JSONField()

    class Meta:
        model = Assignment
        fields = ["folder_link", "rubric"]

    def create(self, validated_data):
        from .models import FolderUpload
        folder_link = validated_data.pop("folder_link")
        folder = FolderUpload.objects.get(unique_link=folder_link)
        return Assignment.objects.create(folder_upload=folder, **validated_data)


class AssignmentListSerializer(serializers.ModelSerializer):
    managing_link = serializers.UUIDField(read_only=True)
    work_link     = serializers.UUIDField(read_only=True)

    class Meta:
        model = Assignment
        fields = ["managing_link", "work_link"]



class FormInitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = ("id", "manage_token", "access_token")

class CompletedFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompletedField
        fields = ("order", "question", "answer")

class FormDetailSerializer(serializers.ModelSerializer):
    completed_fields = CompletedFieldSerializer(many=True)
    class Meta:
        model = Form
        fields = ("id", "topic", "description", "created_at", "completed_fields")
