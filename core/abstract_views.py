from abc import ABCMeta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic.base import View


@method_decorator(login_required, name='dispatch')
class ProtectedView(View, metaclass=ABCMeta):
    """Parent for all views that require a login."""

    ...


@method_decorator(user_passes_test(lambda u: u.is_superuser),
                  name='dispatch')
class SuperuserView(View, metaclass=ABCMeta):
    """Parent for all views that require a login."""

    ...
