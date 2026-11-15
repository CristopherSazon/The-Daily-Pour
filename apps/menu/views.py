from django.http import JsonResponse
from django.shortcuts import render

from .services import MenuService


def home(request):
    return render(request, 'menu/home.html', MenuService().home_context())


def menu_page(request):
    return render(
        request,
        'menu/menu.html',
        {'catalog_json': MenuService().catalog_document()},
    )


def menu(request):
    return JsonResponse(MenuService().menu_payload())
