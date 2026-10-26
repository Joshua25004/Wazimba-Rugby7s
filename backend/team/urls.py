from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import NewsArticleViewSet, AlumniProfileViewSet, AnnouncementViewSet, InjuryRecordViewSet, LearningResourceViewSet, MatchParticipationViewSet, MatchReviewViewSet, MatchViewSet, MediaAssetViewSet, PlayerPerformanceView, PlayerViewSet, ReportsCSVView, ReportsView, SeasonRegistrationViewSet, SeasonViewSet, TeamAnalyticsView, TeamEventAttendanceViewSet, TeamEventViewSet, TournamentViewSet, TrainingAttendanceViewSet, TrainingSessionViewSet

router = DefaultRouter()
router.register('players', PlayerViewSet)
router.register('seasons', SeasonViewSet)
router.register('season-registrations', SeasonRegistrationViewSet)
router.register('tournaments', TournamentViewSet)
router.register('matches', MatchViewSet)
router.register('training-sessions', TrainingSessionViewSet)
router.register('announcements', AnnouncementViewSet, basename='announcement')
router.register('match-reviews', MatchReviewViewSet)
router.register('match-participations', MatchParticipationViewSet)
router.register('training-attendance', TrainingAttendanceViewSet)
router.register('team-events', TeamEventViewSet)
router.register('team-event-attendance', TeamEventAttendanceViewSet)
router.register('learning-resources', LearningResourceViewSet, basename='learning-resource')
router.register('news', NewsArticleViewSet, basename='news-article')
router.register('media', MediaAssetViewSet, basename='media-asset')
router.register('injury-records', InjuryRecordViewSet)
router.register('alumni', AlumniProfileViewSet)

urlpatterns = [
    path('performance/team/', TeamAnalyticsView.as_view(), name='team-analytics'),
    path('performance/players/', PlayerPerformanceView.as_view(), name='player-performance'),
    path('reports/', ReportsView.as_view(), name='reports'),
    path('reports/csv/', ReportsCSVView.as_view(), name='reports-csv'),
] + router.urls
