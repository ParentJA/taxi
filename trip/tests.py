# Standard library imports.
import hashlib

# Django imports.
from django.contrib.auth import get_user_model
from django.shortcuts import reverse

# Third-party imports.
from channels import Group
from channels.test import ChannelTestCase, HttpClient
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT

# Local imports.
from .models import Trip
from .serializers import TripSerializer, UserSerializer


def create_password():
    secure_hash = hashlib.md5()
    secure_hash.update('password'.encode('utf-8'))
    return secure_hash.hexdigest()


def create_user(email):
    return get_user_model().objects.create_user(username=email, email=email, password=create_password())


def log_in(client, username, password):
    response = client.post(reverse('log_in'), data={
        'username': username,
        'password': password,
    })
    return response.data['auth_token']


class AuthenticationTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = create_password()

    def test_can_sign_up(self):
        # curl -H "Content-Type: application/json" -X POST -d '{"username": "user@example.com", "password1": "pAssw0rd!", "password2": "pAssw0rd!"}' http://localhost:8000/api/sign_up/
        response = self.client.post(reverse('sign_up'), data={
            'username': 'user@example.com',
            'email': 'user@example.com',
            'password1': self.password,
            'password2': self.password,
            'group': 'rider',
        })
        self.assertEqual(HTTP_201_CREATED, response.status_code)
        self.assertEqual(0, Token.objects.count())
        self.assertEqual('user@example.com', response.data['username'])

    def test_can_log_in(self):
        # curl -H "Content-Type: application/json" -X POST -d '{"username": "user@example.com", "password": "pAssw0rd!"}' http://localhost:8000/api/log_in/
        user = create_user('user@example.com')
        response = self.client.post(reverse('log_in'), data={
            'username': 'user@example.com',
            'password': self.password,
        })
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(1, Token.objects.count())
        self.assertEqual(user.username, response.data['username'])

    def log_out(self):
        # curl -H "Authorization: Token e4195ef7a0aa819a63dae152a27dec32cc0afaf8" -X POST http://localhost:8000/api/log_out/
        user = create_user('user@example.com')
        log_in(self.client, username=user.username, password=self.password)
        response = self.client.post(reverse('log_out'))
        self.assertEqual(HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(0, Token.objects.count())


class TripTest(APITestCase):
    def setUp(self):
        self.password = create_password()
        self.user1 = create_user(email='user1@example.com')
        self.user2 = create_user(email='user2@example.com')
        self.user3 = create_user(email='user3@example.com')
        self.token = log_in(self.client, username=self.user1.username, password=self.password)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token {token}'.format(token=self.token))

    def test_can_list_trips(self):
        trip = Trip.objects.create(rider=self.user1)
        response = self.client.get(reverse('trip:trip_list'), format='json')
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(TripSerializer([trip], many=True).data, response.data)

    def test_can_retrieve_trip(self):
        trip = Trip.objects.create(rider=self.user1)
        response = self.client.get(trip.get_absolute_url(), format='json')
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(TripSerializer(trip).data, response.data)


class WebSocketTripTest(ChannelTestCase):
    def setUp(self):
        self.password = create_password()
        self.driver = create_user(email='driver@example.com')
        self.rider = create_user(email='rider@example.com')
        self.trip_as_rider = {
            'pick_up_address': 'A',
            'drop_off_address': 'B'
        }

    def connect_as_driver(self, driver):
        client = HttpClient()
        client.login(username=driver.username, password=create_password())
        client.send_and_consume('websocket.connect', path='/driver/')
        return client

    def connect_as_rider(self, rider):
        client = HttpClient()
        client.login(username=rider.username, password=create_password())
        client.send_and_consume('websocket.connect', path='/rider/')
        return client

    def create_trip_as_rider(self, rider, **kwargs):
        kwargs.update({'rider': UserSerializer(rider).data})
        client = self.connect_as_rider(rider)
        client.send_and_consume('websocket.receive', path='/rider/', content={'text': kwargs})
        return client

    def update_trip_as_driver(self, driver, trip, **kwargs):
        trip.driver = driver
        for k, v in kwargs.items():
            setattr(trip, k, v)
        client = self.connect_as_driver(driver)
        client.send_and_consume('websocket.receive', path='/driver/', content={'text': TripSerializer(trip).data})
        return client

    def test_rider_can_create_trip(self):
        client = self.create_trip_as_rider(self.rider, **self.trip_as_rider)
        trip = Trip.objects.last()
        self.assertEqual(TripSerializer(trip).data, client.receive())

    def test_rider_is_subscribed_to_trip_channel(self):
        client = self.create_trip_as_rider(self.rider, **self.trip_as_rider)
        client.receive()
        trip = Trip.objects.last()
        message = {'message': 'test'}
        Group(trip.nk).send(message)
        self.assertEqual(message, client.receive())

    def test_rider_is_not_subscribed_to_other_trip_channel(self):
        trip = Trip.objects.create(pick_up_address='B', drop_off_address='C')
        client = self.create_trip_as_rider(self.rider, **self.trip_as_rider)
        client.receive()
        message = {'message': 'test'}
        Group(trip.nk).send(message)
        self.assertIsNone(client.receive())

    def test_driver_is_alerted_on_trip_creation(self):
        client = self.connect_as_driver(self.driver)
        self.create_trip_as_rider(self.rider, **self.trip_as_rider)
        trip = Trip.objects.last()
        self.assertEqual(TripSerializer(trip).data, client.receive())

    def test_driver_can_update_trip(self):
        trip = Trip.objects.create(pick_up_address='A', drop_off_address='B', status=Trip.REQUESTED)
        client = self.update_trip_as_driver(self.driver, trip=trip, **{'status': Trip.STARTED})
        self.assertEqual(Trip.STARTED, client.receive().get('status'))

    def test_driver_is_subscribed_to_trip_channel(self):
        trip = Trip.objects.create(pick_up_address='A', drop_off_address='B', status=Trip.REQUESTED)
        client = self.update_trip_as_driver(self.driver, trip=trip, **{'status': Trip.STARTED})
        client.receive()
        message = {'message': 'test'}
        Group(trip.nk).send(message)
        self.assertEqual(message, client.receive())

    def test_rider_is_alerted_on_trip_update(self):
        client = self.create_trip_as_rider(self.rider, **self.trip_as_rider)
        client.receive()
        trip = Trip.objects.last()
        trip.status = Trip.STARTED
        self.update_trip_as_driver(self.driver, trip=trip, **{'status': Trip.STARTED})
        self.assertEqual(Trip.STARTED, client.receive().get('status'))
