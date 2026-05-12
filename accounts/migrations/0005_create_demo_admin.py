from django.db import migrations


class Migration(migrations.Migration):
    """Disabled: admin users must be created explicitly with createsuperuser."""

    dependencies = [
        ('accounts', '0004_userprofile_is_admin'),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
    ]
