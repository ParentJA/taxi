# Django imports.
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

# Third-party imports.
from rest_framework import serializers

# Local imports.
from .models import Trip


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email',)


class PrivateUserSerializer(UserSerializer):
    groups = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = list(UserSerializer.Meta.fields) + ['auth_token', 'groups']


class TripSerializer(serializers.ModelSerializer):
    driver = UserSerializer(read_only=True)
    riders = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = ('id', 'nk', 'created', 'updated', 'pick_up_address', 'drop_off_address', 'status', 'driver',
                  'riders',)
        read_only_fields = ('id', 'nk', 'created', 'updated',)
