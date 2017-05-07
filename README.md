**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """User data visible to anyone."""

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email')
        read_only_fields = ('username',)


class PrivateUserSerializer(UserSerializer):
    """Private data only visible to the logged-in user."""

    groups = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = list(UserSerializer.Meta.fields) + ['auth_token', 'groups']
```

**trip/apis.py**

```python
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from rest_framework import status, views
from rest_framework.response import Response
from .serializers import PrivateUserSerializer


class SignUpView(views.APIView):
    def post(self, *args, **kwargs):
        email = self.request.data.get('email')
        group = self.request.data.get('group', 'rider')
        user_group, _ = Group.objects.get_or_create(name=group)
        form = UserCreationForm(data=self.request.data)
        if form.is_valid():
            user = form.save()
            user.email = email
            user.groups.add(user_group)
            user.save()
            return Response(PrivateUserSerializer(user).data, status=status.HTTP_201_CREATED)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
```

**taxi/urls.py**

```python
from django.conf.urls import url
from trip.apis import SignUpView

urlpatterns = [
    url(r'^api/sign_up/$', SignUpView.as_view(), name='sign_up'),
]
```

```bash
$ curl -H "Content-Type: application/json" -X POST -d '{"username": "Rider", "password1": "pAssw0rd$", "password2": "pAssw0rd$", "email": "rider@example.com", "group": "rider"}' http://localhost:8000/api/sign_up/

{"id":1,"username":"Rider","email":"rider@example.com","auth_token":null,"groups":["rider"]}
```

**trip/apis.py**

```python
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group
from rest_framework import permissions, status, views
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .serializers import PrivateUserSerializer


class SignUpView(views.APIView): ...


class LogInView(views.APIView):
    def post(self, *args, **kwargs):
        form = AuthenticationForm(data=self.request.data)
        if form.is_valid():
            user = form.get_user()
            login(self.request, user)
            Token.objects.get_or_create(user=user)
            return Response(PrivateUserSerializer(user).data)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class LogOutView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, *args, **kwargs):
        Token.objects.get(user=self.request.user).delete()
        logout(self.request)
        return Response(status=status.HTTP_204_NO_CONTENT)
```

**taxi/urls.py**

```python
from django.conf.urls import url
from trip.apis import SignUpView, LogInView, LogOutView

urlpatterns = [
    url(r'^api/sign_up/$', SignUpView.as_view(), name='sign_up'),
    url(r'^api/log_in/$', LogInView.as_view(), name='log_in'),
    url(r'^api/log_out/$', LogOutView.as_view(), name='log_out'),
]
```

```bash
$ curl -H "Content-Type: application/json" -X POST -d '{"username": "Rider", "password": "pAssw0rd$"}' http://localhost:8000/api/log_in/

{"id":1,"username":"Rider","email":"rider@example.com","auth_token":43841bb28794f6b433b5c95df9ff879d104a2b6f,"groups":["rider"]}
```

```bash
$ curl -H "Authorization: Token 43841bb28794f6b433b5c95df9ff879d104a2b6f" -X POST http://localhost:8000/api/log_out/
```

**trip/models.py**

```python
import datetime
import hashlib
from django.conf import settings
from django.db import models


class Trip(models.Model):
    REQUESTED = 'REQUESTED'
    STARTED = 'STARTED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    TRIP_STATUSES = (
        (REQUESTED, REQUESTED),
        (STARTED, STARTED),
        (IN_PROGRESS, IN_PROGRESS),
        (COMPLETED, COMPLETED),
    )

    nk = models.CharField(max_length=32, unique=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    pick_up_address = models.CharField(max_length=255)
    drop_off_address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=TRIP_STATUSES, default=REQUESTED)
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='trips_as_driver')
    rider = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='trips_as_rider')

    def save(self, **kwargs):
        if not self.nk:
            secure_hash = hashlib.md5()
            secure_hash.update('{now}:{pick_up_address}:{drop_off_address}'.format(
                now=datetime.datetime.now(),
                pick_up_address=self.pick_up_address,
                drop_off_address=self.drop_off_address
            ).encode('utf-8'))
            self.nk = secure_hash.hexdigest()
        super().save(**kwargs)
```

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Trip


class UserSerializer(serializers.ModelSerializer): ...


class PrivateUserSerializer(serializers.ModelSerializer): ...


class TripSerializer(serializers.ModelSerializer):
    driver = UserSerializer(allow_null=True, required=False)
    rider = UserSerializer(allow_null=True, required=False)

    class Meta:
        model = Trip
        fields = ('id', 'nk', 'created', 'updated', 'pick_up_address', 'drop_off_address', 'status', 'driver',
                  'rider',)
        read_only_fields = ('id', 'nk', 'created', 'updated',)
```

