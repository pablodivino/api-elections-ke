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

from google.appengine.ext import db
## To be Updated as the more data is received from IEBC
class ElectralDistrict(db.Model):
    iebc_code = db.StringProperty()
    name = db.StringProperty()
    etype = db.StringProperty()
    point = db.GeoPtProperty()
    polygon = db.TextProperty()
    
class PollingStation(db.Model):
    iebc_code = db.StringProperty()
    name = db.StringProperty()
    gender = db.StringProperty()
    reg_voters = db.IntegerProperty()
    no_of_streams = db.IntegerProperty()
    facility_type = db.StringProperty()
    electricity = db.StringProperty()
    networks = db.StringProperty()
    accessibility = db.StringProperty()
    disability = db.StringProperty()
    point = db.GeoPtProperty()

class ElectivePost(db.Model):
    iebc_code = db.StringProperty()
    post_name = db.StringProperty()

class Party(db.Model):
    iebc_code = db.StringProperty()
    name = db.StringProperty()
    party_abr =  db.StringProperty()
    symbol = db.StringProperty()
    color = db.StringProperty()
    male = db.IntegerProperty()
    female = db.IntegerProperty()
    
class Contestant(db.Model):
    iebc_code = db.StringProperty()
    other_name = db.StringProperty()
    surname =  db.StringProperty()
    voter_id = db.StringProperty()
    race_type = db.StringProperty()
    race_id =  db.StringProperty()
    party = db.StringProperty()
    independent =  db.StringProperty()

class Contest(db.Model):
    iebc_code =  db.StringProperty()
    race_title =  db.StringProperty()
    race_type =  db.StringProperty()
    location_type =  db.StringProperty()
    location_id =  db.StringProperty()


class Demographics(db.Model):
    sublocation = db.StringProperty()
    name = db.StringProperty()
    age = db.IntegerProperty()
    households = db.IntegerProperty()
    male = db.IntegerProperty()
    female = db.IntegerProperty()

class Voter(db.Model):
    name = db.StringProperty()
    gender = db.StringProperty()
    passport = db.StringProperty()
    idNumber = db.StringProperty()
    milID =  db.StringProperty()
    voterID =  db.StringProperty()
    date =  db.StringProperty()
    contestant =   db.StringProperty()
    pollingStation =  db.StringProperty()

class PStationIncident(db.Model):
    name = db.StringProperty()
    
class PStationIncidentReport(db.Model):
    name = db.StringProperty()
    p_polling_station = db.StringProperty()
    polling_station_info = db.StringProperty()
    report = db.TextProperty()
 
class Results(db.Model):
    candidate = db.StringProperty()
    raceID = db.StringProperty()
    elective_post = db.StringProperty()
    ps_disputed =  db.IntegerProperty()
    ps_rejected =  db.IntegerProperty()
    ps_turnout = db.IntegerProperty()
    ps_station = db.StringProperty()
    result = db.IntegerProperty()
    status = db.StringProperty()
    election  = db.StringProperty()
    resultID = db.StringProperty()

class User(db.Model):
    app_name = db.StringProperty()
    app_id = db.StringProperty()
    app_secret = db.StringProperty()
    app_owner_name = db.StringProperty()
    app_owner_email = db.StringProperty()
    app_owner_mobile = db.StringProperty()
    access_token = db.StringProperty()
    status = db.StringProperty()

class Election(db.Model):
    election_id = db.StringProperty()
    election_title = db.StringProperty()
    election_status = db.StringProperty()

class ContestTotal(db.Model):
    contest_id = db.StringProperty()
    election = db.StringProperty()
    post = db.StringProperty()
    electoral_district_code = db.StringProperty()
    electoral_district = db.ReferenceProperty(ElectralDistrict, collection_name="results")

class RejectedTotals(ContestTotal):
    contest= db.ReferenceProperty(ContestTotal, collection_name="rejected_totals")
    totals = db.IntegerProperty()
    
class VoterTurnoutTotals(ContestTotal):
    contest= db.ReferenceProperty(ContestTotal, collection_name="turnout")
    totals = db.IntegerProperty()

class DisputedTotals(ContestTotal):
    contest = db.ReferenceProperty(ContestTotal, collection_name="disputed_totals")
    totals = db.IntegerProperty()

class CandidateTotals(ContestTotal):
    candidate = db.StringProperty()
    totals = db.IntegerProperty()
    contest = db.ReferenceProperty(ContestTotal, collection_name="candidate_totals")

class VoterInfo(db.Model):
    title = db.StringProperty()
    content = db.TextProperty()
    summary = db.TextProperty()
    link = db.StringProperty()
