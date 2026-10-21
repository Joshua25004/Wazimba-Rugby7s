from datetime import date, time

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import (AlumniProfile, Announcement, LearningResource, MediaAsset,
                     Match, MatchParticipation, Player, Season, TeamEvent,
                     Tournament, TrainingAttendance, TrainingSession)


class WazimbaApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username='manager', password='test-pass-123', is_staff=True)
        self.member = User.objects.create_user(username='player', password='test-pass-123')
        self.season = Season.objects.create(name='2026 Season', start_date=date(2026, 1, 1), status='active')
        self.player = Player.objects.create(full_name='Test Player', position='Centre', status='active')
        self.match = Match.objects.create(opponent='Test RFC', date=date(2026, 4, 2), status='completed',
            wazimba_score=26, opponent_score=12, season=self.season)
        MatchParticipation.objects.create(match=self.match, player=self.player, started=True,
            minutes_played=40, tries=2, tackles=7, assists=1, turnovers_won=1, errors=0)
        self.session = TrainingSession.objects.create(title='Defence', date=date(2026, 4, 3),
            start_time=time(17), season=self.season)
        TrainingAttendance.objects.create(session=self.session, player=self.player, attended=True)

    def test_analytics_are_computed_from_records(self):
        self.client.force_authenticate(self.member)
        team = self.client.get('/api/performance/team/', {'season': self.season.id})
        self.assertEqual(team.status_code, 200)
        self.assertEqual(team.data['matches_played'], 1)
        self.assertEqual(team.data['wins'], 1)
        self.assertEqual(team.data['points_for'], 26)
        self.assertEqual(team.data['training_attendance_rate'], 100)

        players = self.client.get('/api/performance/players/', {'season': self.season.id})
        self.assertEqual(players.status_code, 200)
        self.assertEqual(players.data[0]['tries'], 2)
        self.assertEqual(players.data[0]['minutes'], 40)

    def test_empty_analytics_and_dashboard_are_safe(self):
        Match.objects.all().delete()
        MatchParticipation.objects.all().delete()
        self.client.force_authenticate(self.member)
        result = self.client.get('/api/performance/team/')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['matches_played'], 0)
        self.assertIsNone(result.data['win_rate'])
        dashboard = self.client.get('/api/dashboard/')
        self.assertEqual(dashboard.status_code, 200)
        self.assertIsNone(dashboard.data['win_rate'])

    def test_login_returns_a_valid_token_and_rejects_bad_credentials(self):
        success = self.client.post('/api/auth/token/', {'username': 'manager', 'password': 'test-pass-123'}, format='json')
        self.assertEqual(success.status_code, 200)
        self.assertTrue(success.data['token'])
        self.assertTrue(success.data['is_staff'])
        failure = self.client.post('/api/auth/token/', {'username': 'manager', 'password': 'wrong'}, format='json')
        self.assertEqual(failure.status_code, 400)

    def test_authentication_and_staff_write_permissions_are_enforced(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/players/').status_code, 401)
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.post('/api/players/', {'full_name': 'Blocked'}).status_code, 403)
        self.client.force_authenticate(self.staff)
        created = self.client.post('/api/players/', {'full_name': 'New Player', 'position': 'Wing'}, format='json')
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.patch(f"/api/players/{created.data['id']}/", {'position': 'Centre'}, format='json').status_code, 200)
        self.assertEqual(self.client.delete(f"/api/players/{created.data['id']}/").status_code, 204)
        self.assertEqual(self.client.delete(f'/api/players/{self.player.id}/').status_code, 409)

    def test_reports_and_export(self):
        self.client.force_authenticate(self.member)
        report = self.client.get('/api/reports/', {'season': self.season.id})
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.data['team']['matches_played'], 1)
        export = self.client.get('/api/reports/csv/', {'season': self.season.id})
        self.assertEqual(export.status_code, 200)
        self.assertIn('text/csv', export['Content-Type'])
        self.assertIn(b'Test RFC', export.content)
        self.assertIn(b'Test Player', export.content)

    def test_review_content_and_restricted_welfare_records(self):
        self.client.force_authenticate(self.staff)
        review = self.client.post('/api/match-reviews/', {'match': self.match.id, 'went_well': 'Good support lines'}, format='json')
        self.assertEqual(review.status_code, 201)
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.get('/api/match-reviews/').status_code, 200)
        self.assertEqual(self.client.get('/api/injury-records/').status_code, 403)
        self.client.force_authenticate(self.staff)
        injury = self.client.post('/api/injury-records/', {'player': self.player.id, 'injury_date': '2026-04-04', 'description': 'Shoulder assessment'}, format='json')
        self.assertEqual(injury.status_code, 201)

    def test_connected_management_records_can_be_created(self):
        self.client.force_authenticate(self.staff)
        event = self.client.post('/api/team-events/', {'title': 'Team meeting', 'category': 'meeting', 'date': '2026-04-05'}, format='json')
        self.assertEqual(event.status_code, 201)
        event_attendance = self.client.post('/api/team-event-attendance/', {'event': event.data['id'], 'player': self.player.id, 'attended': True}, format='json')
        self.assertEqual(event_attendance.status_code, 201)
        announcement = self.client.post('/api/announcements/', {'title': 'Selection notice', 'body': 'Squad meeting'}, format='json')
        self.assertEqual(announcement.status_code, 201)
        tournament = self.client.post('/api/tournaments/', {'name': 'Nairobi 7s', 'season': self.season.id}, format='json')
        self.assertEqual(tournament.status_code, 201)
        registration = self.client.post('/api/season-registrations/', {'season': self.season.id, 'player': self.player.id}, format='json')
        self.assertEqual(registration.status_code, 201)
        self.assertEqual(self.client.post('/api/match-participations/', {'match': self.match.id, 'player': self.player.id, 'tries': 3}, format='json').status_code, 400)
        stats = self.client.post('/api/match-participations/', {'match': self.match.id, 'player': Player.objects.create(full_name='Second Player').id, 'tries': 3}, format='json')
        self.assertEqual(stats.status_code, 201)
        attendance = self.client.post('/api/training-attendance/', {'session': self.session.id, 'player': Player.objects.create(full_name='Third Player').id, 'attended': True}, format='json')
        self.assertEqual(attendance.status_code, 201)
        learning = self.client.post('/api/learning-resources/', {'title': '7s law guide', 'category': 'law', 'source_url': 'https://example.org/laws', 'is_official': True}, format='json')
        self.assertEqual(learning.status_code, 201)
        unapproved = self.client.post('/api/media/', {'title': 'Unapproved image', 'media_url': 'https://example.org/image.jpg'}, format='json')
        self.assertEqual(unapproved.status_code, 201)
        approved = self.client.post('/api/media/', {'title': 'Team image', 'media_url': 'https://example.org/team.jpg', 'consent_confirmed': True}, format='json')
        self.assertEqual(approved.status_code, 201)
        alumni = self.client.post('/api/alumni/', {'full_name': 'Former Player', 'contact_email': 'alumni@example.org', 'contact_consent': False}, format='json')
        self.assertEqual(alumni.status_code, 201)
        self.client.force_authenticate(self.member)
        media = self.client.get('/api/media/')
        self.assertEqual(media.status_code, 200)
        self.assertEqual([row['title'] for row in media.data['results']], ['Team image'])
        alumni_rows = self.client.get('/api/alumni/').data['results']
        self.assertEqual(alumni_rows[0]['contact_email'], '')

    def test_invalid_analytics_filters_return_client_errors(self):
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.get('/api/performance/team/', {'season': 'not-a-number'}).status_code, 400)
        self.assertEqual(self.client.get('/api/performance/players/', {'player': 'not-a-number'}).status_code, 400)
