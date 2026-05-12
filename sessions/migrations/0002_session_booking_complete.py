from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('session_booking', '0001_initial'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='session',
            name='sessions_se_schedul_idx',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='scheduled_at',
            new_name='start_time',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='skill_wanted',
            new_name='skill_requested',
        ),
        migrations.AlterModelOptions(
            name='session',
            options={'ordering': ['-start_time']},
        ),
        migrations.AlterField(
            model_name='session',
            name='duration',
            field=models.IntegerField(choices=[(30, '30 minutes'), (60, '1 hour'), (90, '1.5 hours')], help_text='Duration in minutes'),
        ),
        migrations.AlterField(
            model_name='session',
            name='receiver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_sessions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='session',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_sessions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='session',
            name='skill_offered',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='session',
            name='skill_requested',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='session',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('completed', 'Completed')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='session',
            name='feedback',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='session',
            name='is_rated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='session',
            name='meeting_link',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='rating',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['start_time'], name='sessions_se_start_t_7b6b46_idx'),
        ),
    ]
