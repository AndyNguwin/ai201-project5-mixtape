## Codebase Map
- ``app.py``: Creates and serves a Flask app, configured with SQLAlchemy ORM for database interactions and sets up the endpoint routes (outlined below)
- ``models.py``: Defines the SQLAlchemy database schema and object relationships for the Mixtape app. There are 7 models and 3 association tables.
    - Models
        - ``User``: Stores account id, username, email, listening streak count, last listened date, creation time, and relationships to shared songs, ratings, listening events, notifications, playlists, and friends.
        - ``Tag``: Stores unique tag names that can be attached to songs for categorization/search.
        - ``Song``: Stores song metadata such as id, title, artist, album, genre, sharing user, share time, optional share note, tags, ratings, and listening events.
        - ``ListeningEvent``: Records when a user listens to a song, supporting listening history and streak logic. Stores id, user_id, song_id, and when listened at.
        - ``Rating``: Stores a user's 1-5 score for a song, with a unique constraint so each user can rate each song only once. Stores id, user_id, song_id, score, and when rated at.
        - ``Playlist``: Stores user-created playlists with id, name, creating user, creation time, collaborative status, and associated songs through ``playlist_entries``. 
        - ``Notification``: Stores notifications with id, user_id, notification_type, body text, creation time, and read status.
    - Association Tables
        - ``friendships``: A many-to-many table connecting users to other users as friends.
        - ``song_tags``: A many-to-many table connecting songs with reusable tag records.
        - ``playlist_entries``: A many-to-many table connecting playlists and songs while also storing playlist order, who added each song, and when it was added.
- ``seed_data.py``: The script to populate the data tables defined above for initial data.
- Services
    - ``feed_service.py``: Contains the functions for querying social feed features. It queries users, friendships, songs, and listening events to build feed responses.
        - ``get_friends_listening_now(user_id)``: Finds the user's friends, checks which friends have listened within the recent 24-hour threshold, and returns each friend's most recent listening activity.
        - ``get_activity_feed(user_id, limit=20)``: Returns a general friend activity feed with the most recent listening events from all of the user's friends.
    - ``notification_service.py``: Handles notification creation and retrieval. Notifications are made when a friend interacts with a user's shared song.
        - ``create_notification(user_id, notification_type, body)``: Creates and saves a notification for a user.
        - ``add_to_playlist(playlist_id, song_id, added_by_user_id)``: Adds a song to a playlist and notifies the original song sharer when someone else adds their song.
        - ``rate_song(user_id, song_id, score)``: Validates a 1-5 song rating, creates a new rating or updates an existing one, and saves it.
        - ``get_notifications(user_id, unread_only=False)``: Returns a user's notifications, optionally filtering to unread notifications only.
        - ``mark_as_read(notification_id)``: Marks a notification as read.
    - ``playlist_service.py``: Handles playlist creation and playlist lookup.
        - ``create_playlist(name, created_by_user_id, is_collaborative=True)``: Validates the creator user and creates a playlist.
        - ``get_playlist_songs(playlist_id)``: Returns the songs in a playlist ordered by their playlist position.
        - ``get_playlist(playlist_id)``: Returns playlist metadata without the song list.
        - ``get_user_playlists(user_id)``: Returns all playlists created by a specific user.
    - ``search_service.py``: Handles song searching
        - ``search_songs(query)``: Searches songs by title or artist using case-insensitive matching and returns song results.
        - ``get_song(song_id)``: Searches one song by id and returns its details.
    - ``streak_service.py``: Handles listening event recording and user listening streak logic.
        - ``update_listening_streak(user, now)``: Applies the streak rules based on the user's last listening date.
        - ``record_listening_event(user_id, song_id)``: Creates a listening event for a user/song pair and updates the user's listening streak.
        - ``get_streak(user_id)``: Returns a user's current listening streak.
