## Authentication

**taxi/settings.py**

```python
ALLOWED_HOSTS = ['*']

DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
]

LOCAL_APPS = [
    'trip',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    )
}
```

```bash
$ python manage.py migrate
```

**trip/tests.py**

```python
from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_201_CREATED
from rest_framework.test import APIClient, APITestCase
from .serializers import PublicUserSerializer

PASSWORD = 'pAssw0rd!'


class AuthenticationTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_can_sign_up(self):
        response = self.client.post(reverse('sign_up'), data={
            'username': 'user@example.com',
            'password1': PASSWORD,
            'password2': PASSWORD
        })
        user = get_user_model().objects.last()
        self.assertEqual(HTTP_201_CREATED, response.status_code)
        self.assertEqual(PublicUserSerializer(user).data, response.data)
```

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username',)
```

**trip/apis.py**

```python
from django.contrib.auth.forms import UserCreationForm
from rest_framework import status, views
from rest_framework.response import Response
from .serializers import PublicUserSerializer


class SignUpView(views.APIView):
    def post(self, *args, **kwargs):
        form = UserCreationForm(data=self.request.data)
        if form.is_valid():
            user = form.save()
            return Response(PublicUserSerializer(user).data, status=status.HTTP_201_CREATED)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
```

**taxi/urls.py**

```python
from django.conf.urls import url
from .apis import SignUpView

urlpatterns = [
    url(r'^api/sign_up/$', SignUpView.as_view(), name='sign_up'),
]
```

**trip/tests.py**

```python
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.test import APITestCase
from .serializers import PrivateUserSerializer


def create_user(username='user@example.com', password=PASSWORD):
    return get_user_model().objects.create_user(username=username, password=password)


class AuthenticationTest(APITestCase):
    def test_user_can_log_in(self):
        user = create_user()
        response = self.client.post(reverse('log_in'), data={
            'username': user.username,
            'password': PASSWORD,
        })
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(PrivateUserSerializer(user).data, response.data)
        self.assertIsNotNone(Token.objects.get(user=user))

    def test_user_can_log_out(self):
        user = create_user()
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        self.client.login(username=user.username, password=self.password)
        response = self.client.post(reverse('log_out'))
        self.assertEqual(HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(Token.objects.filter(user=user).exists())
```

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers


class PrivateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'auth_token',)
```

**trip/apis.py**

```python
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from rest_framework import permissions, status, views
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .serializers import PrivateUserSerializer


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
        logout(self.request)
        Token.objects.get(user=self.request.user).delete()
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

## HTTP

**trip/tests.py**

```python
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient, APITestCase
from .models import Trip
from .serializers import TripSerializer


class HttpTripTest(APITestCase):
    def setUp(self):
        user = create_user()
        token = Token.objects.create(user=user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_user_can_list_trips(self):
        trips = [
            Trip.objects.create(pick_up_address='A', drop_off_address='B'),
            Trip.objects.create(pick_up_address='B', drop_off_address='C')
        ]
        response = self.client.get(reverse('trip:trip_list'))
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(TripSerializer(trips, many=True).data, response.data)
```

**trip/models.py**

```python
import datetime
import hashlib
from django.db import models
from django.shortcuts import reverse


class Trip(models.Model):
    REQUESTED = 'REQUESTED'
    STARTED = 'STARTED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    STATUSES = (
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
    status = models.CharField(max_length=20, choices=STATUSES, default=REQUESTED)

    def __str__(self):
        return self.nk

    def get_absolute_url(self):
        return reverse('trip:trip_detail', kwargs={'trip_nk': self.nk})

    def save(self, **kwargs):
        if not self.nk:
            now = datetime.datetime.now()
            secure_hash = hashlib.md5()
            secure_hash.update(f'{now}:{self.pick_up_address}:{self.drop_off_address}'.encode('utf-8'))
            self.nk = secure_hash.hexdigest()
        super().save(**kwargs)
```

```bash
$ python manage.py makemigrations
$ python manage.py migrate
```

**trip/serializers.py**

```python
from rest_framework import serializers
from .models import Trip


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = '__all__'
        read_only_fields = ('id', 'nk', 'created', 'updated',)
```

**trip/apis.py**

```python
from rest_framework import permissions, viewsets
from .models import Trip
from .serializers import TripSerializer


class TripView(viewsets.ReadOnlyModelViewSet):
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
]
```

**trip/tests.py**

```python
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase
from .models import Trip
from .serializers import TripSerializer


class HttpTripTest(APITestCase):
    def test_user_can_retrieve_trip_by_nk(self):
        trip = Trip.objects.create(pick_up_address='A', drop_off_address='B')
        response = self.client.get(trip.get_absolute_url())
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(TripSerializer(trip).data, response.data)
```

**trip/apis.py**

```python
from rest_framework import permissions, viewsets
from .models import Trip
from .serializers import TripSerializer


class TripView(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'nk'
    lookup_url_kwarg = 'trip_nk'
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
```

**trip/urls.py**

```python
from django.conf.urls import url
from .apis import TripView

urlpatterns = [
    url(r'^$', TripView.as_view({'get': 'list'}), name='trip_list'),
    url(r'^(?P<trip_nk>\w{32})/$', TripView.as_view({'get': 'retrieve'}), name='trip_detail'),
]
```

## WebSockets

**taxi/settings.py**

```python
THIRD_PARTY_APPS = [
    'channels',
    'rest_framework',
    'rest_framework.authtoken',
]

WSGI_APPLICATION = 'taxi.asgi.application'

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'asgi_redis.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
        'ROUTING': 'taxi.routing.channel_routing',
    },
}
```

**taxi/asgi.py**

```python
import os
from channels import asgi

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi.settings')

