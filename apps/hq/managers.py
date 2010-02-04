from __future__ import absolute_import

from reporters.models import Reporter
from hq.middleware.hq import get_current_domain
from django.db import models

def reporter():
    """Get the filtered list of reporters based on the
       domain set in the middleware.  This overrides the
       view in rapidsms land.  If we can't find any 
       domain, we're not gonna let you see any reporters."""
    domain = get_current_domain()
    if domain:
        return Reporter.objects.filter(profile__domain=domain)
    else:
        # although I would prefer that this return nothing
        # because the sms apps will never have domain knowledge
        # it has to return everything for now.
        # return Reporter.objects.none()
        return Reporter.objects.all()
