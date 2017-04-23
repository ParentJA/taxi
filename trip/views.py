# Django imports.
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect

# Local imports.
from .models import Trip


def sign_up(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            # user.groups.add()
            return redirect(reverse('trip:log_in'))
        else:
            print(form.errors)
    return render(request, 'trip/sign_up.html', {'form': form})


def log_in(request):
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(reverse('trip:user_list'))
        else:
            print(form.errors)
    return render(request, 'trip/log_in.html', {'form': form})


def log_out(request):
    logout(request)
    return redirect(reverse('trip:log_in'))


def new_trip(request):
    trip = Trip.objects.create()
