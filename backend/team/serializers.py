from rest_framework import serializers
from .models import AlumniProfile, Announcement, InjuryRecord, LearningResource, Match, MatchParticipation, MatchReview, MediaAsset, Player, Season, SeasonRegistration, TeamEvent, TeamEventAttendance, Tournament, TrainingAttendance, TrainingSession


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        # Hide player email addresses from non-staff users.
        if not (request and request.user.is_staff):
            data['email'] = ''

        return data

class SeasonSerializer(serializers.ModelSerializer):
    class Meta: model = Season; fields = '__all__'
class SeasonRegistrationSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    season_name = serializers.CharField(source='season.name', read_only=True)
    class Meta: model = SeasonRegistration; fields = '__all__'
class TournamentSerializer(serializers.ModelSerializer):
    class Meta: model = Tournament; fields = '__all__'
class MatchSerializer(serializers.ModelSerializer):
    class Meta: model = Match; fields = '__all__'
class TrainingSessionSerializer(serializers.ModelSerializer):
    class Meta: model = TrainingSession; fields = '__all__'
class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta: model = Announcement; fields = '__all__'; read_only_fields = ['author', 'published_at']
class MatchReviewSerializer(serializers.ModelSerializer):
    class Meta: model = MatchReview; fields = '__all__'
class MatchParticipationSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    class Meta: model = MatchParticipation; fields = '__all__'
class TrainingAttendanceSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    class Meta: model = TrainingAttendance; fields = '__all__'
class TeamEventSerializer(serializers.ModelSerializer):
    class Meta: model = TeamEvent; fields = '__all__'
class TeamEventAttendanceSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    class Meta: model = TeamEventAttendance; fields = '__all__'
class LearningResourceSerializer(serializers.ModelSerializer):
    class Meta: model = LearningResource; fields = '__all__'; read_only_fields = ['created_by', 'created_at']
class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta: model = MediaAsset; fields = '__all__'
class InjuryRecordSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    class Meta: model = InjuryRecord; fields = '__all__'
class AlumniProfileSerializer(serializers.ModelSerializer):
    class Meta: model = AlumniProfile; fields = '__all__'
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not instance.contact_consent and not (request and request.user.is_staff):
            data['contact_email'] = ''
        return data
