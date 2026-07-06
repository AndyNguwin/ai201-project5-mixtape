"""
tests/test_streaks.py — Mixtape

Tests for listening streak logic.
"""

import pytest
from datetime import datetime, timedelta, timezone
from app import create_app, db
from models import ListeningEvent, Song, User
from services.streak_service import record_listening_event, update_listening_streak, get_streak


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def user(app):
    with app.app_context():
        u = User(username="testuser", email="test@example.com")
        db.session.add(u)
        db.session.commit()
        yield u


def test_streak_starts_at_1_for_new_user(app, user):
    """A user with no prior listening history gets a streak of 1."""
    with app.app_context():
        u = db.session.get(User, user.id)
        now = datetime(2024, 6, 10, 12, 0, 0, tzinfo=timezone.utc)  # Monday
        update_listening_streak(u, now)
        assert u.listening_streak == 1


def test_streak_increments_on_consecutive_day(app, user):
    """Listening on consecutive days increments the streak."""
    with app.app_context():
        u = db.session.get(User, user.id)
        monday = datetime(2024, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
        tuesday = datetime(2024, 6, 11, 12, 0, 0, tzinfo=timezone.utc)

        update_listening_streak(u, monday)
        assert u.listening_streak == 1

        update_listening_streak(u, tuesday)
        assert u.listening_streak == 2

def test_streak_does_not_double_count_same_day(app, user):
    """Listening twice in the same day does not increment the streak twice."""
    with app.app_context():
        u = db.session.get(User, user.id)
        morning = datetime(2024, 6, 10, 9, 0, 0, tzinfo=timezone.utc)
        evening = datetime(2024, 6, 10, 20, 0, 0, tzinfo=timezone.utc)

        update_listening_streak(u, morning)
        assert u.listening_streak == 1

        update_listening_streak(u, evening)
        assert u.listening_streak == 1  # Should not change


def test_streak_resets_after_skipped_day(app, user):
    """Skipping a day resets the streak to 1."""
    with app.app_context():
        u = db.session.get(User, user.id)
        monday = datetime(2024, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
        wednesday = datetime(2024, 6, 12, 12, 0, 0, tzinfo=timezone.utc)

        update_listening_streak(u, monday)
        assert u.listening_streak == 1

        update_listening_streak(u, wednesday)
        assert u.listening_streak == 1  # Reset because Tuesday was skipped


def test_streak_increments_on_six_consecutive_day(app, user):
    """
    Listening on six consecutive days increments the streak.
    """
    with app.app_context():
        u = db.session.get(User, user.id)
        monday = datetime(2024, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
        tuesday = datetime(2024, 6, 11, 12, 0, 0, tzinfo=timezone.utc)
        wednesday = datetime(2024, 6, 12, 12, 0, 0, tzinfo=timezone.utc)
        thursday = datetime(2024, 6, 13, 12, 0, 0, tzinfo=timezone.utc)
        friday = datetime(2024, 6, 14, 12, 0, 0, tzinfo=timezone.utc)
        saturday = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

        update_listening_streak(u, monday)
        assert u.listening_streak == 1

        update_listening_streak(u, tuesday)
        assert u.listening_streak == 2

        update_listening_streak(u, wednesday)
        assert u.listening_streak == 3

        update_listening_streak(u, thursday)
        assert u.listening_streak == 4

        update_listening_streak(u, friday)
        assert u.listening_streak == 5

        update_listening_streak(u, saturday)
        assert u.listening_streak == 6


def test_streak_increments_on_sunday(app, user):
    """
    Listening on Saturday and then Sunday should increment the streak.
    """
    with app.app_context():
        u = db.session.get(User, user.id)
        saturday = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)  # weekday() == 5
        sunday = datetime(2024, 6, 16, 12, 0, 0, tzinfo=timezone.utc)    # weekday() == 6

        update_listening_streak(u, saturday)
        assert u.listening_streak == 1

        update_listening_streak(u, sunday)
        assert u.listening_streak == 2  # Should increment, not reset

def test_streak_increments_on_whole_week(app, user):
    """
    Listening on everyday in the week should increment the streak.
    """
    with app.app_context():
        u = db.session.get(User, user.id)
        monday = datetime(2024, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
        tuesday = datetime(2024, 6, 11, 12, 0, 0, tzinfo=timezone.utc)
        wednesday = datetime(2024, 6, 12, 12, 0, 0, tzinfo=timezone.utc)
        thursday = datetime(2024, 6, 13, 12, 0, 0, tzinfo=timezone.utc)
        friday = datetime(2024, 6, 14, 12, 0, 0, tzinfo=timezone.utc)
        saturday = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        sunday = datetime(2024, 6, 16, 12, 0, 0, tzinfo=timezone.utc)

        update_listening_streak(u, monday)
        assert u.listening_streak == 1

        update_listening_streak(u, tuesday)
        assert u.listening_streak == 2

        update_listening_streak(u, wednesday)
        assert u.listening_streak == 3

        update_listening_streak(u, thursday)
        assert u.listening_streak == 4

        update_listening_streak(u, friday)
        assert u.listening_streak == 5

        update_listening_streak(u, saturday)
        assert u.listening_streak == 6

        update_listening_streak(u, sunday)
        assert u.listening_streak == 7


def test_record_listening_event_creates_event_and_updates_streak(app, user):
    """Recording a listen creates an event and updates the user's streak."""
    with app.app_context():
        u = db.session.get(User, user.id)
        song = Song(
            title="Test Song",
            artist="Test Artist",
            shared_by=u.id,
        )
        db.session.add(song)
        db.session.commit()

        event = record_listening_event(u.id, song.id)

        saved_event = db.session.get(ListeningEvent, event.id)
        assert saved_event is not None
        assert saved_event.user_id == u.id
        assert saved_event.song_id == song.id
        assert saved_event.listened_at is not None
        assert get_streak(u.id) == 1
        assert u.last_listened_at is not None

def test_record_listening_event_on_same_day_does_not_increase_streak(app, user):
    """Recording two listens on the same day does not increase the user's streak."""
    with app.app_context():
        u = db.session.get(User, user.id)
        song = Song(
            title="Test Song",
            artist="Test Artist",
            shared_by=u.id,
        )
        db.session.add(song)
        db.session.commit()

        event = record_listening_event(u.id, song.id)
        event = record_listening_event(u.id, song.id)

        saved_events = db.session.query(ListeningEvent).filter_by(user_id=u.id, song_id=song.id).all()
        assert len(saved_events) == 2
        assert get_streak(u.id) == 1
        assert u.last_listened_at is not None