- Routes
    - ``feed.py``: Defines feed-related API endpoints. Connects to ``feed_service.py``.
        - ``listening_now(user_id)``: Handles ``GET /feed/<user_id>/listening-now`` by calling ``get_friends_listening_now`` and returning recent friend listening activity plus a count.
        - ``activity(user_id)``: Handles ``GET /feed/<user_id>/activity`` by calling ``get_activity_feed`` and returning the user's broader friend activity feed plus a count.
    - ``playlists.py``: Defines playlist API endpoints. Connects to ``playlist_service.py`` for playlist operations and ``notification_service.py`` when adding songs.
        - ``create()``: Handles ``POST /playlists/`` by validating playlist name and creator id, then calling ``create_playlist``.
        - ``get_detail(playlist_id)``: Handles ``GET /playlists/<playlist_id>`` by calling ``get_playlist`` to return playlist metadata.
        - ``get_songs(playlist_id)``: Handles ``GET /playlists/<playlist_id>/songs`` by calling ``get_playlist_songs`` to return the playlist's songs.
        - ``add_song(playlist_id)``: Handles ``POST /playlists/<playlist_id>/songs`` by validating song id and adding user id, then calling ``add_to_playlist``.
    - ``songs.py``: Defines song API endpoints. Connects to ``search_service.py`` for search/detail lookup, ``notification_service.py`` for ratings, and ``streak_service.py`` for listens.
        - ``search()``: Handles ``GET /songs/search`` by requiring a ``q`` query parameter, calling ``search_songs``, and returning matching songs plus a count.
        - ``get_song_detail(song_id)``: Handles ``GET /songs/<song_id>`` by calling ``get_song``.
        - ``rate(song_id)``: Handles ``POST /songs/<song_id>/rate`` by validating ``user_id`` and ``score``, then calling ``rate_song``.
        - ``listen(song_id)``: Handles ``POST /songs/<song_id>/listen`` by validating ``user_id``, then calling ``record_listening_event``.
    - ``users.py``: Defines user API endpoints. Connects directly to the ``User`` model for profile lookup, ``streak_service.py`` for streaks, and ``notification_service.py`` for notifications.
        - ``get_user(user_id)``: Handles ``GET /users/<user_id>`` by looking up a user through SQLAlchemy and returning serialized profile data.
        - ``streak(user_id)``: Handles ``GET /users/<user_id>/streak`` by calling ``get_streak``.
        - ``notifications(user_id)``: Handles ``GET /users/<user_id>/notifications`` by calling ``get_notifications`` and supporting ``unread_only=true``.
        - ``read_notification(notification_id)``: Handles ``POST /users/notifications/<notification_id>/read`` by calling ``mark_as_read``.
- Tests: Simple PyTest scripts to test the service
    - ``test_playlists.py``
    - ``test_search.py``
    - ``test_streaks.py``

### Example Data Flow
- A user listens to a song: client sends request ``POST /songs/<song_id>/listen`` in ``routes/songs.py`` which calls ``streak_service.record_listening_event(user_id, song_id)`` from ``services/streak_service.py``. This creates a ``ListeningEvent`` record that stores which user (``user_id``) listened to which song (``song_id``) at what time (``listened_at``).

## Bug Investigation Writeups

### Issue 1: My listening streak keeps resetting

#### Reproduction
- What inputs, sequence of actions, or data condition triggered the behavior?
    - A user whose last listen was Saturday and whose next listen happens on Sunday.
    - Any valid ``song_id``.
    - The live Flask route can only naturally reproduce this if the current system day is Sunday, because the route uses the real current system time.
- What steps did you take to confirm the bug exists before touching any code?
    1. I read over the ``test_streaks.py`` script and ran it to see which cases were outlined and handled correctly. All of the cases passed except for one where the streak is supposed to incremented on Sunday, which failed.  
    2. To check using the Flask app, I added in the seed data, ran a script for all of the user_ids of the users and song_ids of the songs, and checked the result returned from ``/users/<user_id>`` to see which user last listened day was yesterday.
    3. Since the Flask route depends on ``datetime.now(timezone.utc)``, I could not force the route to behave like it was Sunday unless the system date was actually Sunday and I didn't want want to convert it.
    4. Instead, I extended the ``test_streaks.py`` script to confirm it was specifically just Sunday. I duplicated and extended a previous test from two consecutive days to six consecutive days, stopping right before Sunday, to check if the streak incrementing works on the other six days of the week.
    5. I also made another test that tested the every day of the week consecutively (including Sunday).

