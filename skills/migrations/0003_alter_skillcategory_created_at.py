from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('skills', '0002_category_exploration_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='skillcategory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
