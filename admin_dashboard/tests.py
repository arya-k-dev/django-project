from datetime import timedelta

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import UserProfile
from matching.models import ExchangeRequest
from messaging.models import Conversation, Message
from .models import ActivityLog


@override_settings(ALLOWED_HOSTS=['testserver'])
class AdminDashboardAPITests(APITestCase):
    def setUp(self):
        self.admin = self._user('admin', is_admin=True)
        self.other_admin = self._user('other_admin', is_admin=True)
        self.user = self._user('member')

    def _user(self, username, is_admin=False):
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='StrongPass123!',
        )
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_admin = is_admin
        profile.save(update_fields=['is_admin'])
        return user

    def _as_admin(self):
        self.client.force_authenticate(self.admin)

    def test_admin_access_control_returns_403(self):
        url = reverse('admin_dashboard_users')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_admin_can_list_users(self):
        self._as_admin()
        response = self.client.get(reverse('admin_dashboard_users'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)

    def test_admin_cannot_deactivate_self(self):
        self._as_admin()
        url = reverse('admin_dashboard_user_deactivate', kwargs={'user_id': self.admin.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_cannot_deactivate_last_active_admin(self):
        self.other_admin.is_active = False
        self.other_admin.save(update_fields=['is_active'])
        self.user.is_admin = True
        self.client.force_authenticate(self.user)
        url = reverse('admin_dashboard_user_deactivate', kwargs={'user_id': self.admin.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_activity_log_filtering_and_invalid_date(self):
        ActivityLog.record(user=self.user, action='login')
        ActivityLog.record(user=self.admin, action='admin_export_users')
        self._as_admin()

        response = self.client.get(reverse('admin_dashboard_activity_logs'), {'action': 'login'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['action'], 'login')

        response = self.client.get(reverse('admin_dashboard_activity_logs'), {'start_date': 'not-a-date'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('start_date', response.data)

    def test_match_and_skill_analytics_use_request_skill_fields(self):
        learner = self._user('learner')
        mentor = self._user('mentor')
        third = self._user('third')
        ExchangeRequest.objects.create(
            sender=learner,
            receiver=mentor,
            sender_teach_skills=['Python'],
            receiver_teach_skills=['Django', 'Python'],
            match_score=7,
        )
        ExchangeRequest.objects.create(
            sender=learner,
            receiver=third,
            sender_teach_skills=['React'],
            receiver_teach_skills=['Python'],
            match_score=3,
        )
        self._as_admin()

        score_response = self.client.get(reverse('admin_dashboard_match_score_analytics'))
        self.assertEqual(score_response.status_code, 200)
        self.assertEqual(score_response.data['total_matches'], 2)
        self.assertEqual(float(score_response.data['average_match_score']), 5.0)

        skills_response = self.client.get(reverse('admin_dashboard_skill_analytics'))
        self.assertEqual(skills_response.status_code, 200)
        self.assertEqual(skills_response.data['results'][0], {'name': 'Python', 'request_count': 3})

    def test_message_analytics(self):
        exchange = ExchangeRequest.objects.create(
            sender=self.user,
            receiver=self.admin,
            status='accepted',
            match_score=5,
        )
        conversation = Conversation.objects.create(exchange_request=exchange)
        conversation.participants.set([self.user, self.admin])
        Message.objects.create(conversation=conversation, sender=self.user, receiver=self.admin, content='Hello')
        Message.objects.create(conversation=conversation, sender=self.admin, receiver=self.user, content='Hi')
        self._as_admin()

        response = self.client.get(reverse('admin_dashboard_message_analytics'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 2)
        self.assertEqual(response.data['per_day'][0]['total'], 2)

    def test_csv_export_masks_email_and_logs_action(self):
        self._as_admin()

        response = self.client.get(reverse('admin_dashboard_users_csv'))
        body = ''.join(
            chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk
            for chunk in response.streaming_content
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('masked_email', body)
        self.assertIn('ad***@example.com', body)
        self.assertTrue(ActivityLog.objects.filter(action='admin_export_users').exists())

    def test_invalid_date_range_returns_400(self):
        self._as_admin()
        today = timezone.now().date()
        response = self.client.get(reverse('admin_dashboard_match_analytics'), {
            'start_date': (today + timedelta(days=1)).isoformat(),
            'end_date': today.isoformat(),
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('date_range', response.data)