#### Finding the Root Cause
- Which files did you look at? What was your navigation path?
    1. ``routes/users.py`` for finding a user's streak information
    2. ``services/streak_service.py`` to see the functions that handles streaks and to find where these functions are called. I saw that ``streak_service.record_listening_event()`` calls ``streak_service.update_listening_streak()``.
    3. ``routes/songs.py`` to find when ``streak_service.record_listening_event()`` gets called and inspecting if any of the inputs were incorrect before checking the updating listening streak function. It also would let me test the endpoint myself on the Flask app.
    4. Couldn't test the endpoint since it was conditional on real-life days or what the system clock says, so I checked the ``tests/test_streaks.py``.
    4. Went back to ``services/streak_service.py`` to inspect the functions themselves, specifically ``streak_service.update_listening_streak()`` which was called in the tests.
- What moment made you confident you'd found the right place, not just a suspicious area, but the specific cause?
    - Once I saw that the test itself called the ``update_listening_streak`` function for testing the streak incrementing logic, I knew I found the right spot to start debugging. I checked the function itself to read over and understand what it was doing.

#### Root Cause
- In ``services/streak_service.py``, the ``update_listening_streak`` function has this code snippet for updating streak:
```python
if days_since_last == 0:
    # Already updated today — no change needed
    return
elif days_since_last == 1 and today.weekday() != 6:
    user.listening_streak += 1
else:
    user.listening_streak = 1
```
- The main thing to look at is the ``python elif days_since_last == 1 and today.weekday() != 6:``. Because of the second part of that conditional, whenever the day is Sunday (which returns 6 by today.weekday()), it won't increment the streak. Because of that, it goes into the else statement where streak gets reset to 1.

#### Fix & Side-Effect Check
- What did you change?
    - I removed the second part of the conditional that checks if the weekday isn't Sunday.
- Why does that change fix the root cause?
    -  The streak should increase on every day of the week, including Sunday.
- What related functionality did you check afterward to confirm you didn't break anything?
    - I reran the test cases to ensure the streak was correctly incremented.
    - I added two tests to make sure the simple cases of adding a listening event for a new User with ``streak_service.record_listening_event()``, which calls ``streak_service.update_listening_streak()`` still correctly increases the streak to 1 and calling it on the same day doesn't duplicate the increase.
    - It's not possible to test with specific datetimes for ``streak_service.record_listening_event()`` as it grabs the datetime to pass into the streak updating function from the system time rather than getting it as input.
    
### Issue 5: The last song in a playlist never shows up  

#### Reproduction
- What inputs, sequence of actions, or data condition triggered the behavior?
    - The seeded playlists with 7 songs each
    - Any playlist with one or more songs triggers the behavior
    - ``GET /playlists/<playlist_id>/songs`` triggers this behavior

- What steps did you take to confirm the bug exists before touching any code?
    1. I inspected the seed data script to see how many songs were added into playlists (each had 7)
    2. I queried for the playlist ids that are in the database
    3. I made a ``GET http://127.0.0.1:5000/playlists/<playlist_id>/songs`` to get details of how many songs are returned back (only 6)
    4. To confirm it was the last song that is being left out, I created a script to get all the songs in each playlist from the database ordered by insertion.
    5. I cross-referenced the list of songs from the query script with the list returned from the ``GET http://127.0.0.1:5000/playlists/<playlist_id>/songs`` endpoint and confirmed that the last song was always left out.
    6. With knowledge on how I handled the first issue, I also inspected the ``tests\test_playlists.py``, which has a test case failing because the expected result included the last song but not in the actual result.

#### Finding the Root Cause
- Which files did you look at? What was your navigation path?
    1. ``routes/playlists.py`` to look for the function connected to endpoint ``GET http://127.0.0.1:5000/playlists/<playlist_id>/songs``
    2. ``services/playlist_service.py`` since the endpoint calls ``playlist_service.get_playlist_songs()``.
    3. ``tests\test_playlists.py`` to check if the same ``playlist_service.get_playlist_songs()`` is called for the failed test case.
