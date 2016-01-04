# Udacity Fullstack Nanodegree Project 4
# Course: Developing Scalable Apps in Python

### Description:

The objective of this project is to build upon backend functionality in the course-provided Conference Central Application.

###APIs:
* Google Cloud Endpoints
* Google API Explorer,

### Setup Instructions:

Note: To deploy this API server locally the [Google App Engine SDK for Python](https://cloud.google.com/appengine/downloads) is required.

1. Clone the git repository (or download it from the submission)
2. Run `dev_appserver.py DIR` or launch the app from the GUI app launcher Google provides in their API download.  Ensure it's running by visiting your local server's address, which is likely to be [localhost:8080][1]].

Instructions speicific to each deployment: 

1. Update the value of `application` in `app.yaml` to the app ID you have registered in the App Engine admin console and would like to use to host your instance of this sample.

2. Update the values at the top of `settings.py` to the CLIENT_ID you registered in the Google Developer Console

3. Update the value of CLIENT_ID in `static/js/app.js` to the Web client ID in your Google Developer Console 

4. (Optional) Mark the configuration files as unchanged as follows:
   `$ git update-index --assume-unchanged app.yaml settings.py static/js/app.js`

5. Run the app with the devserver using `dev_appserver.py DIR`, and ensure it's running by visiting your local server's address (by default localhost:8080)

6. (Optional) Generate your client library(ies) [the endpoints tool][2].

7. Deploy your application.


### 1: Add Sessions to a Conference

For the Sessions implementation, the Conference serves as the ancestor of the session. For a Session to be created, a
Conference must exist. The Conference is used for default values in Sessions as well. Name and Conference key are
required, while other values may be defaulted. Creating a _copySessionToForm method allowed for easy access to all Session
fields used in downstream methods. Date and Start Time strings were converted to date and time data-types to allow for
calculation of session times.

I created a Session Type class to organize the types of sessions, similar to the T-shirt size setup. 

Endpoints added:
* createSession: open for organizer of conference 
* getConferenceSessions: return all sessions, knowing conference 
* getConferenceSessionsByType: Given a conference, return all sessions of a specified type
* getSessionsBySpeaker: Given a speaker, return all sessions given by this particular speaker for all conferences 


Endpoints and Classes were added to support multiple sessions per conference.
Sessions are memcached for performance because they can be queried often.


### 2: Add sessions ot User Wishlist

Wishlist Session form is created to build upon in add and remove methods.

Endpoints added: 
* addSessionToWishlist: adds the session to the user's list of sessions they will attend 
* getSessionsInWishlist: query for all the sessions in a conference that the user will attend 

### 3: Work on indexes and queries

Create 2 additional queries (see end of conference.py script)
* getThirtyMinSessions: find sessions that last between 0 and 30 minutes
* getGenericTypeSessions: return sessions of Generic Type

API Explorer enables the review of these queries

Query Problem: Let’s say that you don't like workshops and you don't like sessions after 7 pm. How would you handle a query for all non-workshop sessions before 7 pm?

The challenge is that an inequality filter can be applied to one attribute at a time. Since there are two attributes involved, 
workshops/non-workshops and start time before 7pm, two filters are required. 
One way to solve this is to create a type filter for all Sessions that are not Workshop type. 
Then implement a time filter. Finally, iterate over the sessions in that type that match the time filter. 

```py
type = [key.name for key in SessionType if key != SessionType.WORKSHOP]
time = datetime.strptime("19:00", "%H:%M").time()

for session in Session.query(ndb.AND(Session.typeOfSession.IN(types), 
                                     Session.startTime < time)):
    print '%s of type %s at %s' % (session.name, session.typeOfSession, 
                                session.startTime.strftime("%H:%M"))
```

### 4: Add support for a feature speaker and an endpoint to get that speaker

Each time a session is added to a conference, the sessions for the conference are checked for which speaker has the most sessions. The 
speaker with the most sessions is marked in the speaker key in memcache and can be obtained with the getFeaturedSpeaker endpoint. 

* getFeaturedSpeaker(): When a new session is added to a conference if there is more than one session
   by this speaker, return featured speaker / sessions from memcache.


[1]: https://localhost:8080/
[2]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool