from django.contrib.auth.models import User


def create_superuser():
    superuser = User.objects.create_superuser('admin', '', 'admin')
    return superuser
