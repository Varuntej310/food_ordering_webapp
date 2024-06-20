from django.urls import path
from .views import (
    MenuList, CategoryList, MenuSearch,
    UserOrderList, CreateOrder,
    AddressList, CreateAddress, UserList,
    CartView, CartItemCreateUpdate, CartItemIncrementDecrement, CartItemDelete
)

urlpatterns = [
    path('menu/', MenuList.as_view()),
    path('categories/', CategoryList.as_view()),
    path('search/', MenuSearch.as_view()),
    path('orders/', UserOrderList.as_view()),
    path('orders/create/', CreateOrder.as_view()),
    path('addresses/', AddressList.as_view()),
    path('addresses/create/', CreateAddress.as_view()),
    path('users/', UserList.as_view()),  
    path('cart/', CartView.as_view()),
    path('cartitem/', CartItemCreateUpdate.as_view(), name='cartitem-create-update'),
    path('cartitem/<int:pk>/', CartItemIncrementDecrement.as_view(), name='cartitem-increment-decrement'),
    path('cartitem/<int:pk>/delete/', CartItemDelete.as_view(), name='cartitem-delete'),
]

