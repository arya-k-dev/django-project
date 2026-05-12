from django.db import migrations, models
from django.utils import timezone
from django.utils.text import slugify


def populate_category_metadata(apps, schema_editor):
    SkillCategory = apps.get_model('skills', 'SkillCategory')
    gradients = {
        'technology': 'linear-gradient(135deg, #D6C8F3, #CFE0F7)',
        'music': 'linear-gradient(135deg, #F4C7D9, #D6C8F3)',
        'business': 'linear-gradient(135deg, #CFE0F7, #D6C8F3)',
        'languages': 'linear-gradient(135deg, #F6D1C1, #F4C7D9)',
        'cooking': 'linear-gradient(135deg, #F6D1C1, #CFE0F7)',
        'art-design': 'linear-gradient(135deg, #F4C7D9, #F6D1C1)',
        'sports-fitness': 'linear-gradient(135deg, #CFE0F7, #F9F7F6)',
        'crafts': 'linear-gradient(135deg, #F6D1C1, #D6C8F3)',
    }

    used_slugs = set()
    for category in SkillCategory.objects.all():
        base_slug = slugify(category.name) or f'category-{category.pk}'
        slug = base_slug
        suffix = 2
        while slug in used_slugs or SkillCategory.objects.exclude(pk=category.pk).filter(slug=slug).exists():
            slug = f'{base_slug}-{suffix}'
            suffix += 1
        used_slugs.add(slug)
        category.slug = slug
        category.gradient_color = category.gradient_color or gradients.get(slug, 'linear-gradient(135deg, #D6C8F3, #CFE0F7)')
        category.created_at = category.created_at or timezone.now()
        category.save(update_fields=['slug', 'gradient_color', 'created_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('skills', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='skillcategory',
            name='slug',
            field=models.SlugField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='skillcategory',
            name='gradient_color',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='skillcategory',
            name='created_at',
            field=models.DateTimeField(default=timezone.now),
            preserve_default=False,
        ),
        migrations.RunPython(populate_category_metadata, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='skillcategory',
            name='slug',
            field=models.SlugField(blank=True, max_length=120, unique=True),
        ),
    ]
