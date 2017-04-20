from django.shortcuts import render
from .models import Release
# from django.http import HttpResponse


def index(request):

    if request.method == 'GET':
        releases = Release.objects.filter(is_active=True).order_by('-released_at')[:200]

        return render(request, 'index.html', {'releases': releases})