channel_layer = asgi.get_channel_layer()
```

**taxi/routing.py**

```python
channel_routing = []
```

**trip/tests.py**

```python
from django.contrib.auth import get_user_model
from channels.test import ChannelTestCase, HttpClient


class WebSocketTripTest(ChannelTestCase):
    def setUp(self):
        self.driver = create_user('driver@example.com')
        self.rider = create_user('rider@example.com')

    def connect_as_driver(self, driver):
        client = HttpClient()
        client.login(username=driver.username, password=PASSWORD)
        client.send_and_consume('websocket.connect', path='/driver/')
        return client

    def connect_as_rider(self, rider):
        client = HttpClient()
        client.login(username=rider.username, password=PASSWORD)
        client.send_and_consume('websocket.connect', path='/rider/')
        return client

    def test_driver_can_connect_via_websockets(self):
        client = self.connect_as_driver(self.driver)
        message = client.receive()
        self.assertIsNone(message)

    def test_rider_can_connect_via_websockets(self):
        client = self.connect_as_rider(self.rider)
        message = client.receive()
        self.assertIsNone(message)
```

**trip/models.py**

```python
from django.conf import settings


class Trip(models.Model):
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='trips_as_driver')
    rider = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='trips_as_rider')
```

```bash
$ python manage.py makemigrations
$ python manage.py migrate
```

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username',)
        read_only_fields = ('username',)


class PrivateUserSerializer(PublicUserSerializer):
    class Meta(PublicUserSerializer.Meta):
        fields = list(PublicUserSerializer.Meta.fields) + ['auth_token']


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
```

**trip/consumers.py**

```python
from channels.generic.websockets import JsonWebsocketConsumer


class TripConsumer(JsonWebsocketConsumer):
    def connect(self, message, **kwargs):
        self.message.reply_channel.send({'accept': True})


class DriverConsumer(TripConsumer):
    pass


class RiderConsumer(TripConsumer):
    pass
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

**trip/tests.py**

```python
from channels.test import ChannelTestCase
from .models import Trip
from .serializers import TripSerializer


class WebSocketTripTest(ChannelTestCase):
    def test_rider_can_create_trips(self):
        client = self.connect_as_rider(self.rider)
        client.send_and_consume('websocket.receive', path='/rider/', content={
            'text': {
                'pick_up_address': 'A',
                'drop_off_address': 'B',
                'rider': PublicUserSerializer(self.rider).data
            }
        }})
        message = client.receive()
        trip = Trip.objects.last()
        self.assertEqual(TripSerializer(trip).data, message)
```

**trip/consumers.py**

```python
from channels.generic.websockets import JsonWebsocketConsumer
from .serializers import TripSerializer


class RiderConsumer(TripConsumer):
    def receive(self, content, **kwargs):
        serializer = TripSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        trip = serializer.create(serializer.validated_data)
        self.send(content=TripSerializer(trip).data)
