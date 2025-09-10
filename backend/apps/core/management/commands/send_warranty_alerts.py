from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.assets.models import Asset
from apps.maintenance.models import WarrantyAlert


class Command(BaseCommand):
    help = 'Create warranty alerts for assets nearing expiry'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Days before expiry to create alerts (default: 30)'
        )

    def handle(self, *args, **options):
        days_before = options['days']
        alert_date = timezone.now().date() + timedelta(days=days_before)
        
        # Find assets with warranty expiring in specified days
        assets = Asset.objects.filter(
            warranty_expiry__lte=alert_date,
            warranty_expiry__gte=timezone.now().date(),
            status__in=['active', 'maintenance']
        )
        
        created_count = 0
        for asset in assets:
            alert, created = WarrantyAlert.objects.get_or_create(
                asset=asset,
                days_before_expiry=days_before,
                defaults={
                    'alert_date': timezone.now().date()
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created warranty alert for {asset.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} warranty alerts')
        )
        
        # Send pending alerts
        pending_alerts = WarrantyAlert.objects.filter(is_sent=False)
        sent_count = 0
        
        for alert in pending_alerts:
            alert.send_alert()
            sent_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Sent {sent_count} warranty alert emails')
        )