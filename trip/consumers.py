# Standard library imports.
import json

# Django imports.
from django.contrib.auth import get_user_model

# Third-party imports.
from channels import Group
from channels.generic.websockets import WebsocketConsumer

# Local imports.
from .models import Trip
from .serializers import TripSerializer


class AuthenticatedWebsocketConsumer(WebsocketConsumer):
    http_user_and_session = True

    def connect(self, message, **kwargs):
        if self.message.user.is_authenticated:
            super().connect(message, **kwargs)

    def receive(self, text=None, bytes=None, **kwargs):
        if self.message.user.is_authenticated:
            super().receive(text, bytes, **kwargs)

    def disconnect(self, message, **kwargs):
        if self.message.user.is_authenticated:
            super().disconnect(message, **kwargs)


class TripConsumer(WebsocketConsumer):
    http_user_and_session = True

    def current_rider_trips(self, user):
        return user.trips_as_rider.exclude(status=Trip.COMPLETED)

    def current_driver_trips(self, user):
        return user.trips_as_driver.exclude(status=Trip.COMPLETED)

    def requested_trips(self):
        return Trip.objects.filter(driver__isnull=True, status=Trip.REQUESTED)

    def user_is_rider(self, user):
        return 'rider' in [group.name for group in user.groups.all()]

    def user_is_driver(self, user):
        return 'driver' in [group.name for group in user.groups.all()]

    def connection_groups(self, **kwargs):
        return ['riders', 'drivers']

    def connect(self, message, **kwargs):
        self.message.reply_channel.send({'accept': True})

        # Register rider for messages regarding current ride.
        if self.message.user.is_authenticated:
            trip_nks = [trip.nk for trip in self.current_rider_trips(self.message.user)]
            trip_nks.extend([trip.nk for trip in self.current_driver_trips(self.message.user)])
            self.message.channel_session['trip_nks'] = trip_nks
            for trip_nk in trip_nks:
                Group(trip_nk).add(self.message.reply_channel)
            if self.user_is_driver(self.message.user):
                Group('drivers').add(self.message.reply_channel)

    def receive(self, text=None, bytes=None, **kwargs):
        if self.message.user.is_authenticated:
            data = json.loads(text)

            # Rider creates new trips.
            if self.user_is_rider(self.message.user):
                serializer = TripSerializer(data=data)
                if serializer.is_valid():
                    trip = serializer.create(serializer.validated_data)
                    self.message.channel_session['trip_nks'].append(trip.nk)
                    Group(trip.nk).add(self.message.reply_channel)
                    self.group_send(name=trip.nk, text=json.dumps(TripSerializer(trip).data))
                    self.group_send(name='drivers', text=json.dumps(TripSerializer(trip).data))

            # Driver updates existing trips.
            elif self.user_is_driver(self.message.user):
                trip = Trip.objects.get(nk=data.get('nk'))
                serializer = TripSerializer(data=data)
                if serializer.is_valid():
                    trip = serializer.update(trip, serializer.validated_data)
                    self.message.channel_session['trip_nks'].append(trip.nk)
                    Group(trip.nk).add(self.message.reply_channel)
                    self.group_send(name=trip.nk, text=json.dumps(TripSerializer(trip).data))

    def disconnect(self, message, **kwargs):
        for trip_nk in message.channel_session.get('trip_nks', []):
            Group(trip_nk).discard(message.reply_channel)
