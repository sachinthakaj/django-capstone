from rest_framework import permissions


class IsProviderOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, 'owner', None) or getattr(getattr(obj, 'provider', None), 'owner', None)
        return owner == request.user
