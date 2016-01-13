#!/usr/bin/env python

"""
conference.py -- Udacity conference server-side Python App Engine API;
    uses Google Cloud Endpoints

$Id: conference.py,v 1.25 2014/05/24 23:42:19 wesc Exp wesc $

created by wesc on 2014 apr 21

"""

__author__ = 'wesc+api@google.com (Wesley Chun)'


from datetime import datetime

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from models import ConflictException
from models import Profile
from models import ProfileMiniForm
from models import ProfileForm
from models import StringMessage
from models import BooleanMessage
from models import Conference
from models import ConferenceForm
from models import ConferenceForms
from models import Speaker
from models import SpeakerForm
from models import Session
from models import SessionForm
from models import SessionForms
from models import ConferenceQueryForm
from models import ConferenceQueryForms
from models import SessionQueryForm
from models import SessionQueryForms
from models import SessionGetRequest
from models import TeeShirtSize

from settings import WEB_CLIENT_ID

from utils import getUserId

from settings import WEB_CLIENT_ID

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID
MEMCACHE_ANNOUNCEMENTS_KEY = "RECENT_ANNOUNCEMENTS"
MEMCACHE_FEATURED_SPEAKER_KEY = "FEATURED_SPEAKER"
ANNOUNCEMENT_TPL = ('Last chance to attend! The following conferences '
                    'are nearly sold out: %s')

MEMCACHE_FEATURE_SESSIONS_KEY = "RECENT_SESSION_ANNOUNCEMENTS"
FEATURE_SESSIONS_TPL = ('Special Announcement! %s is special attraction on %s')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

DEFAULTS = {
    "city": "Default City",
    "maxAttendees": 0,
    "seatsAvailable": 0,
    "topics": [ "Default", "Topic" ],
}

DEFAULTS_SESSION = {
    "location": "Default Location",
    "highlights": "Default topic",
    "duration": "Default duration",
    "typeOfSession": "Default type",
}

OPERATORS = {
            'EQ':   '=',
            'GT':   '>',
            'GTEQ': '>=',
            'LT':   '<',
            'LTEQ': '<=',
            'NE':   '!='
            }

FIELDS =    {
            'CITY': 'city',
            'TOPIC': 'topics',
            'MONTH': 'month',
            'MAX_ATTENDEES': 'maxAttendees',
            }

CONF_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey=messages.StringField(1),
)

CONF_POST_REQUEST = endpoints.ResourceContainer(
    ConferenceForm,
    websafeConferenceKey=messages.StringField(1),
)

SESSION_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    sessionKey=messages.StringField(1),
)

SESSION_GET_TYPE_REQUEST = endpoints.ResourceContainer(
    typeOfSession=messages.StringField(1),
    websafeConferenceKey=messages.StringField(2),
)

SESSION_GET_TIME_REQUEST = endpoints.ResourceContainer(
    date=messages.StringField(1),
    startTime=messages.StringField(2),
    endTime=messages.StringField(3),
    websafeConferenceKey=messages.StringField(4),
)

SESSION_GET_CD_REQUEST = endpoints.ResourceContainer(
    city=messages.StringField(1),
    startDate=messages.StringField(2),
    endDate=messages.StringField(3),
)

SESSION_POST_REQUEST = endpoints.ResourceContainer(
    SessionForm,
    websafeConferenceKey=messages.StringField(1),
)

SESSION_QUERY_REQUEST = endpoints.ResourceContainer(
    SessionQueryForms,
    websafeConferenceKey=messages.StringField(1),
)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


@endpoints.api(name='conference', version='v1',
    allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
    scopes=[EMAIL_SCOPE])
class ConferenceApi(remote.Service):
    """Conference API v0.1"""

