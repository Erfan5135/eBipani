from django.urls import path
from eSeller import views

urlpatterns = [
    path('', views.index, name='index'),
    path('products/', views.allProducts, name='allProducts'),
    path('profile/', views.profile, name='profile'),
    path('addProducts/', views.addProducts, name='addProducts'),
    path('products/sellerEditProducts', views.editProducts, name='editProducts'),
    path('products/editProductFunc', views.editProductFunc, name='editProductfunc'),
    path('sellerOrders/', views.sellerOrders, name='sellerOrders'),
    path('addProducts/addProductfunc',views.addProductfunc, name='addProductfunc'),
]
