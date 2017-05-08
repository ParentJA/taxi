from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Trip


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username',)
        read_only_fields = ('username',)


class PrivateUserSerializer(UserSerializer):
    groups = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = list(UserSerializer.Meta.fields) + ['auth_token', 'groups']


class TripSerializer(serializers.ModelSerializer):
    driver = UserSerializer(allow_null=True, required=False)
    rider = UserSerializer(allow_null=True, required=False)

    def create(self, validated_data):
        driver_data = validated_data.pop('driver', None)
        rider_data = validated_data.pop('rider', None)
        trip = super().create(validated_data)
        if driver_data:
            trip.driver = get_user_model().objects.get(**driver_data)
        if rider_data:
            trip.rider = get_user_model().objects.get(**rider_data)
        trip.save()
        return trip

    def update(self, instance, validated_data):
        driver_data = validated_data.pop('driver', None)
        if driver_data:
            instance.driver = get_user_model().objects.get(**driver_data)
        rider_data = validated_data.pop('rider', None)
        if rider_data:
            instance.rider = get_user_model().objects.get(**rider_data)
        instance = super().update(instance, validated_data)
        return instance

    class Meta:
        model = Trip
        fields = '__all__'
        read_only_fields = ('id', 'nk', 'created', 'updated',)
