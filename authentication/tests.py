from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User, Tenant

class TenantProvisioningTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a superuser
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='password123'
        )
        # Authenticate as superuser
        # We can force authenticate for testing purposes or get a token
        # Let's get a token to test the full flow including permissions
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'admin@example.com',
            'password': 'password123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_provision_tenant(self):
        url = reverse('provision_tenant')
        data = {
            "business_name": "Test Corp",
            "plan": "Standard",
            "email": "ceo@testcorp.com",
            "password": "securepass",
            "first_name": "Test",
            "last_name": "CEO"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify Tenant created
        self.assertTrue(Tenant.objects.filter(business_name="Test Corp").exists())
        tenant = Tenant.objects.get(business_name="Test Corp")
        
        # Verify Admin User created
        self.assertTrue(User.objects.filter(email="ceo@testcorp.com").exists())
        user = User.objects.get(email="ceo@testcorp.com")
        self.assertEqual(user.tenant, tenant)
        self.assertEqual(user.role, 'Admin')
        
        # Verify Staff profile created
        self.assertIsNotNone(user.staff_profile)
        self.assertEqual(user.staff_profile.tenant, tenant)

    def test_provision_tenant_permission_denied(self):
        # Create a regular user (not superuser)
        regular_user = User.objects.create_user(email='regular@example.com', password='password')
        
        # Get token for regular user
        response = self.client.post(reverse('token_obtain_pair'), {
            'email': 'regular@example.com',
            'password': 'password'
        })
        token = response.data['access']
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('provision_tenant')
        data = {
            "business_name": "Hacker Corp",
            "plan": "Basic",
            "email": "hacker@hack.com",
            "password": "pass"
        }
        response = client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
