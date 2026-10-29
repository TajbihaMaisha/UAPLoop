from django.conf import settings
from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = 'Create or update the admin account from .env'

    def handle(self, *args, **options):
        email = settings.ADMIN_EMAIL
        password = settings.ADMIN_PASSWORD
        if not email or not password:
            self.stderr.write('Set ADMIN_EMAIL and ADMIN_PASSWORD in .env')
            return
        user = User.objects.filter(email=email).first()
        if user is None:
            user = User(email=email)
        user.is_staff = True
        user.is_superuser = True
        user.status = 'active'
        user.set_password(password)
        user.save()
        self.stdout.write('Admin ready: ' + email)
