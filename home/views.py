from django.shortcuts import render


# Create your views here.
def index(request):
    template_data = {}
    template_data["title"] = "FitHub"
    return render(request, "home/index.html", {"template_data": template_data})


def about(request):
    return render(request, "home/about.html")
