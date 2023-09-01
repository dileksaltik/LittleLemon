from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import MenuItem, Category
from .serializers import MenuItemSerializer

class MenuItemListCreateAPIViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager_user = User.objects.create_user(username='test_manager', password='admin@10!')
        self.customer_user = User.objects.create_user(username='test_customer', password='admin@10!')
        self.deliverycrew_user = User.objects.create_user(username='test_deliverycrew', password='admin@10!')
        self.manager_user.groups.create(name='Manager')
        self.manager_user.groups.create(name='Delivery crew')
        # Create a Category instance
        self.category = Category.objects.create(slug='category-slug', title='Category Title')

    def test_get_menu_items(self):
        response = self.client.get('/api/menu-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_menu_item_as_manager(self):
        self.client.login(username='test_manager', password='admin@10!')
        data = {
            'title': 'Test Item',
            'price': 9.99,
            'featured': True,
            'category_id': self.category.id
        }
        response = self.client.post('/api/menu-items/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_menu_item_as_deliverycrew(self):
        self.client.login(username='test_deliverycrew', password='admin@10!')
        data = {
            'title': 'Test Item',
            'price': 9.99,
            'featured': True,
            'category_id': self.category.id
        }
        response = self.client.post('/api/menu-items/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
   
    def test_create_menu_item_as_customer(self):
        self.client.login(username='test_customer', password='admin@10!')
        data = {
            'title': 'Test Item',
            'price': 9.99,
            'featured': True,
            'category_id': self.category.id
        }
        response = self.client.post('/api/menu-items/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_menu_item_unauthenticated(self):
        data = {
            'title': 'Test Item',
            'price': 9.99,
            'featured': True,
            'category_id': self.category.id
        }
        response = self.client.post('/api/menu-items/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



class SingleMenuItemRetrieveUpdateDestroyAPIViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager_user = User.objects.create_user(username='test_manager', password='admin@10!')
        self.customer_user = User.objects.create_user(username='test_customer', password='admin@10!')
        self.delivercrew_user = User.objects.create_user(username='test_deliverycrew', password='admin@10!')
        self.manager_user.groups.create(name='Manager')
        self.delivercrew_user.groups.create(name='Delivery crew')
        # Create a Category instance
        self.category = Category.objects.create(slug='category-slug', title='Category Title')

        # Create a MenuItem instance
        self.menu_item = MenuItem.objects.create(
            title='Test Item',
            price=9.99,
            featured=True,
            category=self.category,
        )

    def test_retrieve_single_menu_item(self):
        response = self.client.get(f'/api/menu-items/{self.menu_item.pk}/')
        print(response.request.get('PATH_INFO'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = MenuItemSerializer(self.menu_item)
        self.assertEqual(response.data, serializer.data)

    def test_update_menu_item_as_manager(self):
        self.client.login(username='test_manager', password='admin@10!')
        data = {
            'title': 'Updated Item',
            'price': 14.99,
            'featured': False,
            'category_id': self.category.pk
        }
        response = self.client.put(f'/api/menu-items/{self.menu_item.pk}/', data)
        print(response.request.get('PATH_INFO'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.menu_item.refresh_from_db()
        serializer = MenuItemSerializer(self.menu_item)
        self.assertEqual(response.data, serializer.data)

    def test_update_menu_item_as_customer(self):
        self.client.login(username='test_customer', password='admin@10!')
        data = {
            'title': 'Updated Item',
            'price': 14.99,
            'featured': False,
            'category_id': self.category.pk
        }
        response = self.client.put(f'/api/menu-items/{self.menu_item.pk}/', data)
        print(response.request.get('PATH_INFO'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_menu_item_as_deliverycrew(self):
        self.client.login(username='test_deliverycrew', password='admin@10!')
        data = {
            'title': 'Updated Item',
            'price': 14.99,
            'featured': False,
            'category_id': self.category.pk
        }
        response = self.client.put(f'/api/menu-items/{self.menu_item.pk}/', data)
        print(response.request.get('PATH_INFO'))
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_menu_item_as_unauthenticated(self):
        data = {
            'title': 'Updated Item',
            'price': 14.99,
            'featured': False,
            'category_id': self.category.pk
        }
        response = self.client.put(f'/api/menu-items/{self.menu_item.pk}/', data)
        print(response.request.get('PATH_INFO'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_menu_item_as_manager(self):
        self.client.login(username='test_manager', password='admin@10!')
        response = self.client.delete(f'/api/menu-items/{self.menu_item.pk}/')
        print(response.request.get('PATH_INFO'))
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MenuItem.objects.filter(pk=self.menu_item.pk).exists())

    def test_delete_menu_item_as_customer(self):
        self.client.login(username='test_customer', password='admin@10!')
        response = self.client.delete(f'/api/menu-items/{self.menu_item.pk}/')
        print(response.request.get('PATH_INFO'))
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_menu_item_as_deliverycrew(self):
        self.client.login(username='test_deliverycrew', password='admin@10!')
        response = self.client.delete(f'/api/menu-items/{self.menu_item.pk}/')
        print(response.request.get('PATH_INFO'))
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_menu_item_as_unauthenticated(self):
        response = self.client.delete(f'/api/menu-items/{self.menu_item.pk}/')
        print(response.request.get('PATH_INFO'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
