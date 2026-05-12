import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile
from matching.models import ExchangeRequest
from messaging.models import Conversation, Message
from ratings.models import Rating
from skills.models import Skill, SkillCategory, UserSkill


class SkillExchangeSmokeTests(TestCase):
    def setUp(self):
        self.category = SkillCategory.objects.create(name='Technology')
        self.python = Skill.objects.create(name='Python', category=self.category)
        self.django = Skill.objects.create(name='Django', category=self.category)
        self.guitar = Skill.objects.create(name='Guitar')

        self.alice = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='pass12345',
            first_name='Alice',
        )
        self.bob = User.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='pass12345',
            first_name='Bob',
        )
        self.cara = User.objects.create_user(
            username='cara',
            email='cara@example.com',
            password='pass12345',
            first_name='Cara',
        )
        for user in (self.alice, self.bob, self.cara):
            UserProfile.objects.get_or_create(user=user)

        UserSkill.objects.create(user=self.alice, skill=self.python, skill_type='teach', level='advanced')
        UserSkill.objects.create(user=self.alice, skill=self.guitar, skill_type='learn', level='beginner')
        UserSkill.objects.create(user=self.bob, skill=self.guitar, skill_type='teach', level='expert')
        UserSkill.objects.create(user=self.bob, skill=self.python, skill_type='learn', level='beginner')

    def login(self, user=None):
        user = user or self.alice
        self.client.force_login(user)

    def test_logged_out_pages_smoke(self):
        for url_name in ('home', 'login', 'signup'):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, url_name)

    def test_logged_in_pages_smoke_for_user_with_skills(self):
        self.login()
        urls = [
            reverse('dashboard'),
            reverse('profile_view', args=[self.alice.username]),
            reverse('skill_add'),
            reverse('skill_manage'),
            reverse('matches'),
            reverse('requests'),
            reverse('inbox'),
            reverse('my_ratings'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_matches_page_shows_reciprocal_skill_sections(self):
        self.login()
        response = self.client.get(reverse('matches'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'They teach you')
        self.assertContains(response, 'Guitar')
        self.assertContains(response, 'You teach them')
        self.assertContains(response, 'Python')

    def test_accepted_exchange_pages_smoke(self):
        exchange = ExchangeRequest.objects.create(
            sender=self.alice,
            receiver=self.bob,
            status='accepted',
            sender_teach_skills=['Python'],
            receiver_teach_skills=['Guitar'],
            match_score=7,
        )
        conversation = Conversation.objects.create(exchange_request=exchange)
        conversation.participants.set([self.alice, self.bob])
        Message.objects.create(
            conversation=conversation,
            sender=self.bob,
            receiver=self.alice,
            content='Ready to exchange?',
        )

        self.login()
        for url in (reverse('dashboard'), reverse('requests'), reverse('inbox'), reverse('conversation', args=[conversation.id])):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
        self.assertContains(self.client.get(reverse('profile_view', args=[self.bob.username])), reverse('conversation', args=[conversation.id]))

    def test_completed_exchange_rating_page_smoke(self):
        exchange = ExchangeRequest.objects.create(
            sender=self.alice,
            receiver=self.cara,
            status='completed',
            sender_teach_skills=['Django'],
            receiver_teach_skills=['Python'],
            match_score=4,
        )
        self.login()
        response = self.client.get(reverse('rate_user', args=[self.cara.id]))
        self.assertEqual(response.status_code, 200)
        Rating.objects.create(exchange_request=exchange, rater=self.cara, rated_user=self.alice, score=5)
        response = self.client.get(reverse('my_ratings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '5/5')


class OnboardingSkillTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='newbie', password='pass12345')
        UserProfile.objects.get_or_create(user=self.user)
        self.client.force_login(self.user)

    def test_step2_creates_teaching_skill_from_autocomplete_name(self):
        response = self.client.post(reverse('onboarding_step2'), {
            'skill_name': 'Photography',
            'skill_type': 'learn',
            'level': 'intermediate',
            'years_experience': '2',
            'description': 'Portrait basics',
        })
        self.assertRedirects(response, reverse('onboarding_step3'))
        skill = UserSkill.objects.get(user=self.user, skill__name='Photography')
        self.assertEqual(skill.skill_type, 'teach')

    def test_step3_creates_learning_skill_from_autocomplete_name(self):
        response = self.client.post(reverse('onboarding_step3'), {
            'skill_name': 'Spanish',
            'skill_type': 'teach',
            'level': 'beginner',
            'years_experience': '0',
            'description': 'Conversation practice',
        })
        self.assertRedirects(response, reverse('dashboard'))
        skill = UserSkill.objects.get(user=self.user, skill__name='Spanish')
        self.assertEqual(skill.skill_type, 'learn')


class SkillAndMessageApiTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pass12345')
        self.bob = User.objects.create_user(username='bob', password='pass12345')
        self.skill = Skill.objects.create(name='React')
        for user in (self.alice, self.bob):
            UserProfile.objects.get_or_create(user=user)

        self.exchange = ExchangeRequest.objects.create(
            sender=self.alice,
            receiver=self.bob,
            status='accepted',
            sender_teach_skills=['React'],
            receiver_teach_skills=['Django'],
            match_score=6,
        )
        self.conversation = Conversation.objects.create(exchange_request=self.exchange)
        self.conversation.participants.set([self.alice, self.bob])

    def test_skill_search_and_create_apis(self):
        response = self.client.get(reverse('skill_search_api'), {'q': 'Re'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['skills'][0]['name'], 'React')

        response = self.client.post(
            reverse('skill_create_api'),
            data=json.dumps({'name': 'Rust'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.alice)
        response = self.client.post(
            reverse('skill_create_api'),
            data=json.dumps({'name': 'Rust'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['created'])
        self.assertTrue(Skill.objects.filter(name='Rust').exists())

    def test_message_send_and_poll_apis(self):
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse('send_message_api', args=[self.conversation.id]),
            data=json.dumps({'content': 'Hello Bob'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 1)
        message_id = response.json()['id']

        self.client.force_login(self.bob)
        response = self.client.get(reverse('poll_messages', args=[self.conversation.id]))
        self.assertEqual(response.status_code, 200)
        messages = response.json()['messages']
        self.assertEqual(messages[0]['id'], message_id)
        self.assertFalse(messages[0]['is_mine'])
