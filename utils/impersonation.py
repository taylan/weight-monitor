class ImpersonationContext():
    def __init__(self, user_id=0, email=''):
        self._user_id = user_id
        self._email = email

    @property
    def user_id(self):
        return self._user_id

    @property
    def email(self):
        return self._email

    @property
    def is_impersonating(self):
        return self.email