```

**trip/tests.py**

```python
from channels.test import ChannelTestCase
from .models import Trip
from .serializers import PublicUserSerializer, TripSerializer


class WebSocketTripTest(ChannelTestCase):
    def create_trip(self, rider, pick_up_address='A', drop_off_address='B'):
        client = self.connect_as_rider(rider)
        client.send_and_consume('websocket.receive', path='/rider/', content={
            'text': {
                'pick_up_address': pick_up_address,
                'drop_off_address': drop_off_address,
                'rider': PublicUserSerializer(rider).data
            }
        })
        return client

    def test_rider_can_create_trips(self):
        client = self.create_trip(self.rider)
        message = client.receive()
        trip = Trip.objects.last()
        self.assertEqual(TripSerializer(trip).data, message)

    def test_rider_is_subscribed_to_trip_channel_on_creation(self):
        client = self.create_trip(self.rider)
        client.receive()
        trip = Trip.objects.last()
        message = {'detail': 'This is a test message.'}
        Group(trip.nk).send(message)
        self.assertEqual(message, client.receive())
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


class RiderConsumer(TripConsumer):
    def user_trips(self):
        return self.message.user.trips_as_rider.exclude(status=Trip.COMPLETED)

    def receive(self, content, **kwargs):
        serializer = TripSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        trip = serializer.create(serializer.validated_data)
        self.message.channel_session['trip_nks'].append(trip.nk)
        Group(trip.nk).add(self.message.reply_channel)
        trips_data = TripSerializer(trip).data
        self.group_send(name=trip.nk, content=trips_data)
```

**trip/tests.py**

```python
from django.contrib.auth import get_user_model
from channels.test import ChannelTestCase
from .models import Trip
from .serializers import TripSerializer


class WebSocketTripTest(ChannelTestCase):
    def update_trip(self, driver, status):
        client = self.connect_as_driver(driver)
        client.send_and_consume('websocket.receive', path='/driver/', content={
            'text': {
                'nk': trip.nk,
                'pick_up_address': trip.pick_up_address,
                'drop_off_address': trip.drop_off_address,
                'status': status,
                'driver': UserSerializer(driver).data
            }
        })
        return client

    def test_driver_can_update_trips(self):
        trip = Trip.objects.create(pick_up_address='A', drop_off_address='B')
        client = self.update_trip(self.driver, trip=trip, status=Trip.STARTED)
        trip = Trip.objects.get(nk=trip.nk)
        self.assertEqual(TripSerializer(trip).data, client.receive())

    def test_driver_is_subscribed_to_trip_channel_on_update(self):
        trip = Trip.objects.create(pick_up_address='A', drop_off_address='B')
        client = self.update_trip(self.driver, trip=trip, status=Trip.STARTED)
        client.receive()
        trip = Trip.objects.last()
        message = {'detail': 'This is a test message.'}
        Group(trip.nk).send(message)
        self.assertEqual(message, client.receive())
```

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers


class TripSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        driver_data = validated_data.pop('driver', None)
        if driver_data:
            instance.driver = get_user_model().objects.get(**driver_data)
        rider_data = validated_data.pop('rider', None)
        if rider_data:
            instance.rider = get_user_model().objects.get(**rider_data)
        instance = super().update(instance, validated_data)
        return instance
```

**trip/consumers.py**

```python
from channels import Group
from .models import Trip
from .serializers import TripSerializer


class DriverConsumer(TripConsumer):
    groups = ['drivers']

    def user_trips(self):
        return self.message.user.trips_as_driver.exclude(status=Trip.COMPLETED)

    def connect(self, message, **kwargs):
        super().connect(message, **kwargs)
        Group('drivers').add(self.message.reply_channel)

    def receive(self, content, **kwargs):
        trip = Trip.objects.get(nk=content.get('nk'))
        serializer = TripSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        trip = serializer.update(trip, serializer.validated_data)
        self.message.channel_session['trip_nks'].append(trip.nk)
        Group(trip.nk).add(self.message.reply_channel)
        trips_data = TripSerializer(trip).data
        self.group_send(name=trip.nk, content=trips_data)
```

**trip/tests.py**