# - - - Conference objects - - - - - - - - - - - - - - - - -

    def _copyConferenceToForm(self, conf, displayName):
        """Copy relevant fields from Conference to ConferenceForm."""
        cf = ConferenceForm()
        for field in cf.all_fields():
            if hasattr(conf, field.name):
                # convert Date to date string; just copy others
                if field.name.endswith('Date'):
                    setattr(cf, field.name, str(getattr(conf, field.name)))
                else:
                    setattr(cf, field.name, getattr(conf, field.name))
            elif field.name == "websafeKey":
                setattr(cf, field.name, conf.key.urlsafe())
        if displayName:
            setattr(cf, 'organizerDisplayName', displayName)
        cf.check_initialized()
        return cf


    def _createConferenceObject(self, request):
        """Create or update Conference object, returning ConferenceForm/request."""
        # preload necessary data items
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        if not request.name:
            raise endpoints.BadRequestException("Conference 'name' field required")

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}
        del data['websafeKey']
        del data['organizerDisplayName']

        # add default values for those missing (both data model & outbound Message)
        for df in DEFAULTS:
            if data[df] in (None, []):
                data[df] = DEFAULTS[df]
                setattr(request, df, DEFAULTS[df])

        # convert dates from strings to Date objects; set month based on start_date
        if data['startDate']:
            data['startDate'] = datetime.strptime(data['startDate'][:10], "%Y-%m-%d").date()
            data['month'] = data['startDate'].month
        else:
            data['month'] = 0
        if data['endDate']:
            data['endDate'] = datetime.strptime(data['endDate'][:10], "%Y-%m-%d").date()

        # set seatsAvailable to be same as maxAttendees on creation
        if data["maxAttendees"] > 0:
            data["seatsAvailable"] = data["maxAttendees"]
        # generate Profile Key based on user ID and Conference
        # ID based on Profile key get Conference key from ID
        p_key = ndb.Key(Profile, user_id)
        c_id = Conference.allocate_ids(size=1, parent=p_key)[0]
        c_key = ndb.Key(Conference, c_id, parent=p_key)
        data['key'] = c_key
        data['organizerUserId'] = request.organizerUserId = user_id

        # create Conference, send email to organizer confirming
        # creation of Conference & return (modified) ConferenceForm
        Conference(**data).put()
        # TODO 2: add confirmation email sending task to queue

        return request


    @ndb.transactional()
    def _updateConferenceObject(self, request):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)

        # copy ConferenceForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}

        # update existing conference
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        # check that conference exists
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)

        # check that user is owner
        if user_id != conf.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the owner can update the conference.')

        # Not getting all the fields, so don't create a new object; just
        # copy relevant fields from ConferenceForm to Conference object
        for field in request.all_fields():
            data = getattr(request, field.name)
            # only copy fields where we get data
            if data not in (None, []):
                # special handling for dates (convert string to Date)
                if field.name in ('startDate', 'endDate'):
                    data = datetime.strptime(data, "%Y-%m-%d").date()
                    if field.name == 'startDate':
                        conf.month = data.month
                # write to Conference object
                setattr(conf, field.name, data)
        conf.put()
        prof = ndb.Key(Profile, user_id).get()
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))


    @endpoints.method(ConferenceForm, ConferenceForm, path='conference',
            http_method='POST', name='createConference')
    def createConference(self, request):
        """Create new conference."""
        return self._createConferenceObject(request)


    @endpoints.method(CONF_POST_REQUEST, ConferenceForm,
            path='conference/{websafeConferenceKey}',
            http_method='PUT', name='updateConference')
    def updateConference(self, request):
        """Update conference w/provided fields & return w/updated info."""
        return self._updateConferenceObject(request)


    @endpoints.method(CONF_GET_REQUEST, ConferenceForm,
            path='conference/{websafeConferenceKey}',
            http_method='GET', name='getConference')
    def getConference(self, request):
        """Return requested conference (by websafeConferenceKey)."""
        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)
        prof = conf.key.parent().get()
        # return ConferenceForm
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))


    @endpoints.method(message_types.VoidMessage, ConferenceForms,
            path='getConferencesCreated',
            http_method='POST', name='getConferencesCreated')
    def getConferencesCreated(self, request):
        """Return conferences created by user."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id =  getUserId(user)
        # create ancestor query for all key matches for this user
        confs = Conference.query(ancestor=ndb.Key(Profile, user_id))
        prof = ndb.Key(Profile, user_id).get()
        # return set of ConferenceForm objects per Conference
        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, getattr(prof, 'displayName')) for conf in confs]
        )


    def _getQuery(self, request):
        """Return formatted query from the submitted filters."""
        q = Conference.query()
        inequality_filter, filters = self._formatFilters(request.filters)

        # If exists, sort on inequality filter first
        if not inequality_filter:
            q = q.order(Conference.name)
        else:
            q = q.order(ndb.GenericProperty(inequality_filter))
            q = q.order(Conference.name)

        for filtr in filters:
            if filtr["field"] in ["month", "maxAttendees"]:
                filtr["value"] = int(filtr["value"])
            formatted_query = ndb.query.FilterNode(filtr["field"], filtr["operator"], filtr["value"])
            q = q.filter(formatted_query)
        return q


    def _formatFilters(self, filters):
        """Parse, check validity and format user supplied filters."""
        formatted_filters = []
        inequality_field = None

        for f in filters:
            filtr = {field.name: getattr(f, field.name) for field in f.all_fields()}

            try:
                filtr["field"] = FIELDS[filtr["field"]]
                filtr["operator"] = OPERATORS[filtr["operator"]]
            except KeyError:
                raise endpoints.BadRequestException("Filter contains invalid field or operator.")

            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                # check if inequality operation has been used in previous filters
                # disallow the filter if inequality was performed on a different field before
                # track the field on which the inequality operation is performed
                if inequality_field and inequality_field != filtr["field"]:
                    raise endpoints.BadRequestException("Inequality filter is allowed on only one field.")
                else:
                    inequality_field = filtr["field"]

            formatted_filters.append(filtr)
        return (inequality_field, formatted_filters)


    @endpoints.method(ConferenceQueryForms, ConferenceForms,
            path='queryConferences',
            http_method='POST',
            name='queryConferences')
    def queryConferences(self, request):
        """Query for conferences."""
        conferences = self._getQuery(request)

        # need to fetch organiser displayName from profiles
        # get all keys and use get_multi for speed
        organisers = [(ndb.Key(Profile, conf.organizerUserId)) for conf in conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return individual ConferenceForm object per Conference
        return ConferenceForms(
                items=[self._copyConferenceToForm(conf, names[conf.organizerUserId]) for conf in \
                conferences]
        )


# - - - Profile objects - - - - - - - - - - - - - - - - - - -

    def _copyProfileToForm(self, prof):
        """Copy relevant fields from Profile to ProfileForm."""
        # copy relevant fields from Profile to ProfileForm
        pf = ProfileForm()
        for field in pf.all_fields():
            if hasattr(prof, field.name):
                # convert t-shirt string to Enum; just copy others
                if field.name == 'teeShirtSize':
                    setattr(pf, field.name, getattr(TeeShirtSize, getattr(prof, field.name)))
                else:
                    setattr(pf, field.name, getattr(prof, field.name))
        pf.check_initialized()
        return pf


    def _getProfileFromUser(self):
        """Return user Profile from datastore, creating new one if non-existent."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # get Profile from datastore
        user_id = getUserId(user)
        p_key = ndb.Key(Profile, user_id)
        profile = p_key.get()
        # create new Profile if not there
        if not profile:
            profile = Profile(
                key = p_key,
                displayName = user.nickname(),
                mainEmail= user.email(),
                teeShirtSize = str(TeeShirtSize.NOT_SPECIFIED),
            )
            profile.put()

        return profile      # return Profile


    def _doProfile(self, save_request=None):
        """Get user Profile and return to user, possibly updating it first."""
        # get user Profile
        prof = self._getProfileFromUser()

        # if saveProfile(), process user-modifyable fields
        if save_request:
            for field in ('displayName', 'teeShirtSize'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(prof, field, str(val))
                        #if field == 'teeShirtSize':
                        #    setattr(prof, field, str(val).upper())
                        #else:
                        #    setattr(prof, field, val)
            prof.put()

        # return ProfileForm
        return self._copyProfileToForm(prof)


    @endpoints.method(message_types.VoidMessage, ProfileForm,
            path='profile', http_method='GET', name='getProfile')
    def getProfile(self, request):
        """Return user profile."""
        return self._doProfile()


    @endpoints.method(ProfileMiniForm, ProfileForm,
            path='profile', http_method='POST', name='saveProfile')
    def saveProfile(self, request):
        """Update & return user profile."""
        return self._doProfile(request)


# - - - Registration - - - - - - - - - - - - - - - - - - - -

    @ndb.transactional(xg=True)
    def _conferenceRegistration(self, request, reg=True):
        """Register or unregister user for selected conference."""
        retval = None
        prof = self._getProfileFromUser() # get user Profile

        # check if conf exists given websafeConfKey
        # get conference; check that it exists
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % wsck)

        # register
        if reg:
            # check if user already registered otherwise add
            if wsck in prof.conferenceKeysToAttend:
                raise ConflictException(
                    "You have already registered for this conference")

            # check if seats avail
            if conf.seatsAvailable <= 0:
                raise ConflictException(
                    "There are no seats available.")

            # register user, take away one seat
            prof.conferenceKeysToAttend.append(wsck)
            conf.seatsAvailable -= 1
            retval = True

        # unregister
        else:
            # check if user already registered
            if wsck in prof.conferenceKeysToAttend:

                # unregister user, add back one seat
                prof.conferenceKeysToAttend.remove(wsck)
                conf.seatsAvailable += 1
                retval = True
            else:
                retval = False

        # write things back to the datastore & return
        prof.put()
        conf.put()
        return BooleanMessage(data=retval)


    @endpoints.method(message_types.VoidMessage, ConferenceForms,
            path='conferences/attending',
            http_method='GET', name='getConferencesToAttend')
    def getConferencesToAttend(self, request):
        """Get list of conferences that user has registered for."""
        prof = self._getProfileFromUser() # get user Profile
        conf_keys = [ndb.Key(urlsafe=wsck) for wsck in prof.conferenceKeysToAttend]
        conferences = ndb.get_multi(conf_keys)

        # get organizers
        organisers = [ndb.Key(Profile, conf.organizerUserId) for conf in conferences]
        profiles = ndb.get_multi(organisers)

        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName

        # return set of ConferenceForm objects per Conference
        return ConferenceForms(items=[self._copyConferenceToForm(conf, names[conf.organizerUserId])\
         for conf in conferences]
        )


    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
            path='conference/{websafeConferenceKey}',
            http_method='POST', name='registerForConference')
    def registerForConference(self, request):
        """Register user for selected conference."""
        return self._conferenceRegistration(request)


    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
            path='conference/{websafeConferenceKey}',
            http_method='DELETE', name='unregisterFromConference')
    def unregisterFromConference(self, request):
        """Unregister user for selected conference."""
        return self._conferenceRegistration(request, reg=False)

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
            path='filterPlayground',
            http_method='GET', name='filterPlayground')
    def filterPlayground(self, request):
        """Filter Playground"""
        q = Conference.query()
        # field = "city"
        # operator = "="
        # value = "London"
        # f = ndb.query.FilterNode(field, operator, value)
        # q = q.filter(f)
        q = q.filter(Conference.city=="London")
        q = q.filter(Conference.topics=="Medical Innovations")
        q = q.filter(Conference.month==6)

        return ConferenceForms(
            items=[self._copyConferenceToForm(conf, "") for conf in q]
        )