- What moment made you confident you'd found the right place, not just a suspicious area, but the specific cause?
    - I was confident I found the right place when both the endpoint and the failed test case called the same function in the same file. Anything that fails at that endpoint should be expected to have failed at the service layer since the endpoint just provides input and output, which were correct. After inspecting the function, I found the bug.

#### Root Cause
- In ``services/playlist_service.py``, specifically the function ``playlist_service.get_playlist_songs()``, the final list cuts off the last song. 
- ```python return [song.to_dict() for song in songs[:-1]]``` means it creates a list of JSONs that represent the songs, but only up to the last song and not including it. The ```python for song in songs[:-1]``` means it goes through all of songs up to the last song since ranges in Python are not inclusive at the upper bound or stopping target. The last song is sliced off.

#### Fix & Side-Effect Check
- What did you change?
    - I removed the ``[-1]`` in ``songs[-1]`` to make the line read as ```python return [song.to_dict() for song in songs]```.
- Why does that change fix the root cause?
    - The final result goes through all of the songs in the list rather than slicing off the last song as the stop target. Specifying a stop target means it will not be included, so removing the stop target allows for all of the songs to be added.
- What related functionality did you check afterward to confirm you didn't break anything?
    - I tested each playlist again with the ``GET http://127.0.0.1:5000/playlists/<playlist_id>/songs`` endpoint, checking both the count and the last song in the return list. They each returned the correct count of 7 and their respective last songs.

### Issue 2: Friends Listening Now shows people from yesterday

#### Reproduction
- What inputs, sequence of actions, or data condition triggered the behavior?
    - The seeded information of user ids, user friendship relationships and last listened state
    - ``GET http://127.0.0.1:5000/feed/<user_id>/listening-now``
- What steps did you take to confirm the bug exists before touching any code?
    1. Ran a command to get Flask app's "now" with ``datetime.now(timezone.utc)`` since results will be in UTC timezone (different from my actual timezone) and need a time to compare results to.
    2. Ran ``GET http://127.0.0.1:5000/feed/<user_id>/listening-now``, specifically with Kenji's and Nova's (users) ids.
    3. Found a friend's listening activity that was the previous day (Nova).

#### Finding the Root Cause
- Which files did you look at? What was your navigation path?
    1. ``routes/feed.py`` to find the endpoint that checks for listening now activity from friends (``GET http://127.0.0.1:5000/feed/<user_id>/listening-now``)
    2. ``services/feed_service.py`` which contains the function ``feed_service.get_friends_listening_now()`` called by the endpoint.

- What moment made you confident you'd found the right place, not just a suspicious area, but the specific cause?
    - After reaching the service layer and inspecting the implementation of ``feed_service.get_friends_listening_now()``, I saw that the cutoff is 24 hours before the current time. The threshold is way too long to be considered "listening now" and also it's possible that 24 hours from the current time crosses into the day before.

#### Root Cause
- In ``feed_service.get_friends_listening_now()``, the threshold cutoff or window size of 24 hours is way too long to be considered "listening now". It's also possible that 24 hours from the current time crosses into the day before.

#### Fix & Side-Effect Check
- What did you change? Why does that change fix the root cause?
    - Rather than a 24 hour window, I reduced the window to be 30 minutes for a more accurate display of "listening now" and recency.
    - Although I disagree that it shouldn't cross over into the previous day and should only check for a 30 minute-window, I added to filter for only listening activity on the same day.
- What related functionality did you check afterward to confirm you didn't break anything?
    - Tested the ``GET http://127.0.0.1:5000/feed/<user_id>/listening-now`` endpoint again to check whether the recent listening now activity still showed activity in the 24 hour window and previous day, which none appeared.

## Git Log, Fix Commits
<img width="911" height="587" alt="image" src="https://github.com/user-attachments/assets/450a400e-4042-42b0-9683-b65fcea0e9af" />
