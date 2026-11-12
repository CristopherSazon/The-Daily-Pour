from django.http import JsonResponse
from django.shortcuts import render

from .services import MenuService


def home(request):
    return render(request, 'pours/home.html', MenuService().home_context())


def menu(request):
    return JsonResponse(MenuService().menu_payload())
