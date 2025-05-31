from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('portfolio/', views.portfolio_details, name='portfolio_details'),
    # path('services/', views.service_details, name='service_details'),
    # path('starter/', views.starter_page, name='starter_page'),
]
