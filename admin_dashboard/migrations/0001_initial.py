from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(db_index=True, max_length=100)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activity_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [
                    models.Index(fields=['action', 'timestamp'], name='admin_dashb_action_739831_idx'),
                    models.Index(fields=['user', 'timestamp'], name='admin_dashb_user_id_3f5210_idx'),
                ],
            },
        ),
    ]
