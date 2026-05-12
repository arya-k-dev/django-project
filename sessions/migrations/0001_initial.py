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
            name='Session',
            fields=[
                ('id',            models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('skill_offered', models.CharField(blank=True, max_length=200)),
                ('skill_wanted',  models.CharField(blank=True, max_length=200)),
                ('scheduled_at',  models.DateTimeField()),
                ('duration',      models.PositiveIntegerField(
                    choices=[(30, '30 minutes'), (45, '45 minutes'), (60, '1 hour'), (90, '1.5 hours'), (120, '2 hours')],
                    default=60,
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending',   'Pending'),
                        ('accepted',  'Accepted'),
                        ('rejected',  'Rejected'),
                        ('completed', 'Completed'),
                        ('cancelled', 'Cancelled'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('notes',      models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sender',   models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions_sent',     to=settings.AUTH_USER_MODEL)),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions_received', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-scheduled_at']},
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['sender', 'status'], name='sessions_se_sender__idx'),
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['receiver', 'status'], name='sessions_se_receive_idx'),
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['scheduled_at'], name='sessions_se_schedul_idx'),
        ),
    ]
