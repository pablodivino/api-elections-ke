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
import Json
import hmac
import hashlib
import dataprovider
import os
import models
import urllib2
import putData
import cgi
import json

from google.appengine.api import users
from google.appengine.ext.webapp import template


class tokenRequest(webapp2.RequestHandler):#handles request for accessTokens
    def get(self):
        app_id = self.request.get('appid')
        params = self.request.arguments() # gets all the url parameters
        if app_id:
            if self.request.get('key'):#check whether the request key is available
                key = self.request.get('key')
                app_secret = dataprovider.getAppSecret({"appid":app_id})
                urlstr= ''
                urldict = {}                
                if app_secret:#check whether a matching app secret for the token was found
                    for param in params:
                        if param != "key":
                            urlstr += "%s=%s&" %(param, self.request.get(param))
                            urldict[param] = self.request.get(param)

                    testKey = hmac.new(app_secret, urlstr.rstrip('&'), hashlib.sha256).hexdigest()
                    # check to see the key(url parameters hmac'd using appsecret) passed by the user matches the testKey a value derived by hmacing the url parameters using the app secret strored in the datastore
                    if testKey == key: #the testKey and key match
                        token = dataprovider.getToken(app_id)
                        response = {"status":"SUCCESS", "token":str(token)}
                    else:#the keys do not match meaning that this is an invalid request
                        response = { #the response when no key is available
                                        "status":"VERIFICATION_FAILED",
                                        "message":"Keys did not match. Confirm that you have the correct appsecret."
                                      }
                        
                    self.response.headers['Content-Type'] = 'application/json'
                    self.response.out.write(Json.encode(response))
                else:#if there was no matching appsecret was found
                    response = { #the response when no key is available
                                    "status":"VERIFICATION_FAILED",
                                    "message":"The appid supplied did not match any authorized apps"
                                  }
                    
                    self.response.headers['Content-Type'] = 'application/json'
                    self.response.out.write(Json.encode(response))
                    
            else:#if no matching app secret for the token was found, respond with an error
                response = { #the response when no key is available
                                    "status":"NO_KEY",
                                    "message":"No key passed. Request can not be verified"
                                  }
                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(Json.encode(response))
        else:
            response = { #the response when no key is available
                                    "status":"NO_APPID",
                                    "message":"Missing appid. Please confirm that you have supplied the appid"
                                  }
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(Json.encode(response))


