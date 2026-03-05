from rest_framework import serializers
from .models import Provider, Service

class ProviderSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    class Meta:
        model = Provider
        fields = ['id', 'owner', 'name', 'email', 'phone', 'business_type', 'is_verified']

class ServiceSerializer(serializers.ModelSerializer):
    provider = serializers.PrimaryKeyRelatedField(read_only=True)
    provider_name = serializers.CharField(source='provider.name', read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'provider', 'provider_name', 'title', 'description', 'price', 'duration_hours', 'is_active']
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive.")
        return value

