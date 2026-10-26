from django.db import migrations

def map_existing_roles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('team', 'UserProfile')
    for user in User.objects.all().iterator():
        role = 'administrator' if user.is_superuser else 'staff' if user.is_staff else 'member'
        Profile.objects.get_or_create(user_id=user.pk, defaults={'role': role})

class Migration(migrations.Migration):
    dependencies = [('team', '0005_announcement_is_featured'), migrations.swappable_dependency('auth.User')]
    operations = [migrations.RunPython(map_existing_roles, migrations.RunPython.noop)]