# - - - Sessions - - - - - - - - - - - - - - - - - - - -

    def _copySessionToForm(self, session, conferenceName):
        """Copy relevant fields from Session to SessionForm."""
        sf = SessionForm()
        for field in sf.all_fields():
            if hasattr(session, field.name):
                # convert Date to date string; just copy others
                if field.name.endswith(('date', 'Time')):
                    setattr(sf, field.name, str(getattr(session, field.name)))
                elif field.name == "speaker":
                    if getattr(session, field.name):
                        speaker = getattr(session, field.name).get()
                        setattr(sf, field.name, speaker.name)
                else:
                    setattr(sf, field.name, getattr(session, field.name))
            elif field.name == "websafeKey":
                setattr(sf, field.name, session.key.urlsafe())

        if conferenceName:
            setattr(sf, 'conferenceName', conferenceName)
        sf.check_initialized()
        return sf

    def _createSessionObject(self, request):
        """Create or update Session object, returning SessionForm/request."""
        # preload necessary data items
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()

        # check that conference exists
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s'
                % request.websafeConferenceKey)

        # check that user is owner
        if user_id != conf.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the conference organizer can create a session.')

        # copy SessionForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name)
                for field in request.all_fields()}
        del data['conferenceName']
        del data['websafeConferenceKey']
        del data['websafeKey']

        # add default values for those missing
        for df in DEFAULTS_SESSION:
            if data[df] in (None, []):
                data[df] = DEFAULTS_SESSION[df]
                setattr(request, df, DEFAULTS_SESSION[df])

        # convert dates from strings to Date objects;
        if data['date']:
            data['date'] = datetime.strptime(
                data['date'][:10], "%Y-%m-%d").date()
        if data['startTime']:
            data['startTime'] = datetime.strptime(
                data['startTime'][:10], "%H:%M").time()

        # generate speaker key based on the speaker name
        speaker_key = ndb.Key(Speaker, data['speaker'])
        speaker = speaker_key.get()
        # create new Speaker if not there
        if not speaker:
            speaker = Speaker(name=data['speaker'], key=speaker_key)
            speaker.put()
        data['speaker'] = speaker_key

        # generate Profile Key based on user ID and Session
        # ID based on Profile key get Session key from ID
        c_key = conf.key
        s_id = Session.allocate_ids(size=1, parent=c_key)[0]
        s_key = ndb.Key(Session, s_id, parent=c_key)

        data['key'] = s_key
        data['organizerUserId'] = request.organizerUserId = user_id
        Session(**data).put()

        # check if speaker has other sessions; if so, add to memcache
        speaker_sessions = Session.query(
            Session.speaker == speaker_key, ancestor=c_key).fetch()
        if len(speaker_sessions) > 1:
            speakerName = speaker_key.get().name
            sessionNames = [
                str(session.name) for session in speaker_sessions]
            # add to taskqueue
            taskqueue.add(
                params={'speakerName': speakerName,
                        'sessionNames': [sessionNames]},
                url='/tasks/update_featured_speaker'
            )

        # return request
        ses = s_key.get()
        return self._copySessionToForm(ses, getattr(conf, 'name'))

    @endpoints.method(SESSION_POST_REQUEST, SessionForm,
                      path='session/{websafeConferenceKey}',
                      http_method='POST', name='createSession')
    def createSession(self, request):
        """Create new session."""
        return self._createSessionObject(request)

    @endpoints.method(SessionGetRequest, SessionForms,
                      path='getSessionsBySpeaker',
                      http_method='GET', name='getSessionsBySpeaker')
    def getSessionsBySpeaker(self, request):
        """Return Sessions given by a speaker."""
        speaker = Speaker.query(Speaker.name == request.speaker).get()
        if speaker is None:
            raise endpoints.NotFoundException(
                'No session found to be given by this speaker: %s'
                % request.speaker)

        sessions = Session.query(Session.speaker == speaker.key).fetch()

        # return set of ConferenceForm objects per Conference
        return SessionForms(
            items=[self._copySessionToForm(
                ses, getattr(ses.key.parent().get(), 'name'))
                    for ses in sessions])


    @endpoints.method(CONF_GET_REQUEST, SessionForms,
                      path='querySession/{websafeConferenceKey}',
                      http_method='GET',
                      name='getConferenceSessions')
    def getConferenceSessions(self, request):
        """Query for conference sessions."""
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()

        # need to fetch all session in the conference
        sessions = Session.query(ancestor=conf.key)

        # return individual SessionForm object per Session
        return SessionForms(
                items=[self._copySessionToForm(
                    ses, getattr(conf, 'name')) for ses in sessions])


    @endpoints.method(SESSION_GET_TYPE_REQUEST, SessionForms,
                      path='querySession/{websafeConferenceKey}',
                      http_method='POST',
                      name='getConferenceSessionsByType')
    def getConferenceSessionsByType(self, request):
        """Query for sessions by type."""
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()

        sessions = Session.query(
            Session.typeOfSession == request.typeOfSession).fetch()

        # return individual SessionForm object per session
        return SessionForms(
                items=[self._copySessionToForm(
                    ses, getattr(conf, 'name')) for ses in sessions])

    @endpoints.method(SESSION_QUERY_REQUEST, SessionForms,
                      path='queryConfSessions/{websafeConferenceKey}',
                      http_method='POST', name='queryConferenceSessions')
    def queryConferenceSessions(self, request):
        """Query for sessions in a conference based on the filters."""
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        # need to fetch all session in the conference
        sessions = self._getSessionQuery(request)

        # return individual SessionForm object per session
        return SessionForms(
                items=[self._copySessionToForm(
                    ses, getattr(conf, 'name')) for ses in sessions])

    def _getSessionQuery(self, request):
        """Return formatted session query from the submitted filters."""
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        q = Session.query(ancestor=conf.key)
        inequality_filter, filters = self._formatFilters(request.filters)

        # If exists, sort on inequality filter first
        if not inequality_filter:
            q = q.order(Session.name)
        else:
            q = q.order(ndb.GenericProperty(inequality_filter))
            q = q.order(Session.name)

        for filtr in filters:
            formatted_query = ndb.query.FilterNode(
                filtr["field"], filtr["operator"], filtr["value"])
            q = q.filter(formatted_query)
        return q

