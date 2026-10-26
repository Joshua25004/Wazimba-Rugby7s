from django.contrib import admin
from .models import AccountAuditLog, UserProfile, AlumniProfile, Announcement, InjuryRecord, LearningResource, NewsArticle, Match, MatchParticipation, MatchReview, MediaAsset, Player, Season, SeasonRegistration, TeamEvent, TeamEventAttendance, Tournament, TrainingAttendance, TrainingSession

admin.site.register([Player, Season, SeasonRegistration, Tournament, Match, MatchParticipation, TrainingSession, TrainingAttendance, Announcement, MatchReview, TeamEvent, TeamEventAttendance, LearningResource, NewsArticle, MediaAsset, InjuryRecord, AlumniProfile])

admin.site.register(UserProfile)

admin.site.register(AccountAuditLog)
