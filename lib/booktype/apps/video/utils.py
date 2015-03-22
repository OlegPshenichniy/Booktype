import sputnik

from django.contrib.auth.models import User


def filter_video_users(bookid, usernames):
    """
    Filter users from provided usernames.
    Leave only users who available for video call in provided book.

    @type usernames: C{list}
    @param usernames: Usernames needed to filter
    @type bookid: C{string}
    @param bookid: Unique Book id
    @rtype: C{list}
    @return: Return users which available for video call
    """
    usernames_qs = User.objects.filter(videosettings__book=bookid,
                                       videosettings__enabled=True,
                                       username__in=usernames)

    usernames = usernames_qs.values('username', 'first_name', 'last_name', 'email')
    return usernames


def get_online_video_users(bookid):
    """
    Get online users which available for video call in provided book.

    @type bookid: C{string}
    @param bookid: Unique Book id
    @rtype: C{list}
    @return: Return online users which available for video call in provided book
    """
    try:
        # need more time to research this feature
        online_users = sputnik.smembers("sputnik:channel:%s:users" % '/booktype/book/1/1.0/')
    except:
        online_users = []

    # filter
    video_users = filter_video_users(bookid, usernames=online_users)

    return list(video_users)


