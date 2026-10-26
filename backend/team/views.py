from django.contrib.auth import authenticate, get_user_model
import csv
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from .models import AccountAuditLog, UserProfile, AlumniProfile, Announcement, InjuryRecord, LearningResource, NewsArticle, Match, MatchParticipation, MatchReview, MediaAsset, Player, Season, SeasonRegistration, TeamEvent, TeamEventAttendance, Tournament, TrainingAttendance, TrainingSession
from .permissions import AdministratorOnly, ReadOnlyOrStaff, WelfareStaffOnly, app_role, has_welfare_access
from .serializers import AccountAuditLogSerializer, AccountUpdateSerializer, RegistrationSerializer, UserProfileSerializer, AlumniProfileSerializer, AnnouncementSerializer, InjuryRecordSerializer, LearningResourceSerializer, NewsArticleSerializer, MatchParticipationSerializer, MatchReviewSerializer, MatchSerializer, MediaAssetSerializer, PlayerSerializer, SeasonRegistrationSerializer, SeasonSerializer, TeamEventAttendanceSerializer, TeamEventSerializer, TournamentSerializer, TrainingAttendanceSerializer, TrainingSessionSerializer

class TokenLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    def post(self, request):
        user = authenticate(username=request.data.get('username'), password=request.data.get('password'))
        if not user or not user.is_active:
            return Response({'detail': 'Invalid username or password.'}, status=400)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'name': user.get_full_name() or user.get_username(), 'is_staff': user.is_staff, 'role': app_role(user)})

class CurrentUserView(APIView):
    def get(self, request):
        user = request.user
        return Response({'username': user.username, 'name': user.get_full_name() or user.username, 'is_staff': user.is_staff, 'role': app_role(user), 'designation': user.team_profile.designation, 'can_access_welfare': has_welfare_access(user)})

class LogoutView(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response({'detail': 'Logged out successfully.'}, status=status.HTTP_200_OK)

class DashboardView(APIView):
    def get(self, request):
        active_season = Season.objects.filter(status=Season.Status.ACTIVE).first()
        matches = Match.objects.filter(season=active_season) if active_season else Match.objects.all()
        today = timezone.localdate()
        next_match = matches.filter(status=Match.Status.SCHEDULED, date__gte=today).order_by('date').first()
        upcoming_training = TrainingSession.objects.filter(date__gte=today)
        if active_season: upcoming_training = upcoming_training.filter(season=active_season)
        next_training = upcoming_training.order_by('date', 'start_time').first()
        completed = matches.filter(status=Match.Status.COMPLETED).exclude(wazimba_score__isnull=True).exclude(opponent_score__isnull=True)
        wins = completed.filter(wazimba_score__gt=F('opponent_score')).count()
        payload = {'active_season': SeasonSerializer(active_season).data if active_season else None,
            'active_players': Player.objects.filter(status=Player.Status.ACTIVE).count(),
            'matches_played': completed.count(), 'upcoming_matches': matches.filter(status=Match.Status.SCHEDULED, date__gte=today).count(),
            'training_sessions': TrainingSession.objects.filter(season=active_season).count() if active_season else TrainingSession.objects.count(), 'wins': wins,
            'win_rate': round(wins * 100 / completed.count()) if completed.exists() else None,
            'next_match': MatchSerializer(next_match).data if next_match else None,
            'next_training': TrainingSessionSerializer(next_training).data if next_training else None,
            'upcoming_events': TeamEventSerializer(TeamEvent.objects.filter(date__gte=today).order_by('date')[:5], many=True).data,
            'recent_announcements': AnnouncementSerializer(Announcement.objects.filter(is_published=True)[:5], many=True).data,
            'recent_news': NewsArticleSerializer(NewsArticle.objects.filter(is_published=True)[:4], many=True).data}
        if app_role(request.user) == UserProfile.Role.ADMINISTRATOR:
            payload['accounts'] = list(UserProfile.objects.values('role').annotate(total=Count('id'), active=Count('id', filter=Q(user__is_active=True))))
            payload['active_accounts'] = get_user_model().objects.filter(is_active=True).count()
            payload['inactive_accounts'] = get_user_model().objects.filter(is_active=False).count()
            payload['recent_admin_activity'] = AccountAuditLogSerializer(AccountAuditLog.objects.select_related('actor', 'target')[:8], many=True).data
        return Response(payload)

class StaffWriteViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadOnlyOrStaff]
    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response({'detail': 'This record is referenced by match, attendance, or welfare history and cannot be deleted.'}, status=status.HTTP_409_CONFLICT)
