from rest_framework import viewsets, permissions
from .models import Provider, Service
from .serializers import ProviderSerializer, ServiceSerializer
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsProviderOwner
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response

class ProviderViewSet(viewsets.ModelViewSet):
    queryset = Provider.objects.all().order_by('id')
    serializer_class = ProviderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['business_type','name']

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'services']:
            return [permissions.IsAuthenticated(), IsProviderOwner()]
        elif self.action == 'destroy':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def services(self, request, pk=None):
        """POST /api/providers/{id}/services/ — Create a service for a provider (owner only)"""
        provider = self.get_object()
        serializer = ServiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(provider=provider)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'provider__business_type': ['exact'],
        'price': ['gte', 'lte'], 
    }
    ordering_fields = ['price', 'created_at']

    def get_permissions(self):
        if self.action in ['update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsProviderOwner()]
        return [permissions.IsAuthenticatedOrReadOnly()]
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def book(self, request, pk=None):
        """Requirement: POST /api/services/{id}/book/"""
        service = self.get_object()
        from apps.bookings.serializers import BookingSerializer
        serializer = BookingSerializer(data=request.data, context={'service': service, 'request': request})
        if serializer.is_valid():
            serializer.save(
                service=service,
                created_by=request.user,
            )
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
