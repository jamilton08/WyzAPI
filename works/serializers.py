# yourapp/serializers.py

from rest_framework import serializers
from .models import Assignment, Submission

class AssignmentCreateSerializer(serializers.ModelSerializer):
    folder_link = serializers.CharField(write_only=True)
    rubric       = serializers.JSONField()

    class Meta:
        model = Assignment
        fields = ["folder_link", "rubric"]

    def create(self, validated_data):
        from yourapp.models import FolderUpload
        folder_link = validated_data.pop("folder_link")
        folder = FolderUpload.objects.get(unique_link=folder_link)
        return Assignment.objects.create(folder_upload=folder, **validated_data)


class AssignmentListSerializer(serializers.ModelSerializer):
    managing_link = serializers.UUIDField(read_only=True)
    work_link     = serializers.UUIDField(read_only=True)

    class Meta:
        model = Assignment
        fields = ["managing_link", "work_link"]
