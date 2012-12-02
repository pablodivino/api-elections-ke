#!/usr/bin/env python

# Copyright 2012 JapakGIS Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#Author: david.japakgis@gmail.com (David Kimari)

import webapp2
import os
import models

from google.appengine.api import users
from google.appengine.ext.webapp import template



class MainHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            userdict = {
                                "username": user.nickname(),
                                "email": user.email(),
                                "apps": userHasApp(user),
                                "url": users.create_logout_url(self.request.uri),
                                "admin": users.is_current_user_admin(),
                                "url_linktext": "Logout"
                            }
        else:
            userdict = {
                                "url": users.create_login_url(self.request.uri),
                                "url_linktext": 'Login'
                            }

        path = os.path.join(os.path.dirname(__file__), 'main.html')
        self.response.out.write(template.render(path, userdict))

app = webapp2.WSGIApplication([
        (r'/', MainHandler),
        (r'/token/', 'requestHandlers.tokenRequest'),
        (r'/addapp/', 'requestHandlers.addUser'),
        (r'/adddata/', 'requestHandlers.addData'),
        (r'/(.*)/(.*)/(.*)/', 'requestHandlers.dataRequest'),
        (r'/(.*)/(.*)/', 'requestHandlers.dataRequest'),
        (r'/(.*)/(.*)', 'requestHandlers.dataRequest'),
        (r'/(.*)/', 'requestHandlers.dataRequest'),
], debug=True)

def userHasApp(user):
    current_user = models.User.all()
    current_user.filter("app_owner_email = ", user.email())
    appsList = []
    if len(list(current_user)) > 0:
        for app in current_user:
            appsList.append(app)

        return appsList

    else:
        return False
    
