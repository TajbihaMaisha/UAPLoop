from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import LoginForm, RegisterForm


def register_view(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Welcome to UAPLoop.')
        return redirect('browse')
    return render(request, 'accounts/form.html', {'form': form, 'title': 'Register', 'button': 'Register'})


def login_view(request):
    form = LoginForm(request, data=request.POST or None)
    if form.is_valid():
        login(request, form.get_user())
        next_url = request.GET.get('next', '')
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts=request.get_host()):
            return redirect(next_url)
        return redirect('browse')
    return render(request, 'accounts/form.html', {'form': form, 'title': 'Login', 'button': 'Login'})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('browse')


def unauthorized(request):
    return render(request, '401.html', {'next': request.GET.get('next', '')}, status=401)
