from django.core.management.base import BaseCommand
from django.utils.text import slugify

from skills.models import Skill, SkillCategory


SEED_DATA = [
    {
        'name': 'Technology',
        'icon': 'code',
        'description': 'Explore coding, AI, web development, data, and digital creativity.',
        'gradient_color': 'linear-gradient(135deg, #D6C8F3, #CFE0F7)',
        'skills': [
            'Python', 'JavaScript', 'React', 'Django', 'Machine Learning',
            'Data Science', 'Web Design', 'SQL', 'DevOps', 'Cybersecurity',
            'iOS Development', 'Android Development',
        ],
    },
    {
        'name': 'Music',
        'icon': 'music',
        'description': 'Practice instruments, theory, production, rhythm, and performance.',
        'gradient_color': 'linear-gradient(135deg, #F4C7D9, #D6C8F3)',
        'skills': [
            'Guitar', 'Piano', 'Drums', 'Violin', 'Singing', 'Music Production',
            'Music Theory', 'Bass Guitar', 'Ukulele', 'Saxophone',
        ],
    },
    {
        'name': 'Languages',
        'icon': 'language',
        'description': 'Build conversation confidence, grammar, writing, and cultural fluency.',
        'gradient_color': 'linear-gradient(135deg, #F6D1C1, #F4C7D9)',
        'skills': [
            'Spanish', 'French', 'Mandarin', 'Japanese', 'German', 'Arabic',
            'Portuguese', 'Italian', 'Korean', 'Hindi', 'Russian',
        ],
    },
    {
        'name': 'Art & Design',
        'icon': 'palette',
        'description': 'Discover illustration, visual design, photography, UI/UX, and creative craft.',
        'gradient_color': 'linear-gradient(135deg, #F4C7D9, #F6D1C1)',
        'skills': [
            'Watercolor Painting', 'Oil Painting', 'Graphic Design', 'Photography',
            'Illustration', 'Sculpting', 'Calligraphy', 'UI/UX Design', 'Video Editing',
        ],
    },
    {
        'name': 'Cooking',
        'icon': 'utensils',
        'description': 'Trade recipes, cuisine techniques, baking, meal prep, and food culture.',
        'gradient_color': 'linear-gradient(135deg, #F6D1C1, #CFE0F7)',
        'skills': [
            'Baking', 'Italian Cuisine', 'Japanese Cooking', 'Vegan Cooking',
            'Pastry Making', 'BBQ & Grilling', 'Indian Cooking', 'Meal Prepping',
        ],
    },
    {
        'name': 'Sports & Fitness',
        'icon': 'fitness',
        'description': 'Find partners for movement, coaching, wellness, training, and active skills.',
        'gradient_color': 'linear-gradient(135deg, #CFE0F7, #F9F7F6)',
        'skills': [
            'Yoga', 'Pilates', 'Swimming', 'Rock Climbing', 'Tennis',
            'Martial Arts', 'Dance', 'Weightlifting', 'Running', 'Cycling',
        ],
    },
    {
        'name': 'Business',
        'icon': 'briefcase',
        'description': 'Learn marketing, leadership, finance, entrepreneurship, and communication.',
        'gradient_color': 'linear-gradient(135deg, #CFE0F7, #D6C8F3)',
        'skills': [
            'Marketing', 'Public Speaking', 'Project Management', 'Accounting',
            'Entrepreneurship', 'Copywriting', 'SEO', 'Social Media Marketing',
        ],
    },
    {
        'name': 'Crafts',
        'icon': 'crafts',
        'description': 'Explore handmade skills, making, repair, textiles, and tactile creativity.',
        'gradient_color': 'linear-gradient(135deg, #F6D1C1, #D6C8F3)',
        'skills': [
            'Knitting', 'Woodworking', 'Sewing', 'Pottery', 'Jewelry Making',
            'Origami', '3D Printing', 'Leatherworking',
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed the database with initial skill categories and skills'

    def handle(self, *args, **kwargs):
        total_cats = 0
        total_skills = 0

        for cat_data in SEED_DATA:
            category, created = SkillCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'slug': slugify(cat_data['name']),
                    'icon': cat_data['icon'],
                    'description': cat_data.get('description', ''),
                    'gradient_color': cat_data.get('gradient_color', ''),
                },
            )
            changed = False
            for field in ['icon', 'description', 'gradient_color']:
                value = cat_data.get(field, '')
                if value and getattr(category, field) != value:
                    setattr(category, field, value)
                    changed = True
            if not category.slug:
                category.slug = slugify(category.name)
                changed = True
            if changed:
                category.save()
            if created:
                total_cats += 1
                self.stdout.write(f'Created category: {category.name}')

            for skill_name in cat_data['skills']:
                _, skill_created = Skill.objects.get_or_create(
                    name=skill_name,
                    defaults={'category': category},
                )
                if skill_created:
                    total_skills += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {total_cats} categories and {total_skills} skills.'
        ))
