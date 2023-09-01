from rest_framework import generics, permissions, status, viewsets, mixins
from django.contrib.auth.models import Group, User
from django.contrib.auth import get_user_model
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import  CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from djoser.views import UserViewSet, TokenCreateView
from djoser.serializers import UserSerializer
from rest_framework.pagination import PageNumberPagination

 
class IsManagerOrReadOnly(permissions.BasePermission):
    message = "You must have the Manager role to perform this action."

    def has_permission(self, request, view):
        if request.method == 'GET':
            return request.user.is_authenticated
        else:
            return request.user.is_authenticated and request.user.groups.filter(name='Manager').exists() 
class IsAdminOrManagerOrReadOnly(permissions.BasePermission):
    message = "You must have the Admin or Manager role to perform this action."
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user.is_authenticated
        return request.user.is_authenticated and (request.user.is_superuser or request.user.groups.filter(name='Manager').exists())
class IsAdminOrReadOnly(permissions.BasePermission):
    message = "You must have the Admin role to perform this action."
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_superuser 

class IsManager(permissions.BasePermission):
    message = "You must have the Manager role to perform this action."

    def has_permission(self, request, view): 
        return request.user.is_authenticated  and request.user.groups.filter(name='Manager').exists()  
class MenuItemListCreateAPIView(generics.ListCreateAPIView):
     
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly] 
    def get_queryset(self):
        category_id = self.request.query_params.get('category_id')  # Get the category ID from query parameters
        ordering_fields=['price']  # Get the sort by price parameter
        search_query = self.request.query_params.get('search')  # Get the search for title field
        perpage = self.request.query_params.get('perpage', default=3)  # Get the perpage number of items by perpage parameter
        page = self.request.query_params.get('page', default=1)  # Get the current page number by page parameter
        
        
        queryset = MenuItem.objects.all()

        if category_id:
            queryset = queryset.filter(category_id=category_id)
    
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)
             
        
        return queryset
class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
class SingleMenuItemRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly] 
class CustomUserViewSet(UserViewSet):
    permission_classes = [permissions.AllowAny]
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        # Add 'userid' field to each user in the response
        data = serializer.data
        for i, user_data in enumerate(data):
            user_data['userid'] = queryset[i].id
        return Response(data)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers) 
class CartItemsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        cart_items = Cart.objects.filter(user=user)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        serializer = CartSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        user = request.user
        Cart.objects.filter(user=user).delete()
        return Response(status=204)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated]) 
def OrderListCreate(request):
    # Get the current user
    user = request.user

    if request.method == 'GET':
        # Check the role of the user
        if user.groups.filter(name='Manager').exists():
            # Manager role, retrieve all orders with items
            orders = Order.objects.all()
             
        elif user.groups.filter(name='Delivery crew').exists():
            # Delivery crew role, retrieve orders assigned to the user with items
            orders = Order.objects.filter(delivery_crew=user)
            
        else:
            # Customer role, retrieve orders created by the user with items
            orders = Order.objects.filter(user=user)
         
        ordering = request.query_params.get('ordering') 
        
        if ordering:
            ordering_fields = ordering.split(",")
            orders = orders.order_by(*ordering_fields)
         

        # Serialize the request
        serializer = OrderSerializer(orders, many=True)
 
        return Response(serializer.data)

    if request.method == 'POST':
        # Get the cart items for the current user
        cart_items = Cart.objects.filter(user=user)
        if not cart_items:
            return Response({'message':'There is no cart related to this user!'} , status=status.HTTP_404_NOT_FOUND)
            
        # Create a new order
        order = Order.objects.create(user=user, status=False, total=0)

        # Iterate through the cart items and add them to the order items
        order_items = []
        total_price = 0
        for cart_item in cart_items:
            menuitem = MenuItem.objects.get(pk=cart_item.menuitem.pk)
            order_item = OrderItem.objects.create(
                order=order,
                menuitem=menuitem,
                quantity=cart_item.quantity,
                unit_price=cart_item.menuitem.price,
                price=cart_item.price
            )
            order_items.append(order_item)
            total_price += cart_item.price

        # Set the total price for the order
        order.total = total_price
        order.date = request.data['date']
        order.save()

        # Delete all items from the cart for this user
        cart_items.delete()

        # Serialize the order and order items
        serializer = OrderSerializer(order)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def OrderDetail(request, orderId):
    # Get the current user
    user = request.user

    # Retrieve the order by orderId
    order = get_object_or_404(Order, id=orderId)

    if request.method == 'GET':
        # Check if the order belongs to the current user
        if order.user != user:
            return Response({'message': 'This order does not belong to the current user.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = OrderSerializer(order)
        return Response(serializer.data)


    if request.method == 'PUT' or request.method == 'PATCH':
        
        # Manager can update delivery crew and status
        # Delivery Crew can update the status into 1 if assigned delivery_crew is himself.
        # Customer can update if delivery_crew did not assign to order yet. 
        serializer = OrderSerializer(order, data=request.data, partial=True, context={'request': request})
  
        if serializer.is_valid():
            serializer.save()                 
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    if request.method == 'DELETE':
        # Check if the user has the Manager role
        if user.groups.filter(name='Manager').exists():
            # Manager can delete the order
            order.delete()
            return Response({'message': 'Order deleted.'}, status=status.HTTP_204_NO_CONTENT)

        # Customer and Delivery crew are not allowed to delete the order
        return Response({'message': 'You are not allowed to delete this order.'}, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET', 'POST'])
@permission_classes([IsManager])
def DeliveryCrewUser(request):
    
    if request.method == "GET":
        deliverycrews = Group.objects.get(name="Delivery crew")
        deliverycrew_usernames = deliverycrews.user_set.values_list('username', flat=True)
        return Response({"delivery crews": deliverycrew_usernames})

    username = request.data['username']
    if username:
        user = get_object_or_404(User, username=username)
        deliverycrews = Group.objects.get(name="Delivery crew")
        if request.method == "POST":
            deliverycrews.user_set.add(user) 

        return Response({"message": "User is added to Delivery crew Role"},  status.HTTP_201_CREATED)
    return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsManager])
def DeliveryCrewUserRemove(request, pk):
    user = get_object_or_404(User, pk=pk)
    if not user.groups.filter(name='Delivery crew').exists():
        return Response({"message": "The user is not in delivery crew role."}, status=status.HTTP_404_NOT_FOUND)
    delivery_crews = Group.objects.get(name="Delivery crew")
    
    if request.method == "DELETE": 
        delivery_crews.user_set.remove(user)
        return Response({"message": "User removed from delivery crew"})
     
    return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def ManagerUser(request):
    
    if request.method == "GET":
        managers = Group.objects.get(name="Manager")
        manager_usernames = managers.user_set.values_list('username', flat=True)
        return Response({"managers": manager_usernames})

    username = request.data['username']
    if username:
        user = get_object_or_404(User, username=username)
        managers = Group.objects.get(name="Manager")
        if request.method == "POST":
            managers.user_set.add(user) 

        return Response({"message": "User is added to Manager Role"},  status.HTTP_201_CREATED)
    return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def ManagerUserRemove(request, pk):
    user = get_object_or_404(User, pk=pk)
    if not user.groups.filter(name='Manager').exists():
        return Response({"message": "The user is not in manager role."}, status=status.HTTP_404_NOT_FOUND)
    managers = Group.objects.get(name="Manager")
    
    if request.method == "DELETE": 
        managers.user_set.remove(user)
        return Response({"message": "User removed from manager role"})
     
    return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def Me(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)