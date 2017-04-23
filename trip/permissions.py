# Third-party imports.
from rest_framework import permissions


class IsDriver(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return 'driver' in [group.name for group in request.user.groups]


class IsRider(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return 'rider' in [group.name for group in request.user.groups]
