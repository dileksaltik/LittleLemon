from django.urls import path, include
from .views import MenuItemListCreateAPIView, SingleMenuItemRetrieveUpdateDestroyAPIView, CustomUserViewSet, CartItemsAPIView, CategoryListCreateAPIView
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
#router.register(r'cart/menu-items', CartItemViewSet, basename='cart-menu-item')


urlpatterns = [
    path('', include(router.urls)),
    path('menu-items/<int:pk>/', SingleMenuItemRetrieveUpdateDestroyAPIView.as_view(), name='singlemenuitem-retrieve-update-destroy'),  
    path('menu-items/', MenuItemListCreateAPIView.as_view(), name='menuitem-list-create'), 
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'), 
    path('groups/manager/users/', views.ManagerUser, name='groups-manager-user-list-create'), 
    path('groups/manager/users/<int:pk>/', views.ManagerUserRemove, name='groups-manager-user-delete'), 
    path('groups/delivery-crew/users/', views.DeliveryCrewUser, name='groups-deliverycrew-user-list-create'),    
    path('groups/delivery-crew/users/<int:pk>/', views.DeliveryCrewUserRemove, name='groups-deliverycrew-user-delete'),    
    path('users/', CustomUserViewSet.as_view({'post': 'create', 'get':'list'}), name='custom-user-create'),  
    path('users/users/me/', views.Me, name='custom-user-getusername'), 
    path('token/login/', views.TokenCreateView.as_view(), name='token-create'), 
    path('auth-token/', obtain_auth_token, name='auth-token'),
    path('cart/menu-items/', CartItemsAPIView.as_view(), name='cart-items'),
    path('orders/', views.OrderListCreate, name='order-list-create'),
    path('cart/orders/', views.OrderListCreate, name='order-list-create'),
    path('orders/<int:orderId>/', views.OrderDetail, name='singleorderitem-retrieve-update-destroy'),  
 
]