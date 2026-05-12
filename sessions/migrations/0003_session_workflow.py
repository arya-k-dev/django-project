from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('session_booking', '0002_session_booking_complete'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('accepted', 'Accepted'),
                    ('rejected', 'Rejected'),
                    ('completed', 'Completed'),
                    ('cancelled', 'Cancelled'),
                    ('missed', 'Missed'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name='SessionReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField()),
                ('feedback', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_reviews', to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='session_booking.session')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='sessionreview',
            constraint=models.UniqueConstraint(fields=('session', 'reviewer'), name='unique_session_review_per_user'),
        ),
        migrations.AddConstraint(
            model_name='sessionreview',
            constraint=models.CheckConstraint(
                check=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name='session_review_rating_1_5',
            ),
        ),
    ]
