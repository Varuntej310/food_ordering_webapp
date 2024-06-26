from django.urls import path
from .views import (
    MenuList, CategoryList, MenuSearch,
    UserOrderList, Checkout,
    AddressList, CreateAddress, UserList,
    CartView, CartItemCreate, CartItemIncrementDecrement, CartItemDelete
)
from .views import (
    UserList, LoginView, SignupView, LogoutView, GetProfileView, BestsellerListView
)

urlpatterns = [
    path('menu/', MenuList.as_view()),
    path('categories/', CategoryList.as_view()),
    path('search/', MenuSearch.as_view()),
    path('orders/', UserOrderList.as_view()),
    path('checkout/', Checkout.as_view()),
    path('addresses/', AddressList.as_view()),
    path('address/create/', CreateAddress.as_view()),
    path('users/', UserList.as_view()),  
    path('cart/', CartView.as_view()),
    path('cart/add/', CartItemCreate.as_view(), name='cart-item-create'),
    path('cartitem/<int:pk>/', CartItemIncrementDecrement.as_view(), name='cartitem-increment-decrement'),
    path('cartitem/<int:pk>/delete/', CartItemDelete.as_view(), name='cartitem-delete'),
    path('users/', UserList.as_view()),
    path('login/', LoginView.as_view()),
    path('signup/', SignupView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('profile/', GetProfileView.as_view(), name='get-profile'),
    path('bestsellers/', BestsellerListView.as_view(), name='bestsellers'),
]

