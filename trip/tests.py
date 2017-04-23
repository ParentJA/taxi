# Standard library imports.
import hashlib

# Django imports.
from django.contrib.auth import get_user_model
from django.shortcuts import reverse

# Third-party imports.
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


class AuthenticationTest(APITestCase):
    def setUp(self):
        self.password = create_password()

    def log_in(self, username, password):
        response = self.client.post(reverse('log_in'), data={
            'username': username,
            'password': password,
        })
        return response.data['auth_token']

    def test_can_sign_up(self):
        # curl -H "Content-Type: application/json" -X POST -d '{"username": "user@example.com", "password1": "pAssw0rd!", "password2": "pAssw0rd!"}' http://localhost:8000/api/sign_up/
        response = self.client.post(reverse('sign_up'), data={
            'username': 'user@example.com',
            'password1': self.password,
            'password2': self.password,
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
        self.log_in(user.username, password=self.password)
        response = self.client.post(reverse('log_out'))
        self.assertEqual(HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(0, Token.objects.count())


class TripTest(APITestCase):
    def setUp(self):
        self.password = create_password()
        self.user1 = create_user(email='user1@example.com')
        self.user2 = create_user(email='user2@example.com')
        self.user3 = create_user(email='user3@example.com')
        self.token = self.log_in(username=self.user1.username, password=self.password)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token {token}'.format(token=self.token))

    def log_in(self, username, password):
        response = self.client.post(reverse('log_in'), data={
            'username': username,
            'password': password,
        })
        return response.data['auth_token']

    def test_can_list_users(self):
        response = self.client.get(reverse('trip:user_list'))
        self.assertEqual(UserSerializer([self.user2, self.user3], many=True).data,
                         response.data)

    def test_can_create_trip(self):
        response = self.client.post(reverse('trip:trip_list'), data={
            'pick_up_address': '310 P Street NW',
            'drop_off_address': '2445 M Street NW',
            'driver': None,
            'riders': UserSerializer([self.user1, self.user2, self.user3], many=True).data,
        }, format='json')
        self.assertEqual(HTTP_201_CREATED, response.status_code)
        self.assertEqual('310 P Street NW', response.data.get('pick_up_address'))
        self.assertEqual('2445 M Street NW', response.data.get('drop_off_address'))
        self.assertEqual(Trip.REQUESTED, response.data.get('status'))
        self.assertEqual(UserSerializer([self.user1, self.user2, self.user3], many=True).data,
                         response.data.get('riders'))

    def test_can_list_trips(self):
        trip = Trip.objects.create()
        trip.riders.add(self.user2)
        trip.riders.add(self.user3)
        trip.save()
        response = self.client.get(reverse('trip:trip_list'), format='json')
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(TripSerializer([trip], many=True).data, response.data)

    def test_can_list_completed_trips(self):
        Trip.objects.create(status=Trip.REQUESTED)
        Trip.objects.create(status=Trip.STARTED)
        Trip.objects.create(status=Trip.IN_PROGRESS)
        Trip.objects.create(status=Trip.COMPLETED)
        response = self.client.get(reverse('trip:trip_list'), data={'status': Trip.COMPLETED}, format='json')
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(TripSerializer(Trip.objects.filter(status=Trip.COMPLETED), many=True).data, response.data)

    def test_can_retrieve_trip(self):
        trip = Trip.objects.create()
        trip.riders.add(self.user1)
        trip.riders.add(self.user2)
        trip.riders.add(self.user3)
        trip.save()
        response = self.client.get(trip.get_absolute_url(), format='json')
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(TripSerializer([trip], many=True).data, response.data)

    def test_can_update_trip(self):
        trip = Trip.objects.create()
        trip.riders.add(self.user1)
        trip.save()
        response = self.client.put(trip.get_absolute_url(), data={
            'riders': UserSerializer([self.user2, self.user3], many=True).data
        }, format='json')
        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(3, len(trip.riders.all()))
