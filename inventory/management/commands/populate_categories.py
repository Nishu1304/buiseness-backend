from django.core.management.base import BaseCommand
from authentication.models import Tenant
from inventory.models import Category


class Command(BaseCommand):
    help = 'Populate default categories (Mens, Womens, Kids) for all tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='Specific tenant ID to populate categories for (optional)',
        )

    def handle(self, *args, **options):
        # Default categories from frontend
        default_categories = [
            {'name': 'Mens', 'description': 'Men\'s clothing and accessories'},
            {'name': 'Womens', 'description': 'Women\'s clothing and accessories'},
            {'name': 'Kids', 'description': 'Kids clothing and accessories'},
        ]

        tenant_id = options.get('tenant_id')

        if tenant_id:
            # Populate for specific tenant
            try:
                tenant = Tenant.objects.get(tenant_id=tenant_id)
                self.populate_categories_for_tenant(tenant, default_categories)
            except Tenant.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Tenant with ID {tenant_id} does not exist')
                )
                return
        else:
            # Populate for all tenants
            tenants = Tenant.objects.all()
            
            if not tenants.exists():
                self.stdout.write(
                    self.style.WARNING('No tenants found in the database')
                )
                return

            for tenant in tenants:
                self.populate_categories_for_tenant(tenant, default_categories)

        self.stdout.write(
            self.style.SUCCESS('Successfully populated categories!')
        )

    def populate_categories_for_tenant(self, tenant, categories):
        """Populate categories for a specific tenant"""
        self.stdout.write(f'\nPopulating categories for tenant: {tenant.business_name}')
        
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                tenant=tenant,
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created category: {cat_data["name"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  - Category already exists: {cat_data["name"]}')
                )