# - - - Session Wishlist - - - - - - - - - - - - - - - - - - - -

    @endpoints.method(message_types.VoidMessage, SessionForms,
            path='wishlist',
            http_method='GET', name='getSessionsInWishlist')
    def getSessionsInWishlist(self, request):
        """Get list of sessions that user has added to their wishlist."""
        prof = self._getProfileFromUser() # get user Profile
        sess_keys = [ndb.Key(urlsafe=wsck) for wsck in prof.sessionKeysInWishlist]
        sessions = ndb.get_multi(sess_keys)

         # return set of SessionForm objects per session
        return SessionForms(items=[self._copySessionToForm(session) for session in sessions])


    @endpoints.method(endpoints.ResourceContainer(
        SessionKey=messages.StringField(1)), BooleanMessage,
            path='session/{SessionKey}',
            http_method='POST', name='addSessionToWishlist')
    def addSessionToWishlist(self, request):
        """Add session to this user's wishlist."""
        return self._sessionWishlist(request)


    @endpoints.method(endpoints.ResourceContainer(
        SessionKey=messages.StringField(1)), BooleanMessage,
            path='session/{SessionKey}',
            http_method='DELETE', name='deleteSessionFromWishlist')
    def deleteSessionFromWishlist(self, request):
        """Add session to user wishlist."""
        return self._sessionWishlist(request, False)


    @ndb.transactional
    def _sessionWishlist(self, request, add=True):
        """Manage sessions in the current user's wishlist."""
        returnValue = None
        prof = self._getProfileFromUser() # get user Profile

        # Check if session exists with the given SessionKey
        wssk = request.SessionKey
        session = ndb.Key(urlsafe=wssk).get()
        if not session:
            raise endpoints.NotFoundException(
                'No session found with key: %s' % wssk)

        if not isinstance(session, Session):
            raise endpoints.BadRequestException(
                'Key must refer to a Session')

        if add:
            if wssk in prof.sessionKeysInWishlist:
                raise ConflictException(
                    "This session is already in your wishlist")
            prof.sessionKeysInWishlist.append(wssk)
            returnValue = True
        else:
            if wssk in prof.sessionKeysInWishlist:
                prof.sessionKeysInWishlist.remove(wssk)
                returnValue = True
            else:
                returnValue = False

        # Write changes back to the datastore and return
        prof.put()
        return BooleanMessage(data=returnValue)


    # Get announcment for feature session
    @staticmethod
    def _cacheFeatureSessions(speaker, wsck):
        """
            When a new session is added to a conference, the speaker is checked.
            If there is more than one session by this speaker at this conference,
            a new Memcache entry is also added that features the speaker and session names.
        """
        conf = ndb.Key(urlsafe=wsck).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with the key: %s' % wsck)

        sessions = Session.query(ancestor=conf.key).\
            filter(Session.speaker == speaker).\
            fetch()
        count = len(sessions)
        if count > 1:
            features = FEATURE_SESSIONS_TPL % (speaker,
                                                   ', '.join([s.name for s in sessions]))
            memcache.set(MEMCACHE_FEATURE_SESSIONS_KEY, features)


    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='session/announcement/get',
                      http_method='GET', name='getFeaturedSpeaker')
    def getFeaturedSpeaker(self, request):
        """Return the Announcement from memcache"""
        return StringMessage(data=memcache.get(MEMCACHE_FEATURE_SESSIONS_KEY) or "")


