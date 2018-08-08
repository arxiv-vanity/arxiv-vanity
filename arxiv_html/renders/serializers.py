from rest_framework import serializers
from .models import Render


class RenderSerializer(serializers.ModelSerializer):
    html_url = serializers.CharField(source='get_output_url', read_only=True)

    class Meta:
        model = Render
        fields = ('id_type', 'paper_id', 'created_at', 'state', 'html_url')
        read_only_fields = ('created_at', 'state', 'html_url')
