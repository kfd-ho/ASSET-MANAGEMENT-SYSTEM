from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from decimal import Decimal
from apps.core.models import User
from apps.assets.models import Category, Asset
from apps.employees.models import Department, Employee
from apps.allocations.models import Allocation
from apps.maintenance.models import MaintenanceSchedule, MaintenanceRecord

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@company.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Created admin user')
        
        # Create manager user
        manager_user, created = User.objects.get_or_create(
            username='manager',
            defaults={
                'email': 'manager@company.com',
                'first_name': 'John',
                'last_name': 'Manager',
                'role': 'manager'
            }
        )
        if created:
            manager_user.set_password('manager123')
            manager_user.save()
            self.stdout.write('Created manager user')
        
        # Create employee user
        employee_user, created = User.objects.get_or_create(
            username='employee',
            defaults={
                'email': 'employee@company.com',
                'first_name': 'Jane',
                'last_name': 'Employee',
                'role': 'employee'
            }
        )
        if created:
            employee_user.set_password('employee123')
            employee_user.save()
            self.stdout.write('Created employee user')
        
        # Create departments
        it_dept, _ = Department.objects.get_or_create(
            name='Information Technology',
            defaults={
                'description': 'IT Department',
                'manager': manager_user,
                'created_by': admin_user
            }
        )
        
        hr_dept, _ = Department.objects.get_or_create(
            name='Human Resources',
            defaults={
                'description': 'HR Department',
                'created_by': admin_user
            }
        )
        
        finance_dept, _ = Department.objects.get_or_create(
            name='Finance',
            defaults={
                'description': 'Finance Department',
                'created_by': admin_user
            }
        )
        
        # Create employees
        Employee.objects.get_or_create(
            user=manager_user,
            defaults={
                'employee_id': 'EMP001',
                'department': it_dept,
                'designation': 'IT Manager',
                'join_date': date.today() - timedelta(days=365),
                'mobile': '+91-9876543210',
                'created_by': admin_user
            }
        )
        
        Employee.objects.get_or_create(
            user=employee_user,
            defaults={
                'employee_id': 'EMP002',
                'department': it_dept,
                'designation': 'Software Developer',
                'join_date': date.today() - timedelta(days=180),
                'mobile': '+91-9876543211',
                'reporting_manager': manager_user,
                'created_by': admin_user
            }
        )
        
        # Create categories
        laptop_category, _ = Category.objects.get_or_create(
            name='Laptops',
            defaults={
                'description': 'Laptop computers',
                'useful_life_years': 4,
                'depreciation_rate': Decimal('25.00'),
                'created_by': admin_user
            }
        )
        
        desktop_category, _ = Category.objects.get_or_create(
            name='Desktop Computers',
            defaults={
                'description': 'Desktop computers',
                'useful_life_years': 5,
                'depreciation_rate': Decimal('20.00'),
                'created_by': admin_user
            }
        )
        
        mobile_category, _ = Category.objects.get_or_create(
            name='Mobile Phones',
            defaults={
                'description': 'Mobile phones and smartphones',
                'useful_life_years': 3,
                'depreciation_rate': Decimal('33.33'),
                'created_by': admin_user
            }
        )
        
        furniture_category, _ = Category.objects.get_or_create(
            name='Office Furniture',
            defaults={
                'description': 'Office furniture and fixtures',
                'useful_life_years': 10,
                'depreciation_rate': Decimal('10.00'),
                'created_by': admin_user
            }
        )
        
        # Create assets
        assets_data = [
            {
                'name': 'Dell Latitude 7420',
                'category': laptop_category,
                'serial_number': 'DL7420001',
                'cost': Decimal('75000.00'),
                'brand': 'Dell',
                'model': 'Latitude 7420',
                'purchase_date': date.today() - timedelta(days=90),
                'warranty_expiry': date.today() + timedelta(days=275)
            },
            {
                'name': 'HP EliteBook 840',
                'category': laptop_category,
                'serial_number': 'HP840001',
                'cost': Decimal('68000.00'),
                'brand': 'HP',
                'model': 'EliteBook 840',
                'purchase_date': date.today() - timedelta(days=120),
                'warranty_expiry': date.today() + timedelta(days=245)
            },
            {
                'name': 'Dell OptiPlex 7090',
                'category': desktop_category,
                'serial_number': 'DO7090001',
                'cost': Decimal('45000.00'),
                'brand': 'Dell',
                'model': 'OptiPlex 7090',
                'purchase_date': date.today() - timedelta(days=200),
                'warranty_expiry': date.today() + timedelta(days=165)
            },
            {
                'name': 'iPhone 13',
                'category': mobile_category,
                'serial_number': 'IP13001',
                'cost': Decimal('79900.00'),
                'brand': 'Apple',
                'model': 'iPhone 13',
                'purchase_date': date.today() - timedelta(days=60),
                'warranty_expiry': date.today() + timedelta(days=305)
            },
            {
                'name': 'Executive Office Chair',
                'category': furniture_category,
                'serial_number': 'EOC001',
                'cost': Decimal('15000.00'),
                'brand': 'Steelcase',
                'model': 'Leap V2',
                'purchase_date': date.today() - timedelta(days=300),
                'warranty_expiry': date.today() + timedelta(days=65)
            }
        ]
        
        created_assets = []
        for asset_data in assets_data:
            asset, created = Asset.objects.get_or_create(
                serial_number=asset_data['serial_number'],
                defaults={
                    **asset_data,
                    'location': 'Head Office',
                    'created_by': admin_user
                }
            )
            if created:
                created_assets.append(asset)
                self.stdout.write(f'Created asset: {asset.name}')
        
        # Create allocations
        if created_assets:
            # Allocate laptop to employee
            laptop = next((a for a in created_assets if a.category == laptop_category), None)
            if laptop:
                Allocation.objects.get_or_create(
                    asset=laptop,
                    employee=employee_user,
                    defaults={
                        'notes': 'Allocated for development work',
                        'condition_at_allocation': 'excellent',
                        'created_by': admin_user
                    }
                )
                self.stdout.write(f'Allocated {laptop.name} to {employee_user.get_full_name()}')
        
        # Create maintenance schedules
        for asset in created_assets[:3]:  # Create schedules for first 3 assets
            MaintenanceSchedule.objects.get_or_create(
                asset=asset,
                title=f'Regular Maintenance - {asset.name}',
                defaults={
                    'description': 'Regular preventive maintenance',
                    'frequency': 'quarterly',
                    'next_due_date': date.today() + timedelta(days=30),
                    'estimated_cost': Decimal('2000.00'),
                    'assigned_to': manager_user,
                    'created_by': admin_user
                }
            )
        
        # Create maintenance records
        if created_assets:
            asset = created_assets[0]
            MaintenanceRecord.objects.get_or_create(
                asset=asset,
                title='Software Update',
                defaults={
                    'description': 'Update operating system and software',
                    'status': 'completed',
                    'priority': 'medium',
                    'scheduled_date': date.today() - timedelta(days=7),
                    'completed_at': date.today() - timedelta(days=5),
                    'assigned_to': manager_user,
                    'performed_by': 'IT Support Team',
                    'estimated_cost': Decimal('1000.00'),
                    'actual_cost': Decimal('800.00'),
                    'work_performed': 'Updated OS, installed security patches, updated software applications',
                    'created_by': admin_user
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        self.stdout.write('Login credentials:')
        self.stdout.write('Admin: admin / admin123')
        self.stdout.write('Manager: manager / manager123')
        self.stdout.write('Employee: employee / employee123')