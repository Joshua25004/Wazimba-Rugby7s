from django.conf import settings
from django.db import models

class Season(models.Model):
    class Status(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
    name = models.CharField(max_length=80, unique=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.UPCOMING)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class Player(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INJURED = 'injured', 'Injured'
        SUSPENDED = 'suspended', 'Suspended'
        INACTIVE = 'inactive', 'Inactive'
    full_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    position = models.CharField(max_length=40, blank=True)
    jersey_number = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    seasons = models.ManyToManyField(Season, through='SeasonRegistration', related_name='players', blank=True)
    joined_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['full_name']
    def __str__(self): return self.full_name

class SeasonRegistration(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    registered_at = models.DateField(auto_now_add=True)
    class Meta: constraints = [models.UniqueConstraint(fields=['player', 'season'], name='unique_player_season')]

class Tournament(models.Model):
    class Status(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        ONGOING = 'ongoing', 'Ongoing'
        COMPLETED = 'completed', 'Completed'
    name = models.CharField(max_length=160)
    location = models.CharField(max_length=160, blank=True)
    organizer = models.CharField(max_length=160, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.UPCOMING)
    official_url = models.URLField(blank=True)
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True, related_name='tournaments')
    def __str__(self): return self.name

class Match(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    opponent = models.CharField(max_length=160)
    date = models.DateField()
    venue = models.CharField(max_length=160, blank=True)
    competition_name = models.CharField(max_length=160, blank=True)
    tournament = models.ForeignKey(Tournament, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches')
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCHEDULED)
    wazimba_score = models.PositiveSmallIntegerField(null=True, blank=True)
    opponent_score = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-date']
    def __str__(self): return f'Wazimba vs {self.opponent} ({self.date})'

class MatchParticipation(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='participations')
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='match_participations')
    started = models.BooleanField(default=False)
    minutes_played = models.PositiveSmallIntegerField(default=0)
    tries = models.PositiveSmallIntegerField(default=0)
    assists = models.PositiveSmallIntegerField(default=0)
    tackles = models.PositiveSmallIntegerField(default=0)
    turnovers_won = models.PositiveSmallIntegerField(default=0)
    errors = models.PositiveSmallIntegerField(default=0)
    class Meta: constraints = [models.UniqueConstraint(fields=['match', 'player'], name='unique_match_player')]

class TrainingSession(models.Model):
    title = models.CharField(max_length=160)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=160, blank=True)
    session_type = models.CharField(max_length=40, blank=True)
    objectives = models.TextField(blank=True)
    drills = models.TextField(blank=True)
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True, related_name='training_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['date', 'start_time']
    def __str__(self): return self.title

class TrainingAttendance(models.Model):
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='attendance')
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='training_attendance')
    attended = models.BooleanField(default=False)
    notes = models.CharField(max_length=240, blank=True)
    class Meta: constraints = [models.UniqueConstraint(fields=['session', 'player'], name='unique_session_player')]

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=40, default='General')
    body = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    published_at = models.DateField(auto_now_add=True)
    is_published = models.BooleanField(default=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta: ordering = ['-published_at', '-id']
    def __str__(self): return self.title

class MatchReview(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='review')
    went_well = models.TextField(blank=True)
    needs_work = models.TextField(blank=True)
    tactical_observations = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    training_objectives = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

class TeamEvent(models.Model):
    class Category(models.TextChoices):
        MEETING = 'meeting', 'Meeting'
        BONDING = 'bonding', 'Team bonding'
        WELFARE = 'welfare', 'Welfare'
        FUNDRAISING = 'fundraising', 'Fundraising'
        OTHER = 'other', 'Other'
    title = models.CharField(max_length=160)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['date', 'start_time']
    def __str__(self): return self.title

class TeamEventAttendance(models.Model):
    event = models.ForeignKey(TeamEvent, on_delete=models.CASCADE, related_name='attendance')
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='event_attendance')
    attended = models.BooleanField(default=False)
    notes = models.CharField(max_length=240, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['event', 'player'], name='unique_event_player')]
        ordering = ['event__date', 'player__full_name']

class LearningResource(models.Model):
    class Category(models.TextChoices):
        LAW = 'law', 'Rules & laws'
        TACTICS = 'tactics', 'Tactical learning'
        VIDEO = 'video', 'Video resource'
        NEWS = 'news', 'Rugby news'
        SAFETY = 'safety', 'Safety & welfare'
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=Category.choices)
    summary = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    is_official = models.BooleanField(default=False)
    published_at = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-published_at', 'title']
    def __str__(self): return self.title

class MediaAsset(models.Model):
    class Category(models.TextChoices):
        MATCH = 'match', 'Match'
        TRAINING = 'training', 'Training'
        TOURNAMENT = 'tournament', 'Tournament'
        EVENT = 'event', 'Team event'
        TEAM = 'team', 'Team photo'
    title = models.CharField(max_length=180)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.MATCH)
    media_url = models.URLField()
    consent_confirmed = models.BooleanField(default=False)
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True, related_name='media')
    match = models.ForeignKey(Match, on_delete=models.SET_NULL, null=True, blank=True, related_name='media')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

class InjuryRecord(models.Model):
    class Status(models.TextChoices):
        ASSESSED = 'assessed', 'Assessed'
        RECOVERING = 'recovering', 'Recovering'
        RETURN_TRAINING = 'return_training', 'Return to training'
        RETURN_PLAY = 'return_play', 'Return to play'
    player = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='injury_records')
    injury_date = models.DateField()
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ASSESSED)
    staff_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-injury_date']
    def __str__(self): return f'{self.player} — {self.injury_date}'

class AlumniProfile(models.Model):
    full_name = models.CharField(max_length=160)
    former_position = models.CharField(max_length=40, blank=True)
    seasons_played = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_consent = models.BooleanField(default=False)
    mentorship_available = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['full_name']
    def __str__(self): return self.full_name
