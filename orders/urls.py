from django.urls import path
from . import views

urlpatterns = [
    path("placeorder/",views.place_order,name="place_order"),
    path("payments/",views.payments,name="payments"),
    path("order_complete/",views.order_complete,name="order_complete"),
]