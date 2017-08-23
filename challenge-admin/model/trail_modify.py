__author__ = 'n2m'

from rest import crudmgo
from mod_auth import current_user, current_session


class TrailDocument(crudmgo.RootDocument):
    _trail_modify = False

    def save(self, *args, **kargs):
        if self._trail_modify and self.get("_id"):
            if not isinstance(self.get(self._trail_modify), list):
                self[self._trail_modify] = []

            if current_user._get_current_object() and not current_user.is_anonymous:
                self[self._trail_modify].append({
                    "by": current_user.id,
                    "on": crudmgo.utctime(),
                    "username": current_user.get_username()
                })
            else:
                self[self._trail_modify].append({
                    "by": None,
                    "on": crudmgo.utctime(),
                    "username": current_session._get_current_object() and current_session.get("ipaddr")
                })

        return super(TrailDocument, self).save(*args, **kargs)