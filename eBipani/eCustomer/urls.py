from django.urls import path
from eCustomer import views

urlpatterns = [
    path('', views.index, name='index'),
    path('products/<category>/', views.productByCategory, name='productByCategory'),
    path('products/<category>/<pid>/', views.individualProduct, name='individualProduct'),
    path('profile/', views.profile, name='profile'),
    path('search/', views.searchProduct, name='searchProduct'),
    path('cart/', views.cart, name='cart'), 
    path('myorders/', views.myOrders, name='myOrders'),
    path('confirmOrder/<pid>/', views.preOrderDetails, name='preOrderDetails'),
]
