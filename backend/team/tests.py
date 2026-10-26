from datetime import date, time

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from rest_framework.authtoken.models import Token


from .models import (AlumniProfile, Announcement, LearningResource, MatchReview,
                     MediaAsset, Match, MatchParticipation, Player, Season,
                     TeamEvent, Tournament, TrainingAttendance, TrainingSession)


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


    def test_login_rejects_missing_credentials(self):
        # Submit a login request without a username or password.
        response = self.client.post(
            '/api/auth/token/',
            {},
            format='json',
        )

        # Login must fail and must not return an authentication token.
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('token', response.data)


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

    def test_alumni_contact_email_respects_consent(self):
        alumni = AlumniProfile.objects.create(
            full_name='Privacy Test Alumni',
            contact_email='private@example.org',
            contact_consent=False,
        )

        # Ordinary members should not see the email without consent.
        self.client.force_authenticate(self.member)
        response = self.client.get(f'/api/alumni/{alumni.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['contact_email'], '')

        # Staff can access the email even without consent.
        self.client.force_authenticate(self.staff)
        response = self.client.get(f'/api/alumni/{alumni.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['contact_email'],
            'private@example.org',
        )

        # With consent, ordinary members can see the email.
        alumni.contact_consent = True
        alumni.save(update_fields=['contact_consent'])

        self.client.force_authenticate(self.member)
        response = self.client.get(f'/api/alumni/{alumni.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['contact_email'],
            'private@example.org',
        )

    def test_match_reviews_are_readable_by_members_but_writable_only_by_staff(self):
        review = MatchReview.objects.create(
            match=self.match,
            went_well='Good support lines',
            needs_work='Improve defensive alignment',
        )

        # Ordinary members can read the review list and individual reviews.
        self.client.force_authenticate(self.member)
        self.assertEqual(
            self.client.get('/api/match-reviews/').status_code, 200
        )
        self.assertEqual(
            self.client.get(f'/api/match-reviews/{review.id}/').status_code, 200
        )

        # Ordinary members cannot edit or delete reviews.
        self.assertEqual(
            self.client.patch(
                f'/api/match-reviews/{review.id}/',
                {'went_well': 'Changed by member'},
                format='json',
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.delete(f'/api/match-reviews/{review.id}/').status_code,
            403,
        )

        # Staff can edit and delete reviews.
        self.client.force_authenticate(self.staff)
        self.assertEqual(
            self.client.patch(
                f'/api/match-reviews/{review.id}/',
                {'went_well': 'Updated by staff'},
                format='json',
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.delete(f'/api/match-reviews/{review.id}/').status_code,
            204,
        )

    def test_player_email_is_visible_to_staff_only(self):
        player = Player.objects.create(
            full_name='Privacy Test Player',
            email='player-private@example.org',
        )

        # Ordinary authenticated members can view the profile,
        # but the email address must be hidden.
        self.client.force_authenticate(self.member)
        response = self.client.get(f'/api/players/{player.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], '')

        # Staff can view the actual email address.
        self.client.force_authenticate(self.staff)
        response = self.client.get(f'/api/players/{player.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['email'],
            'player-private@example.org',
        )

    def test_training_attendance_notes_are_visible_to_staff_only(self):
        attendance = TrainingAttendance.objects.get(
            session=self.session,
            player=self.player,
        )
        attendance.notes = 'Private welfare follow-up'
        attendance.save(update_fields=['notes'])

        # Members can view attendance, but not private notes.
        self.client.force_authenticate(self.member)
        response = self.client.get(
            f'/api/training-attendance/{attendance.id}/'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['attended'], True)
        self.assertEqual(response.data['notes'], '')

        # Staff can view the notes.
        self.client.force_authenticate(self.staff)
        response = self.client.get(
            f'/api/training-attendance/{attendance.id}/'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['notes'],
            'Private welfare follow-up',
        )

    def test_training_attendance_is_read_only_for_members(self):
        attendance = TrainingAttendance.objects.get(
            session=self.session,
            player=self.player,
        )
        url = f'/api/training-attendance/{attendance.id}/'

        self.client.force_authenticate(self.member)

        # Members should not be able to change attendance.
        response = self.client.patch(
            url,
            {'attended': False},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

        # Members should not be able to delete attendance.
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

        # Confirm the attendance record remains unchanged.
        attendance.refresh_from_db()
        self.assertTrue(attendance.attended)


    def test_staff_can_update_training_attendance(self):
        attendance = TrainingAttendance.objects.get(
            session=self.session,
            player=self.player,
        )
        url = f'/api/training-attendance/{attendance.id}/'

        self.client.force_authenticate(self.staff)

        response = self.client.patch(
            url,
            {'attended': False},
            format='json',
        )

        self.assertEqual(response.status_code, 200)

        attendance.refresh_from_db()
        self.assertFalse(attendance.attended)
    def test_announcements_are_read_only_for_members(self):
        announcement = Announcement.objects.create(
            title='Training Update',
            body='Training is scheduled for Friday.',
            is_published=True,
            author=self.staff,
        )
        url = f'/api/announcements/{announcement.id}/'

        self.client.force_authenticate(self.member)

        # Members can read published announcements.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Members cannot edit or delete announcements.
        response = self.client.patch(
            url,
            {'title': 'Unauthorized Update'},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

        # Confirm the original title remains unchanged.
        announcement.refresh_from_db()
        self.assertEqual(announcement.title, 'Training Update')

        # Members cannot create announcements.
        response = self.client.post(
            '/api/announcements/',
            {
                'title': 'Unauthorized Announcement',
                'body': 'This should not be published.',
                'is_published': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)


    def test_staff_can_create_and_update_announcements(self):
        self.client.force_authenticate(self.staff)

        # Staff can create an announcement.
        response = self.client.post(
            '/api/announcements/',
            {
                'title': 'Training Update',
                'body': 'Training is scheduled for Friday.',
                'is_published': True,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)

        announcement_id = response.data['id']
        url = f'/api/announcements/{announcement_id}/'

        # Staff can update the announcement.
        response = self.client.patch(
            url,
            {'title': 'Updated Training Notice'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data['title'],
            'Updated Training Notice',
        )


    def test_injury_records_are_accessible_to_staff_only(self):
        from .models import InjuryRecord

        injury = InjuryRecord.objects.create(
            player=self.player,
            injury_date=date(2026, 4, 1),
            description='Test knee injury',
            status='assessed',
            staff_notes='Private medical follow-up',
        )
        url = f'/api/injury-records/{injury.id}/'

        # Ordinary members must not access injury records.
        self.client.force_authenticate(self.member)

        response = self.client.get('/api/injury-records/')
        self.assertEqual(response.status_code, 403)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # Staff should be able to list and retrieve injury records.
        self.client.force_authenticate(self.staff)

        response = self.client.get('/api/injury-records/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['staff_notes'],
            'Private medical follow-up',
        )



    def test_media_visibility_respects_consent(self):
        confirmed_media = MediaAsset.objects.create(
            title='Approved Team Photo',
            category='team',
            media_url='https://example.com/approved.jpg',
            consent_confirmed=True,
            season=self.season,
        )
        unconfirmed_media = MediaAsset.objects.create(
            title='Unapproved Team Photo',
            category='team',
            media_url='https://example.com/unapproved.jpg',
            consent_confirmed=False,
            season=self.season,
        )

        # Members should see only media with confirmed consent.
        self.client.force_authenticate(self.member)
        response = self.client.get('/api/media/')

        self.assertEqual(response.status_code, 200)
        member_ids = {
            item['id'] for item in response.data['results']
        }
        self.assertIn(confirmed_media.id, member_ids)
        self.assertNotIn(unconfirmed_media.id, member_ids)

        # Staff should see both approved and unapproved media.
        self.client.force_authenticate(self.staff)
        response = self.client.get('/api/media/')

        self.assertEqual(response.status_code, 200)
        staff_ids = {
            item['id'] for item in response.data['results']
        }
        self.assertIn(confirmed_media.id, staff_ids)
        self.assertIn(unconfirmed_media.id, staff_ids)


    def test_learning_resources_are_read_only_for_members(self):
        resource = LearningResource.objects.create(
            title='Rugby Laws Guide',
            category='law',
            summary='A guide to rugby rules and laws.',
            source_url='https://example.com/rugby-laws',
            is_official=True,
            created_by=self.staff,
        )
        url = f'/api/learning-resources/{resource.id}/'

        self.client.force_authenticate(self.member)

        # Members can read resources.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Members cannot edit or delete resources.
        response = self.client.patch(
            url,
            {'title': 'Unauthorized Change'},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

        # Members cannot create resources.
        response = self.client.post(
            '/api/learning-resources/',
            {
                'title': 'Unauthorized Resource',
                'category': 'law',
                'summary': 'This should not be created.',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

        # Confirm the original record was not changed.
        resource.refresh_from_db()
        self.assertEqual(resource.title, 'Rugby Laws Guide')


    def test_team_events_are_read_only_for_members(self):
        event = TeamEvent.objects.create(
            title='Team Bonding Day',
            category='bonding',
            date=date(2026, 11, 15),
            start_time=time(10, 0),
            location='Laikipia University',
            description='Team bonding activities.',
            season=self.season,
        )
        url = f'/api/team-events/{event.id}/'

        self.client.force_authenticate(self.member)

        # Members can view events.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Members cannot edit or delete events.
        response = self.client.patch(
            url,
            {'title': 'Unauthorized Event Change'},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

        # Members cannot create events.
        response = self.client.post(
        '/api/team-events/',
            {
                'title': 'Unauthorized Event',
                'category': 'other',
                'date': '2026-11-16',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

        # Confirm the event remains unchanged.
        event.refresh_from_db()
        self.assertEqual(event.title, 'Team Bonding Day')


    def test_tournaments_are_read_only_for_members(self):
        tournament = Tournament.objects.create(
            name='Laikipia Rugby Sevens',
            location='Nanyuki',
            organizer='Laikipia University',
            start_date=date(2026, 11, 20),
            end_date=date(2026, 11, 21),
            status='upcoming',
            season=self.season,
        )
        url = f'/api/tournaments/{tournament.id}/'

        self.client.force_authenticate(self.member)

        # Members can view tournaments.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Members cannot edit or delete tournaments.
        response = self.client.patch(
            url,
            {'name': 'Unauthorized Tournament Change'},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

        # Members cannot create tournaments.
        response = self.client.post(
            '/api/tournaments/',
            {
                'name': 'Unauthorized Tournament',
                'status': 'upcoming',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

        # Confirm the original tournament remains unchanged.
        tournament.refresh_from_db()
        self.assertEqual(tournament.name, 'Laikipia Rugby Sevens')

def test_matches_are_read_only_for_members(self):
    url = f'/api/matches/{self.match.id}/'

    # Members can view matches.
    self.client.force_authenticate(user=self.member)
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)

    # Members cannot edit or delete matches.
    response = self.client.patch(url, {'opponent': 'Changed RFC'})
    self.assertEqual(response.status_code, 403)

    response = self.client.delete(url)
    self.assertEqual(response.status_code, 403)

    # Members cannot create matches.
    response = self.client.post('/api/matches/', {
        'opponent': 'New RFC',
        'date': '2026-05-01',
        'status': 'upcoming',
        'wazimba_score': 0,
        'opponent_score': 0,
        'season': self.season.id,
    })
    self.assertEqual(response.status_code, 403)

    # The original match remains unchanged.
    self.match.refresh_from_db()
    self.assertEqual(self.match.opponent, 'Test RFC')


def test_players_are_read_only_for_members(self):
    url = f'/api/players/{self.player.id}/'

    # Members can view player records.
    self.client.force_authenticate(user=self.member)
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)

    # Members cannot edit or delete player records.
    response = self.client.patch(url, {'full_name': 'Changed Player'})
    self.assertEqual(response.status_code, 403)

    response = self.client.delete(url)
    self.assertEqual(response.status_code, 403)

    # Members cannot create player records.
    response = self.client.post('/api/players/', {
        'full_name': 'New Player',
        'position': 'Centre',
        'status': 'active',
    })
    self.assertEqual(response.status_code, 403)

    # The original player remains unchanged.
    self.player.refresh_from_db()
    self.assertEqual(self.player.full_name, 'Test Player')


def test_seasons_are_read_only_for_members(self):
    url = f'/api/seasons/{self.season.id}/'

    # Members can view season information.
    self.client.force_authenticate(user=self.member)
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)

    # Members cannot edit or delete seasons.
    response = self.client.patch(url, {'name': 'Changed Season'})
    self.assertEqual(response.status_code, 403)

    response = self.client.delete(url)
    self.assertEqual(response.status_code, 403)

    # Members cannot create seasons.
    response = self.client.post('/api/seasons/', {
        'name': 'New Season',
        'start_date': '2027-01-01',
        'status': 'upcoming',
    })
    self.assertEqual(response.status_code, 403)

    # The original season remains unchanged.
    self.season.refresh_from_db()
    self.assertEqual(self.season.name, '2026 Season')


def test_match_participations_are_read_only_for_members(self):
    participation = MatchParticipation.objects.get(
        match=self.match,
        player=self.player,
    )
    url = f'/api/match-participations/{participation.id}/'

    # Members can view participation statistics.
    self.client.force_authenticate(user=self.member)
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)

    # Members cannot edit or delete participation records.
    response = self.client.patch(url, {'tries': 5})
    self.assertEqual(response.status_code, 403)

    response = self.client.delete(url)
    self.assertEqual(response.status_code, 403)

    # Members cannot create participation records.
    response = self.client.post('/api/match-participations/', {
        'match': self.match.id,
        'player': self.player.id,
        'started': True,
        'minutes_played': 40,
        'tries': 5,
        'tackles': 7,
        'assists': 1,
        'turnovers_won': 1,
        'errors': 0,
    })
    self.assertEqual(response.status_code, 403)

    # The original statistics remain unchanged.
    participation.refresh_from_db()
    self.assertEqual(participation.tries, 2)


def test_training_sessions_are_read_only_for_members(self):
    url = f'/api/training-sessions/{self.session.id}/'

    # Members can view training sessions.
    self.client.force_authenticate(user=self.member)
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)

    # Members cannot edit or delete training sessions.
    response = self.client.patch(url, {'title': 'Changed Training'})
    self.assertEqual(response.status_code, 403)

    response = self.client.delete(url)
    self.assertEqual(response.status_code, 403)

    # Members cannot create training sessions.
    response = self.client.post('/api/training-sessions/', {
        'title': 'New Training',
        'date': '2026-05-01',
        'start_time': '17:00:00',
        'season': self.season.id,
    })
    self.assertEqual(response.status_code, 403)

    # The original session remains unchanged.
    self.session.refresh_from_db()
    self.assertEqual(self.session.title, 'Defence')


def test_alumni_profiles_are_read_only_for_members(self):
    alumni = AlumniProfile.objects.create(
        full_name='Former Player',
        email='alumni@example.com',
        consent_to_share_contact=True,
    )
    url = f'/api/alumni/{alumni.id}/'

    # Members can view alumni profiles.
    self.client.force_authenticate(user=self.member)
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)

    # Members cannot edit or delete profiles.
    response = self.client.patch(url, {'full_name': 'Changed Name'})
    self.assertEqual(response.status_code, 403)

    response = self.client.delete(url)
    self.assertEqual(response.status_code, 403)

    # Members cannot create profiles.
    response = self.client.post('/api/alumni/', {
        'full_name': 'New Alumni',
        'email': 'newalumni@example.com',
    })
    self.assertEqual(response.status_code, 403)

    # The original profile remains unchanged.
    alumni.refresh_from_db()
    self.assertEqual(alumni.full_name, 'Former Player')


def test_dashboard_requires_authentication(self):
    url = '/api/dashboard/'

    # Unauthenticated visitors must not access the dashboard.
    self.client.force_authenticate(user=None)
    response = self.client.get(url)
    self.assertEqual(response.status_code, 401)

    # Authenticated members can view the dashboard.
    self.client.force_authenticate(user=self.member)
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)

    # Verify that the dashboard returns its expected information.
    self.assertIn('active_players', response.data)
    self.assertIn('matches_played', response.data)
    self.assertIn('upcoming_matches', response.data)
    self.assertIn('recent_announcements', response.data)


    def test_inactive_users_cannot_log_in(self):
        User = get_user_model()
        inactive_user = User.objects.create_user(
            username='inactive_player',
            password='test-pass-123',
            is_active=False,
        )

        response = self.client.post(
            '/api/auth/token/',
            {
                'username': 'inactive_player',
                'password': 'test-pass-123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn('token', response.data)
        self.assertFalse(
            Token.objects.filter(user=inactive_user).exists()
        )
