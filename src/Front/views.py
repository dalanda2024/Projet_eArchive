from django.shortcuts import render

def index(request):
    return render(request, 'Front/index.html')

# def portfolio_details(request):
#     return render(request, 'Front/portfolio_details.html')

# def service_details(request):
#     return render(request, 'Front/service-details.html')

# def starter_page(request):
#     return render(request, 'Front/starter-page.html')