class dataRequest(webapp2.RequestHandler):#handles all request for data
    def get(self, cat=False, catid=0, cat2=False):
        if self.request.get('token'): #check whether the request token is available
            token = self.request.get('token')
            params = self.request.arguments() # gets all the url parameters
            app_secret = dataprovider.getAppSecret({"token":token})
            electoral_dist = ['county', 'constituency', 'ward']
            elective_post = ['electivepost', 'president', 'governor', 'senator', 'women_rep', 'mp', 'councillor']
            
            if self.request.get('key'):#check whether the request key is available
                key = self.request.get('key')
                urlstr= ''
                urldict = {}
                filters = {}
                if app_secret:#check whether a matching app secret for the token was found
                    for param in params:
                        if param != "key":
                            if param !="token":
                                filters["%s"%param] = self.request.get(param)
                            urlstr += "%s=%s&" %(param, self.request.get(param))
                            urldict[param] = self.request.get(param)
                    urlstr = urlstr.rstrip()
                    testKey = hmac.new(app_secret, urlstr.rstrip("&"), hashlib.sha256).hexdigest()
                    # check to see the key(url parameters hmac'd using appsecret) passed by the user matches the testKey a value derived by hmacing the url parameters using the app secret strored in the datastore
                    if testKey: #the testKey and key match
                        """This is the portion that fetches the data as per the users request. The results will all depend on what is returned by the classes handling the various data requests."""
                        output = ""
                        ##This conditional handles the requests made for electoral district data """
                        if cat in electoral_dist:
                            if catid == 0 or catid =="" or catid ==" " or catid =="  ":
                                response = dataprovider.ElectoralDistrict("%s" % cgi.escape(cat), "", filters).getList()
                            else:
                                response = dataprovider.ElectoralDistrict("%s" % cgi.escape(cat), "%s" % cgi.escape(catid), filters).getDetailList()
                        ##This conditional handles the requests made for elective post data """
                        elif cat == "post":
                            if catid == 0 or catid =="" or catid ==" " or catid =="  ":
                                response = dataprovider.ElectivePost().getList()
                            else:
                                response = dataprovider.ElectivePost("%s" % cgi.escape(catid)).getDetailList()

                        
                        ##This conditional handles the requests made for elective post data """
                        elif cat == "pollingstation":
                            if catid == 0 or catid =="" or catid ==" " or catid =="  ":
                                response = dataprovider.PollingStation("",filters).getList()
                            else:
                                response = dataprovider.PollingStation("%s" % cgi.escape(catid), filters).getDetailList()
                                
                               
                        ##This conditional handles the requests made for candidate data """
                        elif cat == "candidate":
                            if catid == 0 or catid =="" or catid ==" " or catid =="  ":
                                response = dataprovider.Candidates("", filters).getList()
                            else:
                                response = dataprovider.Candidates("%s" % cgi.escape(catid), filters).getDetailList()
                        
                        ##This conditional handles the requests made for party data """
                        elif cat == "party":
                            if catid == 0 or catid =="" or catid ==" " or catid =="  ":
                                response = dataprovider.Party().getList()
                            else:
                                response = dataprovider.Party("%s" % cgi.escape(catid)).getDetailList()

                        ##This conditional handles the requests made for contest data"""
                        elif cat == "contest":
                            if catid == 0 or catid =="" or catid ==" " or catid =="  ":
                                response = dataprovider.Contests("", filters).getList()
                            else:
                                response = dataprovider.Contests("%s" % cgi.escape(catid), filters).getList()
                                
                        ##This conditional handles the requests made for party data """
                        elif cat == "voter":
                            response = dataprovider.Voter("%s" % cgi.escape(catid), self.request.get('type')).getList()
                                
                        ##This conditional handles the requests made for party data """
                        elif cat == "results":
                            if cat2 is not False:
                                response = dataprovider.Results("%s" % cgi.escape(catid), "%s" % cgi.escape(cat2), filters).getList()
                            else:
                                response = dataprovider.Results("%s" % cgi.escape(catid), "", filters).getList()
                        
                        else:
                            response['status'] = "Unknown Request Type"
                            response['messsage'] = "Unknown category specified."
                            
                        self.response.headers['Content-Type'] = 'application/json'
                        self.response.out.write(Json.encode(response))
                        """This marks the end of the portion that handles user responses"""
                    else:#the keys do not match meaning that this is an invalid request
                        response = { #the response when no key is available
                                        "status":"VERIFICATION_FAILED",
                                        "message":"Keys did not match. Confirm that you have the correct appsecret. %s" % urlstr
                                      }
                        self.response.headers['Content-Type'] = 'application/json'
                        self.response.out.write(Json.encode(response))
                    
                else:#if no matching app secret for the token was found, respond with an error
                    response = { #the response when no appsecret is returned
                                        "status":"VERIFICATION_FAILED",
                                        "message":"The token supplied did not match any authorized apps."
                                      }
                    self.response.headers['Content-Type'] = 'application/json'
                    self.response.out.write(Json.encode(response))
            else:
                response = { #the response when no key is available
                    "status":"NO_KEY",
                    "message":"No key passed. Request can not be verified"
                }
            
                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(Json.encode(response))
                
                
        else:
            response = { #the response when no token is available
                    "status":"NO_TOKEN",
                    "message":"No token passed."
                }
            
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(Json.encode(response))