**trip/apis.py**

```python
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group
from rest_framework import permissions, status, views, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .models import Trip
from .serializers import TripSerializer, PrivateUserSerializer


class SignUpView(views.APIView): ...


class LogInView(views.APIView): ...


class LogOutView(views.APIView): ...


class TripView(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'nk'
    lookup_url_kwarg = 'trip_nk'
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
```

**taxi/urls.py**

```python
from django.conf.urls import include, url
from trip.apis import SignUpView, LogInView, LogOutView

urlpatterns = [
    url(r'^api/sign_up/$', SignUpView.as_view(), name='sign_up'),
    url(r'^api/log_in/$', LogInView.as_view(), name='log_in'),
    url(r'^api/log_out/$', LogOutView.as_view(), name='log_out'),
    url(r'^api/trip/', include('trip.urls', namespace='trip')),
]
```

**trip/urls.py**

```python
from django.conf.urls import url
from .apis import TripView

urlpatterns = [
    url(r'^$', TripView.as_view({'get': 'list'}), name='trip_list'),
    url(r'^(?P<trip_nk>\w+)/$', TripView.as_view({'get': 'retrieve'}), name='trip_detail'),
]
```

```bash
$ curl -H "Authorization: Token 81ff6ef21b02f22435d9b97f06e4c36b3bc4bb81" http://localhost:8000/api/trip/

[]
```

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Trip


class UserSerializer(serializers.ModelSerializer): ...


class PrivateUserSerializer(serializers.ModelSerializer): ...


class TripSerializer(serializers.ModelSerializer):
    driver = UserSerializer(allow_null=True, required=False)
    rider = UserSerializer(allow_null=True, required=False)

    def create(self, validated_data):
        user_model = get_user_model()
        rider_data = validated_data.pop('rider', None)
        driver_data = validated_data.pop('driver', None)
        trip = Trip.objects.create(**validated_data)
        if rider_data:
            trip.rider = user_model.objects.get(**rider_data)
        if driver_data:
            trip.driver = user_model.objects.get(**driver_data)
        trip.save()
        return trip

    class Meta:
        model = Trip
        fields = ('id', 'nk', 'created', 'updated', 'pick_up_address', 'drop_off_address', 'status', 'driver',
                  'rider',)
        read_only_fields = ('id', 'nk', 'created', 'updated',)
```

**trip/consumers.py**

```python
from channels import Group
from channels.generic.websockets import JsonWebsocketConsumer
from .models import Trip
from .serializers import TripSerializer


class TripConsumer(JsonWebsocketConsumer):
    http_user_and_session = True

    def user_trips(self):
        return Trip.objects.none()

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


class RiderConsumer(TripConsumer):
    def user_trips(self):
        return self.message.user.trips_as_rider.exclude(status=Trip.COMPLETED)

    def receive(self, content, **kwargs):
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
```

**taxi/routing.py**

```python
from channels import route_class
from trip.consumers import RiderConsumer


channel_routing = [
    route_class(RiderConsumer, path=r'^/rider/$'),
]
```

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Trip


class UserSerializer(serializers.ModelSerializer): ...


class PrivateUserSerializer(serializers.ModelSerializer): ...


class TripSerializer(serializers.ModelSerializer):
    driver = UserSerializer(allow_null=True, required=False)
    rider = UserSerializer(allow_null=True, required=False)

    def create(self, validated_data): ...

    def update(self, instance, validated_data):
        user_model = get_user_model()
        rider_data = validated_data.pop('rider', None)
        if rider_data:
            instance.rider = user_model.objects.get(**rider_data)
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
                  'rider',)
        read_only_fields = ('id', 'nk', 'created', 'updated',)
```

**trip/consumers.py**

```python
from channels import Group
from channels.generic.websockets import JsonWebsocketConsumer
from .models import Trip
from .serializers import TripSerializer


class TripConsumer(JsonWebsocketConsumer): ...


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
    def user_trips(self): ...

    def receive(self, content, **kwargs):
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
```

**taxi/routing.py**

```python
from channels import route_class
from trip.consumers import DriverConsumer, RiderConsumer


channel_routing = [
    route_class(DriverConsumer, path=r'^/driver/$'),
    route_class(RiderConsumer, path=r'^/rider/$'),
]
```