class PlayerViewSet(StaffWriteViewSet): queryset = Player.objects.all(); serializer_class = PlayerSerializer
class SeasonViewSet(StaffWriteViewSet): queryset = Season.objects.order_by('start_date', 'name'); serializer_class = SeasonSerializer
class SeasonRegistrationViewSet(StaffWriteViewSet): queryset = SeasonRegistration.objects.select_related('season', 'player').order_by('season__start_date', 'player__full_name'); serializer_class = SeasonRegistrationSerializer
class TournamentViewSet(StaffWriteViewSet): queryset = Tournament.objects.select_related('season').order_by('start_date', 'name'); serializer_class = TournamentSerializer
class MatchViewSet(StaffWriteViewSet): queryset = Match.objects.select_related('season', 'tournament').all(); serializer_class = MatchSerializer
class TrainingSessionViewSet(StaffWriteViewSet): queryset = TrainingSession.objects.select_related('season').all(); serializer_class = TrainingSessionSerializer
class AnnouncementViewSet(StaffWriteViewSet):
    serializer_class = AnnouncementSerializer
    def get_queryset(self):
        qs = Announcement.objects.all()
        return qs if self.request.user.is_staff else qs.filter(is_published=True)
    def perform_create(self, serializer): serializer.save(author=self.request.user)

class MatchReviewViewSet(StaffWriteViewSet):
    queryset = MatchReview.objects.select_related('match').order_by('-updated_at')
    serializer_class = MatchReviewSerializer

class MatchParticipationViewSet(StaffWriteViewSet):
    queryset = MatchParticipation.objects.select_related('player', 'match').order_by('-match__date', 'player__full_name')
    serializer_class = MatchParticipationSerializer

class TrainingAttendanceViewSet(StaffWriteViewSet):
    queryset = TrainingAttendance.objects.select_related('player', 'session').order_by('-session__date', 'player__full_name')
    serializer_class = TrainingAttendanceSerializer

class TeamEventViewSet(StaffWriteViewSet): queryset = TeamEvent.objects.select_related('season').all(); serializer_class = TeamEventSerializer
class TeamEventAttendanceViewSet(StaffWriteViewSet):
    queryset = TeamEventAttendance.objects.select_related('event', 'player').all()
    serializer_class = TeamEventAttendanceSerializer
class LearningResourceViewSet(StaffWriteViewSet):
    serializer_class = LearningResourceSerializer
    def get_queryset(self):
        qs = LearningResource.objects.select_related('created_by', 'season', 'match', 'training_session', 'event').all()
        return qs if self.request.user.is_staff else qs.filter(is_published=True)
    def perform_create(self, serializer): serializer.save(created_by=self.request.user)

class NewsArticleViewSet(StaffWriteViewSet):
    serializer_class = NewsArticleSerializer
    def get_queryset(self):
        qs = NewsArticle.objects.select_related('author').all()
        return qs if self.request.user.is_staff else qs.filter(is_published=True)
    def perform_create(self, serializer): serializer.save(author=self.request.user)
class MediaAssetViewSet(StaffWriteViewSet):
    serializer_class = MediaAssetSerializer
    def get_queryset(self):
        qs = MediaAsset.objects.select_related('season', 'match').order_by('-created_at')
        return qs if self.request.user.is_staff else qs.filter(consent_confirmed=True)
class AlumniProfileViewSet(StaffWriteViewSet): queryset = AlumniProfile.objects.all(); serializer_class = AlumniProfileSerializer

class InjuryRecordViewSet(StaffWriteViewSet):
    queryset = InjuryRecord.objects.select_related('player').all()
    serializer_class = InjuryRecordSerializer
    permission_classes = [WelfareStaffOnly]

def _season_matches(request):
    matches = Match.objects.filter(status=Match.Status.COMPLETED).exclude(wazimba_score__isnull=True).exclude(opponent_score__isnull=True)
    season_id = request.query_params.get('season')
    if season_id:
        season = _get_by_id(Season, season_id, 'season')
        matches = matches.filter(season=season)
    return matches.select_related('season', 'tournament').prefetch_related('participations__player', 'review')

