from django.conf.urls import patterns, url

from .views import VideoCallView, CameraTestView

urlpatterns = patterns(
    '',
    url(r'^camera-test/$', CameraTestView.as_view(), name='video_camera_test'),
    url(r'^(?P<inviter>[\w\s\_\.\-\d]+)/(?P<invited_bookid>[\w\s\_\.\-\d]+)/$',
        VideoCallView.as_view(), name='video_call')
)
