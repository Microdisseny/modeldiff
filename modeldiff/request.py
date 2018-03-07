# From http://www.softwarematrix.cn/blog/django/using-customer-model-manager

#
# In Django's default Admin Site,
# here is the way
# just list the user's own objects in changelist pages
#

#
# add a global request middelware
# so that you can access the current request object from anywhere
#

from threading import currentThread
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser


def GlobalRequest():
    t = currentThread()
    if hasattr(t, 'request'):
        return t.request
    #
    # you can just return None
    # because we thirsty for the "user" :-)
    # so we create an AnonymousUser if request doesn't exists...
    #
    r = HttpRequest()
    r.user = AnonymousUser()
    return r


#
# I think you should already know how to install a customer middleware...
# If not, read the official documents
#
class GlobalRequestMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        t = currentThread()
        t.request = request

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.
        t.request = None

        return response

# use it as:
# user = GlobalRequest().user
