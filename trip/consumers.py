from channels import Group
from channels.generic.websockets import JsonWebsocketConsumer
from .models import Trip
from .serializers import TripSerializer


class TripConsumer(JsonWebsocketConsumer):
    http_user_and_session = True

    def user_trips(self):
        raise NotImplementedError()

    def connect(self, message, **kwargs):
        self.message.reply_channel.send({'accept': True})
        if self.message.user.is_authenticated:
            trip_nks = [trip.nk for trip in self.user_trips()]
            self.message.channel_session['trip_nks'] = trip_nks
            for trip_nk in trip_nks:
                Group(trip_nk).add(self.message.reply_channel)

    def disconnect(self, message, **kwargs):
        for trip_nk in message.channel_session.get('trip_nks', []):
            Group(trip_nk).discard(message.reply_channel)


class DriverConsumer(TripConsumer):
    groups = ['drivers']

    def user_trips(self):
        return self.message.user.trips_as_driver.exclude(status=Trip.COMPLETED)

    def connect(self, message, **kwargs):
        super().connect(message, **kwargs)
        Group('drivers').add(self.message.reply_channel)

    def receive(self, content, **kwargs):
        """Drivers should send trip status updates."""

        # Update an existing trip from the incoming data.
        trip = Trip.objects.get(nk=content.get('nk'))
        serializer = TripSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        trip = serializer.update(trip, serializer.validated_data)

        # Subscribe driver to messages regarding the existing trip.
        # Driver will receive updates about existing trip.
        self.message.channel_session['trip_nks'].append(trip.nk)
        Group(trip.nk).add(self.message.reply_channel)
        trips_data = TripSerializer(trip).data
        self.group_send(name=trip.nk, content=trips_data)


class RiderConsumer(TripConsumer):
    def user_trips(self):
        return self.message.user.trips_as_rider.exclude(status=Trip.COMPLETED)

    def receive(self, content, **kwargs):
        """Riders should only ever send a request to create a new Trip."""

        # Create a new trip from the incoming data.
        serializer = TripSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        trip = serializer.create(serializer.validated_data)

        # Subscribe rider to messages regarding the newly created trip.
        # Rider will receive updates from driver.
        self.message.channel_session['trip_nks'].append(trip.nk)
        Group(trip.nk).add(self.message.reply_channel)
        trips_data = TripSerializer(trip).data
        self.group_send(name=trip.nk, content=trips_data)

        # Alert all drivers that a new trip has been requested.
        self.group_send(name='drivers', content=trips_data)
