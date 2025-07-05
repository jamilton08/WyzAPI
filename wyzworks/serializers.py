# yourapp/serializers.py
from rest_framework import serializers
from .models import Form, CompletedField, FormFile




class FormInitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = ("id", "manage_token", "access_token")

class CompletedFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompletedField
        fields = (
            "order",
            "field_type",
            "uid",
            "question",
            "answer",
            "defaultProps",
            "validation",
            "gradable",
            "points",
        )

class CompletedModulatedFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompletedField
        fields = (
            "order",
            "field_type",
            "uid",
            "question",
            "answer",
            "default_props",
            "validation",
            "gradable",
            "points",
        )

class FormFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompletedField
        fields = (
            "order",
            "field_type",
            "uid",
            "question",
            "default_props",
            "validation",
            "gradable",
            "points",
        )


class FormDetailSerializer(serializers.ModelSerializer):
    completed_fields = CompletedFieldSerializer(many=True)
    class Meta:
        model = Form
        fields = ("id", "topic", "description", "created_at", "completed_fields")


class FormLinkerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FormFile
        fields = ('id', 'form', 'file_id', 'created_at')
        read_only_fields = ('id', 'created_at')