class addUser(webapp2.RequestHandler):#This is a handler for all add user requests
    def get(self):
        user = users.get_current_user()
        if user:
            userdict = {
                                "username": user.nickname(),
                                "email": user.email(),
                                "url": users.create_logout_url(self.request.uri),
                                "url_linktext": "Logout",
                                "admin": users.is_current_user_admin()
                            }
        else:
            userdict = {
                                "url": users.create_login_url(self.request.uri),
                                "url_linktext": 'Login'
                            }

        path = os.path.join(os.path.dirname(__file__), 'adduser.html')
        self.response.out.write(template.render(path, userdict))

    def post(self):
        user = users.get_current_user()
        if user:
            app = models.User()
            app.app_name = self.request.get('app_title')
            app.app_owner_name = self.request.get('creator_name')
            app.app_owner_email = self.request.get('creator_email')
            app.app_owner_mobile = self.request.get('creator_mobile')
            if users.is_current_user_admin():
                appSEC = self.request.get('creator_mobile')+self.request.get('creator_email')+self.request.get('creator_name')
                app.app_secret = hmac.new("New App", appSEC, hashlib.md5).hexdigest()
            else:
                app.app_secret = ""
            app.status = "unapproved"
            app.put()
            app.app_id = "KEA%s" % app.key().id()
            app.put()
            userdict = {
                            "username": user.nickname(),
                            "email": user.email(),
                            "url": users.create_logout_url(self.request.uri),
                            "url_linktext": "Logout",
                            "admin": users.is_current_user_admin(),
                            "appid": app.app_id,
                            "appsecret": app.app_secret,
                            "appname": app.app_name
                        }
                
        else:
            userdict = {
                                "url": users.create_login_url(self.request.uri),
                                "url_linktext": 'Login'
                            }            
        if users.is_current_user_admin():
            path = os.path.join(os.path.dirname(__file__), 'adduser.html')
        else:
            path = os.path.join(os.path.dirname(__file__), 'main.html')
        self.response.out.write(template.render(path, userdict))


class addData(webapp2.RequestHandler):##This handles data inputs
    def get(self):
        user = users.get_current_user()
        if user and users.is_current_user_admin():
            userdict = {
                                "username": user.nickname(),
                                "email": user.email(),
                                "url": users.create_logout_url(self.request.uri),
                                "url_linktext": "Logout",
                                "admin": users.is_current_user_admin()
                            }
        else:
            userdict = {
                                "url": users.create_login_url(self.request.uri),
                                "url_linktext": 'Login'
                            }

        path = os.path.join(os.path.dirname(__file__), 'adddata.html')
        self.response.out.write(template.render(path, userdict))

    def post(self):
        user = users.get_current_user()
        putLog = []
        if user and users.is_current_user_admin():
            jsonFile = urllib2.urlopen(self.request.get('data_link'))
            jsonData = json.load(jsonFile)
            if self.request.get('data_type') in ["results", "election"]:
                if self.request.get('confirmed') not in ['Yes', 'yes']:
                    write_ok = putData.put(self.request.get('data_type'), jsonData, {"status":"provisional", "election_title":self.request.get('election_title'), "election_selected":self.request.get('election_selected')})
                else:
                    write_ok = putData.put(self.request.get('data_type'), jsonData, {"status":"confirmed", "election_title":self.request.get('election_title'), "election_selected":self.request.get('election_selected')})
                    
            else:
                write_ok = putData.put(self.request.get('data_type'), jsonData)
                
            putLog.append(write_ok["exist"])
            userdict = {
                                "username": user.nickname(),
                                "email": user.email(),
                                "url": users.create_logout_url(self.request.uri),
                                "url_linktext": "Logout",
                                "admin": users.is_current_user_admin(),
                                "Message":"The %s data entry was successful." % self.request.get('data_type')
                            }
            if len(putLog) > 0:
                userdict['error'] = putLog
        else:
            userdict = {
                                "url": users.create_login_url(self.request.uri),
                                "url_linktext": 'Login'
                            }
        path = os.path.join(os.path.dirname(__file__), 'adddata.html')
        self.response.out.write(template.render(path, userdict))
