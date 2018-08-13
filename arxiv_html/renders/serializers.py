from rest_framework import serializers
from .models import Render


class RenderSerializer(serializers.ModelSerializer):
    output_url = serializers.CharField(source='get_output_url', read_only=True)

    class Meta:
        model = Render
        fields = ('id', 'source_type', 'source_id', 'created_at', 'state', 'output_url', 'logs')
        read_only_fields = ('id', 'created_at', 'state', 'output_url', 'logs')
