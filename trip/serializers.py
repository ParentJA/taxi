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
        read_only_fields = ('username',)


class PrivateUserSerializer(UserSerializer):
    groups = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = list(UserSerializer.Meta.fields) + ['auth_token', 'groups']


class TripSerializer(serializers.ModelSerializer):
    driver = UserSerializer(allow_null=True, required=False)
    riders = UserSerializer(many=True, allow_null=True, required=False)

    def create(self, validated_data):
        user_model = get_user_model()
        rider_data = validated_data.pop('riders', [])
        driver_data = validated_data.pop('driver', None)
        trip = Trip.objects.create(**validated_data)
        for data in rider_data:
            trip.riders.add(user_model.objects.get(**data))
        if driver_data:
            trip.driver = user_model.objects.get(**driver_data)
        trip.save()
        return trip

    def update(self, instance, validated_data):
        user_model = get_user_model()
        rider_data = validated_data.pop('riders', [])
        for data in rider_data:
            instance.riders.add(user_model.objects.get(**data))
        driver_data = validated_data.pop('driver', None)
        if driver_data:
            instance.driver = user_model.objects.get(**driver_data)
        instance.pick_up_address = validated_data.get('pick_up_address', instance.pick_up_address)
        instance.drop_off_address = validated_data.get('drop_off_address', instance.drop_off_address)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance

    class Meta:
        model = Trip
        fields = ('id', 'nk', 'created', 'updated', 'pick_up_address', 'drop_off_address', 'status', 'driver',
                  'riders',)
        read_only_fields = ('id', 'nk', 'created', 'updated',)