def _get_by_id(model, value, field):
    try:
        pk = int(value)
    except (TypeError, ValueError):
        raise ValidationError({field: 'Enter a valid record ID.'})
    return get_object_or_404(model, pk=pk)

class TeamAnalyticsView(APIView):
    def get(self, request):
        matches = _season_matches(request)
        played = matches.count()
        wins = matches.filter(wazimba_score__gt=F('opponent_score')).count()
        losses = matches.filter(wazimba_score__lt=F('opponent_score')).count()
        draws = played - wins - losses
        points_for = matches.aggregate(total=Sum('wazimba_score'))['total'] or 0
        points_against = matches.aggregate(total=Sum('opponent_score'))['total'] or 0
        participation = MatchParticipation.objects.filter(match__in=matches).aggregate(
            appearances=Count('id'), tries=Sum('tries'), assists=Sum('assists'), tackles=Sum('tackles'), turnovers=Sum('turnovers_won'), errors=Sum('errors'))
        training = TrainingSession.objects.all()
        if request.query_params.get('season'):
            training = training.filter(season_id=request.query_params['season'])
        attendance = TrainingAttendance.objects.filter(session__in=training).aggregate(total=Count('id'), present=Count('id', filter=Q(attended=True)))
        match_rows = [{'id': m.id, 'date': m.date, 'opponent': m.opponent, 'score_for': m.wazimba_score, 'score_against': m.opponent_score,
                       'result': 'Win' if m.wazimba_score > m.opponent_score else 'Loss' if m.wazimba_score < m.opponent_score else 'Draw'} for m in matches.order_by('date')]
        return Response({'matches_played': played, 'wins': wins, 'losses': losses, 'draws': draws,
            'win_rate': round(wins * 100 / played, 1) if played else None,
            'points_for': points_for, 'points_against': points_against,
            'point_difference': points_for - points_against,
            'participation': {key: value or 0 for key, value in participation.items()},
            'training_sessions': training.count(), 'training_attendance_total': attendance['total'],
            'training_attendance_rate': round(attendance['present'] * 100 / attendance['total'], 1) if attendance['total'] else None,
            'match_results': match_rows})

class PlayerPerformanceView(APIView):
    def get(self, request):
        matches = _season_matches(request)
        rows = MatchParticipation.objects.filter(match__in=matches).values('player_id', 'player__full_name', 'player__position').annotate(
            appearances=Count('match', distinct=True), starts=Count('id', filter=Q(started=True)),
            minutes=Sum('minutes_played'), tries=Sum('tries'), assists=Sum('assists'), tackles=Sum('tackles'),
            turnovers_won=Sum('turnovers_won'), errors=Sum('errors')).order_by('-tries', '-appearances', 'player__full_name')
        player_id = request.query_params.get('player')
        if player_id:
            _get_by_id(Player, player_id, 'player')
            rows = rows.filter(player_id=player_id)
        return Response(list(rows))

class ReportsView(APIView):
    def get(self, request):
        analytics = TeamAnalyticsView().get(request).data
        players = PlayerPerformanceView().get(request).data
        season_id = request.query_params.get('season')
        matches = Match.objects.filter(status=Match.Status.COMPLETED)
        season = _get_by_id(Season, season_id, 'season') if season_id else None
        if season: matches = matches.filter(season=season)
        sessions = TrainingSession.objects.all()
        if season: sessions = sessions.filter(season=season)
        return Response({'season': SeasonSerializer(season).data if season else None,
            'team': analytics, 'players': players, 'training_sessions': sessions.count(), 'matches': analytics['match_results']})

class ReportsCSVView(APIView):
    def get(self, request):
        payload = ReportsView().get(request).data
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="wazimba-season-report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Wazimba Rugby 7s season report', payload['season']['name'] if payload['season'] else 'All seasons'])
        writer.writerow(['Matches played', payload['team']['matches_played'], 'Wins', payload['team']['wins'], 'Losses', payload['team']['losses'], 'Draws', payload['team']['draws']])
        writer.writerow(['Points for', payload['team']['points_for'], 'Points against', payload['team']['points_against'], 'Win rate (%)', payload['team']['win_rate'] if payload['team']['win_rate'] is not None else ''])
        writer.writerow([]); writer.writerow(['Match date', 'Opponent', 'Wazimba points', 'Opponent points', 'Result'])
        for match in payload['matches']:
            writer.writerow([match['date'], match['opponent'], match['score_for'], match['score_against'], match['result']])
        writer.writerow([]); writer.writerow(['Player', 'Position', 'Appearances', 'Minutes', 'Tries', 'Assists', 'Tackles', 'Turnovers won', 'Errors'])
        for player in payload['players']:
            writer.writerow([player['player__full_name'], player['player__position'], player['appearances'], player['minutes'] or 0, player['tries'] or 0, player['assists'] or 0, player['tackles'] or 0, player['turnovers_won'] or 0, player['errors'] or 0])
        return response


class RegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'detail': 'Account created. You can now sign in.', 'username': user.username}, status=status.HTTP_201_CREATED)

class AccountManagementView(APIView):
    permission_classes = [AdministratorOnly]
    def get(self, request):
        from django.contrib.auth import get_user_model
        profiles = UserProfile.objects.select_related('user').filter(user__username__icontains=request.query_params.get('search', '')).order_by('user__username')
        return Response(UserProfileSerializer(profiles, many=True).data)
    @transaction.atomic
    def patch(self, request, pk):
        from django.contrib.auth import get_user_model
        profile = get_object_or_404(UserProfile.objects.select_related('user'), pk=pk)
        serializer = AccountUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        target = profile.user
        before = {'role': profile.role, 'designation': profile.designation, 'can_access_welfare': profile.can_access_welfare, 'is_active': target.is_active}
        next_role = serializer.validated_data.get('role', profile.role)
        next_active = serializer.validated_data.get('is_active', target.is_active)
        if profile.role == UserProfile.Role.ADMINISTRATOR and target.is_active and (next_role != UserProfile.Role.ADMINISTRATOR or not next_active):
            admins = UserProfile.objects.select_for_update().filter(role=UserProfile.Role.ADMINISTRATOR, user__is_active=True).exclude(pk=profile.pk).count()
            if admins == 0:
                return Response({'detail': 'At least one active administrator must remain.'}, status=409)
        if target.pk == request.user.pk and (next_role != UserProfile.Role.ADMINISTRATOR or not next_active):
            return Response({'detail': 'You cannot remove your own administrator access.'}, status=409)
        profile = serializer.save()
        # Keep Django admin access aligned with application roles.
        profile.user.is_staff = profile.role in (UserProfile.Role.STAFF, UserProfile.Role.ADMINISTRATOR)
        profile.user.is_superuser = profile.role == UserProfile.Role.ADMINISTRATOR and profile.user.is_superuser
        profile.user.save(update_fields=['is_staff', 'is_superuser'])
        after = {'role': profile.role, 'designation': profile.designation, 'can_access_welfare': profile.can_access_welfare, 'is_active': profile.user.is_active}
        changes = {key: {'from': before[key], 'to': after[key]} for key in before if before[key] != after[key]}
        if changes:
            AccountAuditLog.objects.create(actor=request.user, target=profile.user, changes=changes)
        return Response(UserProfileSerializer(profile).data)

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    def post(self, request):
        from django.conf import settings
        from django.contrib.auth import get_user_model
        from django.contrib.auth.tokens import default_token_generator
        from django.core.mail import send_mail
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        email = request.data.get('email', '')
        for user in get_user_model().objects.filter(email__iexact=email, is_active=True):
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            base = getattr(settings, 'PUBLIC_FRONTEND_URL', 'http://localhost:5173/')
            link = f"{base}?reset=1&uid={uid}&token={token}"
            send_mail('Reset your Wazimba password', f"Use this secure link to reset your password. It expires automatically.\n\n{link}", settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        return Response({'detail': 'If an account uses that email, reset instructions have been sent.'})

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    def post(self, request):
        from django.contrib.auth import get_user_model, password_validation
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_decode
        uid = request.data.get('uid', '')
        try: user = get_user_model().objects.get(pk=urlsafe_base64_decode(uid).decode())
        except Exception: user = None
        if not user or not default_token_generator.check_token(user, request.data.get('token', '')):
            return Response({'detail': 'This password reset link is invalid or has expired.'}, status=400)
        password = request.data.get('password', '')
        try: password_validation.validate_password(password, user)
        except Exception as exc: return Response({'password': getattr(exc, 'messages', ['Choose a stronger password.'])}, status=400)
        user.set_password(password); user.save(update_fields=['password'])
        Token.objects.filter(user=user).delete()
        return Response({'detail': 'Password changed. Please sign in again.'})

