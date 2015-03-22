from django.shortcuts import render
from django.views.generic import TemplateView, View


class CameraTestView(TemplateView):
    template_name = 'video_camera_test.html'
    page_title = 'Camera Test'

    def get_context_data(self, **kwargs):
        context = super(CameraTestView, self).get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["title"] = self.page_title
        return context


class VideoCallView(View):

    def get(self, request, inviter, invited_bookid):
        invited = invited_bookid.rsplit('-book-', 1)[0]
        bookid = invited_bookid.split('-book-', 1)[-1]
        page_title = "Conversation {0} and {1}".format(inviter.title(), invited.title())

        # TODO log some info about calls
        # print "inviter", inviter
        # print "invited", invited
        # print "bookid", bookid

        return render(request, "video_call.html",
                      {"inviter": inviter,
                       "invited": invited,
                       "page_title": page_title,
                       "title": page_title})