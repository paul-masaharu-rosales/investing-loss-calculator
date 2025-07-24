from . import views
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),
    path('reset_db', views.reset_db, name="reset_db"),
]