App Engine application for the Udacity Nanodegree: Full Stack Developer (Project 4)

## Products
- [App Engine][1]

## Language
- [Python][2]

## APIs
- [Google Cloud Endpoints][3]
- [API Explorer][7]

## Setup Instructions
1. Update the value of `application` in `app.yaml` to the app ID you
   have registered in the App Engine admin console and would like to use to host
   your instance of this sample.
1. Update the values at the top of `settings.py` to
   reflect the respective client IDs you have registered in the
   [Developer Console][4].
1. Update the value of CLIENT_ID in `static/js/app.js` to the Web client ID
1. (Optional) Mark the configuration files as unchanged as follows:
   `$ git update-index --assume-unchanged app.yaml settings.py static/js/app.js`
1. Run the app with the devserver using `dev_appserver.py DIR`, and ensure it's running by visiting your local server's address (by default [localhost:8080][5].)
1. (Optional) Generate your client library(ies) with [the endpoints tool][6].
1. Deploy your application.

## Tasks

## Task 1: Add Sessions to a Conference

### Define the following Endpoints methods

- `getConferenceSessions(websafeConferenceKey)`
   Given a conference, return all sessions

- `getConferenceSessionsByType(websafeConferenceKey, typeOfSession)`
   Given a conference, return all sessions of a specified type (eg lecture, keynote, workshop)

- `getSessionsBySpeaker(speaker)`
   Given a speaker, return all sessions given by this particular speaker, across all conferences

- `createSession(SessionForm, websafeConferenceKey)`
   Open only to the organizer of the conference

### Define Session class and SessionForm

In the SessionForm pass in:
- name
- highlights
- speaker
- duration
- typeOfSession
- date
- start time (in 24 hour notation so it can be ordered)

### Explain your design choices

The Sessions implementation is based heavy on the existing Conference
implementation due to their similar functionality and related purpose.

For the sake of simplicity speaker is defined as a StringProperty to avoid the
need create a separate speaker entity.

## Task 2: Add Sessions to User Wishlist

### Define the following Endpoints methods

- `addSessionToWishlist(SessionKey)`
   adds the session to the user's list of sessions they are interested in attending

- `getSessionsInWishlist()`
   query for all the sessions in a conference that the user is interested in

## Task 3: Work on indexes and queries

### Part 1: Come up with 2 additional queries

Think about other types of queries that would be useful for this application.
Describe the purpose of 2 new queries and write the code that would perform them.

Note: The following two endpoints can be assessed from the [API Explorer][7]

#### query 1

Get session that are less than 1 hour long.
This maybe useful for people only interested in short sessions.

```py
@endpoints.method(message_types.VoidMessage, SessionForms,
                  http_method='GET', name='getShortSessions')
def getShortSessions(self, request):
    """Return all sessions that are under one hour"""

    sessions = Session.query(ndb.AND(Session.duration > 0, Session.duration < 60))
    # assuming duration is specified in minutes

    return SessionForms(items=[self._copySessionToForm(session) for session in sessions])
```

#### query 2

Get all sessions with default information for speaker, duration, or type.
This maybe useful for find sessions that need further info added.

```py
@endpoints.method(message_types.VoidMessage, SessionForms,
                  http_method='GET', name='getIncompleteSessions')
def getIncompleteSessions(self, request):
    """Return all sessions with default information for speaker, duration, or type"""

    sessions = Session.query(ndb.OR(Session.speaker == "Default",
                                    Session.duration == 0,
                                    Session.typeOfSession == "Default"))

    return SessionForms(items=[self._copySessionToForm(session) for session in sessions])
```

### Part 2: Solve the following query related problem

> Let’s say that you don't like workshops and you don't like sessions after 7 pm.
> How would you handle a query for all non-workshop sessions before 7 pm?

#### What is the problem for implementing this query?

An inequality filter can be applied to at most one property. The problem here
would require an inequality filter on two:

- typeOfSession not equal to workshop
- startTime less than 7 pm

#### What ways to solve it did you think of?

#### Option 1

1. First query with the inequality filter that would return the smallest amount of
   sessions. An educated guess would be that there are more sessions with
   typeOfSession that is workshop than there are sessions that start 7pm or later.

2. Create an empty session list then iterate through the 'non_workshop_sessions'
   and append all sessions that start before 7pm to the new list.


```py
time_filter = datetime.strptime("19:00", "%H:%M").time()

non_workshop_sessions = Session.query(Session.typeOfSession != 'WORKSHOP')

sessions = []
for session in non_workshop_sessions:
    if session.typeOfSession < time_filter:
        sessions.append(session)

return sessions
```

#### Option 2

Alternatively if you know all types of session you could also avoid the
inequality filter on typeOfSession using ndb in as below:

```py
type_filter = ['NOT_SPECIFIED', 'KEYNOTE', 'LECTURE']  # all types that are not workshop
time_filter = datetime.strptime("19:00", "%H:%M").time()

sessions = Session.query(ndb.AND(Session.typeOfSession.IN(type_filter),
                                 Session.startTime < time_filter))

return sessions
```

#### Additional Notes

For a truly accurate solution checking the session startTime alone would be insufficient
as we should consider the duration too. i.e a session could start at 6pm and run
for two hours taking the session over the 7pm limit.
Therefore the statement would be more accurately represented as shown in the below pseudo code:
`Session.startTime + Session.duration < time_filter`

## Task 4: Add a Task

### Define the following Endpoints method

- `getFeaturedSpeaker()`
   When a new session is added to a conference if there is more than one session
   by this speaker return featured speaker / sessions from memcache.


[1]: https://developers.google.com/appengine
[2]: http://python.org
[3]: https://developers.google.com/appengine/docs/python/endpoints/
[4]: https://console.developers.google.com/
[5]: https://localhost:8080/
[6]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool
[7]: https://apis-explorer.appspot.com/apis-explorer/?base=https://udacity--conference-central.appspot.com/_ah/api#p/