# - - - Featured Speaker - - - - - - - - - - - - - - -

    @endpoints.method(message_types.VoidMessage, SpeakerForm,
                      http_method='GET', name='getFeaturedSpeaker')
    def getFeaturedSpeaker(self, request):
        """Returns the sessions of the featured speaker"""
        # attempt to get data from memcache
        data = memcache.get(MEMCACHE_FEATURED_SPEAKER_KEY)
        # copy relevant fields to SpeakerForm
        sf = SpeakerForm()
        for field in sf.all_fields():
            if data and data[field.name]:
                setattr(sf, field.name, str(data[field.name]))
        sf.check_initialized()
        return sf

    @staticmethod
    def _cacheFeaturedSpeaker(speakerName, sessionNames):
        """Update new featured speaker to memcache; used by
        memcache cron job.
        """
        cache_data = {}
        cache_data['speaker'] = speakerName
        cache_data['sessionNames'] = sessionNames
        if not memcache.set(MEMCACHE_FEATURED_SPEAKER_KEY, cache_data):
            logging.error('Memcache set failed.')
        return cache_data



# - - - Additional Queries  - - - - - - - - - - - - - - - - - - - -

    @endpoints.method(message_types.VoidMessage,
                      SessionForms,
                      http_method='GET',
                      name='getIncompleteSessions')
    def getIncompleteSessions(self, request):
        """Return all sessions with default information for speaker, duration, or type"""

        sessions = Session.query(ndb.OR(Session.speaker == "Default",
                                        Session.duration == 0,
                                        Session.typeOfSession == "NOT_SPECIFIED"))

        return SessionForms(items=[self._copySessionToForm(session) for session in sessions])


    @endpoints.method(message_types.VoidMessage,
                      SessionForms,
                      path='shortSessions',
                      http_method='GET',
                      name='getThirtyMinSessions')
    def getThirtyMinSessions(self, request):
        """Return all sessions between 5 and 30 minutes long with duration specified in minutes"""

        sessions = Session.query(ndb.AND(Session.duration > 0, Session.duration < 30))

        return SessionForms(items=[self._copySessionToForm(session) for session in sessions])

# - - - Announcements - - - - - - - - - - - - - - - - - - - -


api = endpoints.api_server([ConferenceApi]) # register API
