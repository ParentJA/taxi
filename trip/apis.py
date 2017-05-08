from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group
from rest_framework import permissions, status, views, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .models import Trip
from .serializers import TripSerializer, PrivateUserSerializer


class SignUpView(views.APIView):
    def post(self):
        group = self.request.data.get('group', 'rider')
        user_group, _ = Group.objects.get_or_create(name=group)
        form = UserCreationForm(data=self.request.data)
        if form.is_valid():
            user = form.save()
            user.groups.add(user_group)
            user.save()
            return Response(PrivateUserSerializer(user).data, status=status.HTTP_201_CREATED)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class LogInView(views.APIView):
    def post(self):
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

    def post(self):
        Token.objects.get(user=self.request.user).delete()
        logout(self.request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TripView(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'nk'
    lookup_url_kwarg = 'trip_nk'
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
