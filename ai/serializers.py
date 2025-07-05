from rest_framework import serializers
from wyzworks.models import Form, CompletedField


class CompletedFieldSerializer(serializers.ModelSerializer):
    # expose the JSONField `default_props` under the camelCase key `defaultProps`
    defaultProps = serializers.JSONField(source="default_props")
    # expose the JSONField `validation`
    validation   = serializers.JSONField()

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

class FormDetailSerializer(serializers.ModelSerializer):
    completed_fields = CompletedFieldSerializer(many=True)
    class Meta:
        model = Form
        fields = ("id", "topic", "description", "created_at", "completed_fields")
