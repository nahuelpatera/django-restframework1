from django.urls import path
from e_commerce.api.hello_world_api import *
from e_commerce.api.marvel_api_views import *

urlpatterns = [
    path('hola_mundo_1/',hello_world_api_1),
    path('hola_mundo_2/',hello_world_api_2),
    path('hola_mundo_3/',hello_world_api_3),
    path('request-data/',return_request_data),
    path('get-comics/',get_comics),
    path('purchased-item/',purchased_item),
]
 