```python
from channels.test import ChannelTestCase
from .models import Trip
from .serializers import TripSerializer


class WebSocketTripTest(ChannelTestCase):
    def test_driver_is_alerted_on_trip_creation(self):
        client = self.connect_as_driver(self.driver)
        self.create_trip(self.rider)
        trip = Trip.objects.last()
        self.assertEqual(TripSerializer(trip).data, client.receive())

    def test_rider_is_alerted_on_trip_update(self):
        client = self.create_trip(self.rider)
        client.receive()
        trip = Trip.objects.last()
        self.update_trip(self.driver, trip=trip, status=Trip.STARTED)
        trip = Trip.objects.get(nk=trip.nk)
        self.assertEqual(TripSerializer(trip).data, client.receive())
```

**trip/consumers.py**

```python
from channels import Group
from .serializers import TripSerializer


class RiderConsumer(TripConsumer):
    def receive(self, content, **kwargs):
        serializer = TripSerializer(data=content)
        serializer.is_valid(raise_exception=True)
        trip = serializer.create(serializer.validated_data)
        self.message.channel_session['trip_nks'].append(trip.nk)
        Group(trip.nk).add(self.message.reply_channel)
        trips_data = TripSerializer(trip).data
        self.group_send(name=trip.nk, content=trips_data)
        self.group_send(name='drivers', content=trips_data)
```

**trip/serializers.py**

```python
from django.contrib.auth import get_user_model
from rest_framework import serializers


class PublicUserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'groups',)
        read_only_fields = ('username',)
```

**trip/apis.py**

```python
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from rest_framework import status, views
from rest_framework.response import Response
from .serializers import PublicUserSerializer


class SignUpView(views.APIView):
    def post(self, *args, **kwargs):
        group = self.request.data.pop('group', 'rider')
        user_group, _ = Group.objects.get_or_create(name=group)
        form = UserCreationForm(data=self.request.data)
        if form.is_valid():
            user = form.save()
            user.groups.add(user_group)
            user.save()
            return Response(PublicUserSerializer(user).data, status=status.HTTP_201_CREATED)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
```








## Rider Commands

```bash
$ curl -H "Content-Type: application/json" -X POST -d '{"username": "rider@example.com", "password1": "pAssw0rd!", "password2": "pAssw0rd!", "group": "rider"}' http://localhost:8000/api/sign_up/

{"id":1,"username":"rider@example.com","auth_token":null,"groups":["rider"]}
```

```bash
$ curl -H "Content-Type: application/json" -X POST -d '{"username": "rider@example.com", "password": "pAssw0rd!"}' http://localhost:8000/api/log_in/

{"id":1,"username":"rider@example.com","auth_token":81ff6ef21b02f22435d9b97f06e4c36b3bc4bb81,"groups":["rider"]}
```

```bash
$ curl -H "Authorization: Token 81ff6ef21b02f22435d9b97f06e4c36b3bc4bb81" -X POST http://localhost:8000/api/log_out/
```

```bash
$ wscat -H "Content-Type: application/json; Authorization: Token 81ff6ef21b02f22435d9b97f06e4c36b3bc4bb81" -c ws://localhost:8000/rider/ --parsecommands
```

```bash
> send '{"text":{"pick_up_address":"A","drop_off_address":"B","rider":{"id":3,"username":"rider@example.com"}}}'
```

## Driver Commands

```bash
$ curl -H "Content-Type: application/json" -X POST -d '{"username": "driver@example.com", "password1": "pAssw0rd!", "password2": "pAssw0rd!", "group": "driver"}' http://localhost:8000/api/sign_up/

{"id":1,"username":"driver@example.com","auth_token":null,"groups":["driver"]}
```

```bash
$ curl -H "Content-Type: application/json" -X POST -d '{"username": "driver@example.com", "password": "pAssw0rd!"}' http://localhost:8000/api/log_in/

{"id":1,"username":"driver@example.com","auth_token":43841bb28794f6b433b5c95df9ff879d104a2b6f,"groups":["driver"]}
```

```bash
$ curl -H "Authorization: Token 43841bb28794f6b433b5c95df9ff879d104a2b6f" -X POST http://localhost:8000/api/log_out/
```

## Universal Commands

```bash
$ curl -H "Authorization: Token 81ff6ef21b02f22435d9b97f06e4c36b3bc4bb81" http://localhost:8000/api/trip/

[]
```

```bash
$ curl -H "Authorization: Token 81ff6ef21b02f22435d9b97f06e4c36b3bc4bb81" http://localhost:8000/api/trip/something/

[]
```
