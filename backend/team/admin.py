from django.contrib import admin
from .models import AlumniProfile, Announcement, InjuryRecord, LearningResource, Match, MatchParticipation, MatchReview, MediaAsset, Player, Season, SeasonRegistration, TeamEvent, TeamEventAttendance, Tournament, TrainingAttendance, TrainingSession

admin.site.register([Player, Season, SeasonRegistration, Tournament, Match, MatchParticipation, TrainingSession, TrainingAttendance, Announcement, MatchReview, TeamEvent, TeamEventAttendance, LearningResource, MediaAsset, InjuryRecord, AlumniProfile])
