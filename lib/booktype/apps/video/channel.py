import sputnik

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from booki.utils import security
from booki.editor import models
from booktype.apps.edit.channel import get_video_users

from .models import VideoSettings


def get_online_video_users(bookid):
    try:
        # need more time to research this feature
        online_users = sputnik.smembers("sputnik:channel:%s:users" % '/booktype/book/1/1.0/')
    except:
        online_users = []

    # video users
    video_users = get_video_users(bookid, online_usernames=online_users)

    return list(video_users)


def remote_video_settings(request, message, bookid):
    """
    Change video settings for user in current book.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @rtype: C{dict}
    @return: Returns success of this command
    """
    # get book and check permissions
    try:
        book = models.Book.objects.get(id=int(bookid))
    except models.Book.DoesNotExist:
        raise ObjectDoesNotExist
    except models.Book.MultipleObjectsReturned:
        raise ObjectDoesNotExist

    book_security = security.getUserSecurityForBook(request.user, book)
    hasPermission = security.canEditBook(book, book_security)

    if not hasPermission:
        raise PermissionDenied

    # create or update settings
    video_settings, _ = VideoSettings.objects.get_or_create(user=request.user, book=book)
    video_settings.enabled = message['enabled']
    video_settings.save()

    sputnik.addMessageToChannel(request, "/video/%s/" % bookid,
                                {"command": "video_settings_changed"},
                                myself=False)

    # get online users which available for call
    video_users = get_online_video_users(bookid)
    sputnik.addMessageToChannel(request, "/video/%s/" % bookid,
                                {"command": "video_retrieve_users",
                                 "videoUsers": video_users},
                                myself=False)

    return {'result': True}


def remote_video_invite(request, message, bookid):
    """
    Send video call invite for user.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type message: C{dict}
    @param message: Message object
    @type bookid: C{string}
    @param bookid: Unique Book id
    @rtype: C{dict}
    @return: Returns success of this command
    """
    # get book and check permissions
    try:
        book = models.Book.objects.get(id=int(bookid))
    except models.Book.DoesNotExist:
        raise ObjectDoesNotExist
    except models.Book.MultipleObjectsReturned:
        raise ObjectDoesNotExist

    book_security = security.getUserSecurityForBook(request.user, book)
    hasPermission = security.canEditBook(book, book_security)

    if not hasPermission:
        raise PermissionDenied

    inviter, invited = message['video_node_link'].split('/video/')[1].split('/')[:2]
    invited = invited.split('-book-')[0]

    sputnik.addMessageToChannel(request, "/video/%s/" % bookid,
                                {"command": "video_invite",
                                 "inviter": inviter,
                                 "invited": invited,
                                 "node_link": message['video_node_link']},
                                myself=False)

    return {'result': True}
