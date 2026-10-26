from rest_framework import serializers
from .models import AccountAuditLog, AlumniProfile, Announcement, InjuryRecord, LearningResource, NewsArticle, Match, MatchParticipation, MatchReview, MediaAsset, Player, Season, SeasonRegistration, TeamEvent, TeamEventAttendance, Tournament, TrainingAttendance, TrainingSession


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
    class Meta:
        model = TrainingAttendance
        fields = '__all__'
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not (request and request.user.is_staff):
            data['notes'] = ''
        return data

class TeamEventSerializer(serializers.ModelSerializer):
    class Meta: model = TeamEvent; fields = '__all__'
class TeamEventAttendanceSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    class Meta: model = TeamEventAttendance; fields = '__all__'
class LearningResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningResource
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']
    def validate(self, attrs):
        upload = attrs.get('uploaded_file')
        if upload:
            from django.conf import settings
            if upload.size > settings.MAX_VIDEO_UPLOAD_SIZE:
                raise serializers.ValidationError({'uploaded_file': 'Video files must be 500 MB or smaller.'})
            if upload.name.rsplit('.', 1)[-1].lower() not in {'mp4', 'webm', 'ogg'}:
                raise serializers.ValidationError({'uploaded_file': 'Upload an MP4, WebM, or Ogg video.'})
            if upload.content_type not in {'video/mp4', 'video/webm', 'video/ogg', 'application/ogg'}:
                raise serializers.ValidationError({'uploaded_file': 'The uploaded file must have a supported video content type.'})
            upload.seek(0); signature = upload.read(16); upload.seek(0)
            extension = upload.name.rsplit('.', 1)[-1].lower()
            valid_signature = (extension == 'mp4' and signature[4:8] == b'ftyp') or (extension == 'webm' and signature.startswith(b'\x1aE\xdf\xa3')) or (extension == 'ogg' and signature.startswith(b'OggS'))
            if not valid_signature:
                raise serializers.ValidationError({'uploaded_file': 'The file contents do not match a supported video format.'})
        embed_url = attrs.get('embed_url')
        if embed_url:
            from urllib.parse import urlparse
            host = urlparse(embed_url).hostname or ''
            if not (host == 'youtu.be' or host == 'youtube.com' or host.endswith('.youtube.com') or host == 'youtube-nocookie.com' or host.endswith('.youtube-nocookie.com') or host == 'vimeo.com' or host.endswith('.vimeo.com')):
                raise serializers.ValidationError({'embed_url': 'Use a YouTube or Vimeo video URL.'})
        return attrs

class NewsArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = '__all__'
        read_only_fields = ['author', 'created_at']
    def validate(self, attrs):
        kind = attrs.get('kind', getattr(self.instance, 'kind', NewsArticle.Kind.ORIGINAL))
        body = attrs.get('body', getattr(self.instance, 'body', ''))
        source_url = attrs.get('source_url', getattr(self.instance, 'source_url', ''))
        if kind == NewsArticle.Kind.ORIGINAL and not body.strip():
            raise serializers.ValidationError({'body': 'Original Wazimba articles need article text.'})
        if kind == NewsArticle.Kind.EXTERNAL and not source_url:
            raise serializers.ValidationError({'source_url': 'Curated external stories need a link to the publisher.'})
        image = attrs.get('image_file')
        if image:
            from django.conf import settings
            if image.size > settings.MAX_NEWS_IMAGE_SIZE:
                raise serializers.ValidationError({'image_file': 'The image exceeds the configured upload size limit.'})
            if image.name.rsplit('.', 1)[-1].lower() not in {'jpg', 'jpeg', 'png', 'webp'}:
                raise serializers.ValidationError({'image_file': 'Upload a JPG, PNG, or WebP image.'})
            if image.content_type not in {'image/jpeg', 'image/png', 'image/webp'}:
                raise serializers.ValidationError({'image_file': 'The uploaded file must have a supported image content type.'})
            image.seek(0); signature = image.read(12); image.seek(0)
            extension = image.name.rsplit('.', 1)[-1].lower()
            valid_signature = (extension in {'jpg', 'jpeg'} and signature.startswith(b'\xff\xd8\xff')) or (extension == 'png' and signature.startswith(b'\x89PNG\r\n\x1a\n')) or (extension == 'webp' and signature.startswith(b'RIFF') and signature[8:12] == b'WEBP')
            if not valid_signature:
                raise serializers.ValidationError({'image_file': 'The file contents do not match a supported image format.'})
        return attrs

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
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import UserProfile

class AccountAuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    target_name = serializers.SerializerMethodField()
    class Meta:
        model = AccountAuditLog
        fields = ['id', 'actor_name', 'target_name', 'action', 'changes', 'created_at']
    def get_actor_name(self, obj): return obj.actor.get_full_name() or obj.actor.username if obj.actor else 'Deleted user'
    def get_target_name(self, obj): return obj.target.get_full_name() or obj.target.username if obj.target else 'Deleted account'

class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    full_name = serializers.CharField(max_length=160)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirmation = serializers.CharField(write_only=True, trim_whitespace=False)
    accepted_terms = serializers.BooleanField()
    def validate(self, attrs):
        User = get_user_model()
        if attrs['password'] != attrs['password_confirmation']:
            raise serializers.ValidationError({'password_confirmation': 'Passwords do not match.'})
        if not attrs['accepted_terms']:
            raise serializers.ValidationError({'accepted_terms': 'You must accept the account terms.'})
        if User.objects.filter(username__iexact=attrs['username']).exists():
            raise serializers.ValidationError({'username': 'This username is already in use.'})
        if User.objects.filter(email__iexact=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'This email is already in use.'})
        candidate = User(username=attrs['username'], email=attrs['email'], first_name=attrs['full_name'].split()[0], last_name=' '.join(attrs['full_name'].split()[1:]))
        try: password_validation.validate_password(attrs['password'], candidate)
        except DjangoValidationError as exc: raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs
    def create(self, validated_data):
        User = get_user_model()
        names = validated_data.pop('full_name').split()
        validated_data.pop('password_confirmation'); validated_data.pop('accepted_terms')
        password = validated_data.pop('password')
        username = validated_data.pop('username'); email = validated_data.pop('email')
        user = User(username=username, email=email, first_name=names[0], last_name=' '.join(names[1:]), is_staff=False, is_superuser=False)
        user.set_password(password); user.save()
        UserProfile.objects.update_or_create(user=user, defaults={'role': UserProfile.Role.MEMBER})
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'name', 'email', 'role', 'designation', 'can_access_welfare', 'is_active']
    def get_name(self, obj): return obj.user.get_full_name() or obj.user.username

class AccountUpdateSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(write_only=True, required=False)
    class Meta:
        model = UserProfile
        fields = ['role', 'designation', 'can_access_welfare', 'is_active']
    def validate(self, attrs):
        role = attrs.get('role', self.instance.role)
        if attrs.get('can_access_welfare', False) and role == UserProfile.Role.MEMBER:
            raise serializers.ValidationError({'can_access_welfare': 'Welfare access can only be assigned to staff or administrators.'})
        return attrs
    def update(self, instance, validated_data):
        active = validated_data.pop('is_active', None)
        for key, value in validated_data.items(): setattr(instance, key, value)
        if instance.role == UserProfile.Role.MEMBER:
            instance.can_access_welfare = False
        instance.save()
        if active is not None:
            instance.user.is_active = active; instance.user.save(update_fields=['is_active'])
        return instance
