# -*- coding: utf-8 -*-
__author__ = 'n2m'


class StageProgress(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.stage_app = self

    def update_progress(self, user, stage, mission, meta):
        pass
