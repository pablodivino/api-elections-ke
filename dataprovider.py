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
import models
import hmac
import hashlib
import cgi
import Json


from google.appengine.ext import db
def getAppSecret(appid):# The function returns the AppSecret that matches the AppID supplied.
    app = models.User.all()
    appsec = ''
    if appid.has_key('token'):
        app.filter('access_token = ',appid['token'])
    else:
        app.filter('app_id = ',appid['appid'])
        
    for k in app.fetch(1):
        appsec= k.app_secret

    return str(appsec)


def getContentType(contesttype):
    contests = {
            "Presidential":"1",
            "Governor":"2",
            "Senator":"3",
            "WomenRep":"4",
            "MP":"5",
            "CAW":"6",
        }

    return contests[contesttype]

def getToken(appid): # This function returns the Access Token for the supplied AppID. 
    app = models.User.all()
    app.filter('app_id = ',appid)
    for k in app.fetch(1):
        appsec= k

    if k.access_token:
        return k.access_token
    else:
        t = "%sTOKEN%s" %(k.app_owner_email, k.app_id)
        token = hmac.new("Create Token", t, hashlib.sha256).hexdigest();
        k.access_token = token
        k.put()
        return k.access_token
        
class Parent:
    def __init__(self, myKey, typ):
        self.key = myKey
        self.type = typ
    
    def getParent(self):
        parent_obj = {}
        if self.type == "pollingstation":
            pollingSt = db.get(self.key)
            ward = db.get(pollingSt.parent().key())
            constituency = db.get(ward.parent().key())
            county = db.get(constituency.parent().key())
            country = db.get(county.parent().key())
            parent_obj['ward'] = ward
            parent_obj['constituency'] =constituency
            parent_obj['county'] = county
            parent_obj['country'] = country
            
        if self.type == "ward":
            ward  = db.get(self.key)
            constituency = db.get(ward.parent().key())
            county = db.get(constituency.parent().key())
            country = db.get(county.parent().key())
            parent_obj['constituency'] =constituency
            parent_obj['county'] = county
            parent_obj['country'] = country

        if self.type == "constituency":
            constituency = db.get(self.key)
            county = db.get(constituency.parent().key())
            country = db.get(county.parent().key())
            parent_obj['county'] = county
            parent_obj['country'] = country

        if self.type == "country":
            county = db.get(self.key)
            country = db.get(county.parent().key())
            parent_obj['country'] = country

        return parent_obj


""" This is the class that returns a list of polling stations or information on a given polling station """    
class PollingStation:
    def __init__(self, ps_id, params={}):
        self.ftype = ""
        self.ftype_id = 0
        self.params = params
        self.filterParams = ["county","constituency","ward", "contest"]
        for param in params:
            if param in self.filterParams:
                self.ftype = param#this is the filter type for the url
                self.ftype_id = params[param]#this is the id of the filter given in ftype 
        self.ps_id = ps_id
        self.false = ('', ' ', False, '0')

    def getList(self): #this class returns a list of polling stations for a given category_id
        result = {}
        if self.ftype not in self.false or self.ftype_id not in self.false:
            ancestor = models.ElectralDistrict.all()
            if self.ftype == "contest":
                contest = models.Contest.all().filter("iebc_code = ",self.ftype_id)
                ancestor.filter("iebc_code = ", contest[0].location_id)
            else:
                ancestor.filter("iebc_code = ", self.ftype_id)
            ancestorkey = ""
            for an in ancestor.fetch(1):
                ancestorkey = an.key();
                
            thisPS = models.PollingStation.all()
            thisPS.ancestor(ancestorkey)
            result['status'] = "SUCCESS"
            result['polling_stations'] = list(thisPS)
        else:
            thisPS = models.PollingStation.all()
            psInfo = []
            for ps in thisPS.fetch(100):
                psInfo.append({
                        "name":ps.name,
                        "code":ps.iebc_code
                    })
            result['status'] = "SUCCESS"
            result['polling_stations'] = psInfo
            
        return result
    def getDetailList(self):
        result = {}
        psinfo =  thisPS = models.PollingStation.all()
        psinfo.filter("iebc_code = ", self.ps_id)
        result['status'] = "SUCCESS"
        result['info'] = list(psinfo)
        
        return result
        
        
class ElectoralDistrict: #this class handles request to the electoral district class
    def __init__(self, cat=False, cat_id=False, params={}):
        self.cat = cat
        self.cat_id = cat_id
        self.ftype = ""
        self.ftype_id = 0
        self.params = params
        self.filterParams = ["county","constituency","ward"]
        for param in params:
            if param in self.filterParams:
                self.ftype = param#this is the filter type for the url
                self.ftype_id = params[param]#this is the id of the filter given in ftype 
        self.false = ('', ' ', False, '0')

    def getList(self):#this is the function of the electoral district class that returns a list of electoral districts that match the category of electoral districts supplied
        result = {}
        limit = 1000
        output={}
        if self.cat not in self.false:
            if self.ftype in self.false:
                edQuery = db.GqlQuery("SELECT * FROM ElectralDistrict "+
                                                   "WHERE etype = :1 "+
                                                   "ORDER BY name ASC", cgi.escape(self.cat))
            else:
                pKey = 0
                pr = models.ElectralDistrict.all().filter("iebc_code = ", self.ftype_id)
                for pK in pr:
                    pKey = pK.key()
                if pKey != 0:
                    edQuery = db.GqlQuery("SELECT * FROM ElectralDistrict "+
                                                   "WHERE etype = :1 AND ANCESTOR IS :2 "+
                                                   "ORDER BY name ASC", cgi.escape(self.cat), pr[0].key())
                else:
                    edQuery = db.GqlQuery("SELECT * FROM ElectralDistrict "+
                                                   "WHERE etype = :1 "+
                                                   "ORDER BY name ASC", cgi.escape(self.cat))
                
            edArray = []
            for ed in edQuery:
                edArray.append({
                        "name": ed.name,
                        "code":ed.iebc_code,
                        "center":ed.point
                })
                
            result['location_type'] = "%s"%self.cat
            result["locations"] = edArray
            result["polygon"] = "http://the-api.host/%s.geojson"% self.cat
            #result['candidates'] = Candidates(self.cat).getList()
            #result['contests'] = Contests(self.cat).getList()
            output['status'] = 'SUCCESS'
            output['region'] = result

        else:
            output['status'] = 'ERROR'
            output['CATEGORY_ERROR']= 'Category missing from request. Specify i.e. county'

        return output
    
    def getDetailList(self):#this the function of the electoral district class that returns a detailed list on the electoral district specified by the category id.
        output = {}
        result = {}
        if self.cat not in self.false:## Test to see if the category is set.
            if self.cat_id not in self.false: ## Test to see if the category_id has been set.
                edQuery = db.GqlQuery("SELECT * FROM ElectralDistrict "+
                                           "WHERE etype = :1 AND iebc_code = :2 "+
                                           "ORDER BY name ASC ", cgi.escape(self.cat), cgi.escape(self.cat_id))
                

                edArray = []
                for ed in edQuery:
                    edArray.append({
                            "name": ed.name,
                            "code":ed.iebc_code,
                            "center":ed.point,
                            "polygon": "http://the-api.host/%s_%s.gejson"%(ed.etype, ed.name)
                    })
                result = {"info": edArray,"subregions": self.getChildrenList(self.cat, self.cat_id)}
                output['status'] = "SUCCESS"
                output['region'] = result
            else:## This is the query to use if the category_id has not been set.
                self.getList()
        else:
            output['CATEGORY_ERROR']= 'Category missing from request. Specify i.e. county'
            
        return output

    def getChildrenList(self, pType, pID=""):#this function returns the children of the specified electoral district.
        if pID in self.false:
            pID=self.cat_id
        ancestor = models.ElectralDistrict.all()
        ancestor.filter("iebc_code = ", pID)
        ancestorkey = ""
        for an in ancestor.fetch(1):
          ancestorkey = an.key();

        children = models.ElectralDistrict.all()
        children.filter("etype !=",pType)
        children.ancestor(ancestorkey)
        edArray = []
        for ed in children:
            edArray.append({
                    "name": ed.name,
                    "code":ed.iebc_code,
                    "center":ed.point,
                    "polygon": "http://the-api.host/%s_%s.gejson"%(ed.etype, ed.name)
            })
        return edArray


class Candidates:#This is the class that returns information about the candidates

    def __init__(self, candidate=False, params={}):
        self.candidate = candidate #this is the candidate iebc_code
        filterParams = ["county", "constituency","ward", "party", "post", "contest", "candidate"]
        self.type = ""
        self.type_id = 0
        for param in params:
            if param in filterParams:
                self.type = param#this is the filter type for the url
                self.type_id = params[param]#this is the id of the filter given in ftype
            if param =="election":
                self.election = params[param]
        self.false = ('', ' ', False, '0')

    def getList(self):#this is the function of the Candidate class that returns a list of candidates that match the category of candidates supplied
        output={}
        result = []
        contests = models.Contest.all()
        if self.type == "contest":
            contests.filter("iebc_code = ", self.type_id)
        elif self.type == "post":
            contests.filter("race_type = ", self.type_id)
        elif self.type in ["constituency", "ward","county"]:
            contests.filter("location_id = ", self.type_id)

        for contest in contests:
            candidates = models.Contestant.all()
            if self.type == "party":
                candidates.filter("party = ", self.type_id)
            candidates.filter("race_id = ", contest.iebc_code)
            result.append({"race": contest.race_title, "candidates":list(candidates)})

        output['status'] = "SUCCESS"
        output['candidates'] = result
        return output
    
    def getDetailList(self):#this the function of the candidate class that returns information about the candidate defined by the candidate ID.
        output = {}
        if self.candidate not in self.false:
            edQuery = db.GqlQuery("SELECT * FROM Contestant "+
                                                           "WHERE iebc_code  = :1 "+
                                                           "ORDER BY iebc_code ASC", cgi.escape(self.candidate))
            output['status'] = "SUCCESS"
            output['info'] = list(edQuery)
        return output

class ElectivePost: #This is used to access information concerning elective posts
    def __init__(self, cat_id=False):
        self.cat_id = cat_id
        
        self.false = ('', ' ', False, '0')

    def getList(self):#this is the function of the Elective Post class that returns a list of Elective Post
        output={}
        if self.cat_id in self.false:
            edQuery = db.GqlQuery("SELECT * FROM ElectivePost "+
                                                             "ORDER BY iebc_code ASC")
            output = {
                "status": "SUCCESS",
                "elective_posts":  list(edQuery.run(limit=50))
                }
        else:
            self.getDetailList()
            
        return output              

    def getDetailList(self):#this is the function of the Elective Post class that returns a list of Candidates under the elective Post Supplied
        output={}
        if self.cat_id not in self.false:
            edQuery = db.GqlQuery("SELECT * FROM Contestant "+
                                                       "WHERE elective_post = :1 "+
                                                       "ORDER BY name ASC", cgi.escape(self.cat_id))
            output = {
                "status": "SUCCESS",
                "candidates":  Contests(list(edQuery.run(limit=1000))).getList()
            }

        else:
            self.getList()
            
        return output
    

class Party: #This is used to access information concerning Parties
    def __init__(self, cat_id=False):
        self.cat_id = cat_id
        self.false = ('', ' ', False, '0')

    def getList(self):#this is the function of the Party class that returns a list of Parties
        output={}
        edQuery = db.GqlQuery("SELECT * FROM Party")
        output['status'] = 'SUCCESS'
        parties = []
        for party in edQuery:
            parties.append({
                    "name":party.name,
                    "code":party.iebc_code
            })
        output['parties'] = parties

        return output
                

    def getDetailList(self):#this is the function of the Party class that returns information on a specified party
        output={}
        if self.cat_id not in self.false:
            edQuery = db.GqlQuery("SELECT * FROM Party "+
                                                       "WHERE iebc_code = :1 "+
                                                       "ORDER BY name ASC", cgi.escape(self.cat_id))
            output['status'] = 'SUCCESS'
            output['info'] = list(edQuery.run())
        return output


class Contests: #This is used to access information concerning the Contests available
    def __init__(self, contest_id = 0, params={}):
        filterParams = ["county", "constituency","ward", "post"]
        self.type =""
        self.type_id = 0
        for param in params:
            if param in filterParams:
                self.type = param#this is the filter type for the url
                self.type_id = params[param]#this is the id of the filter given in ftype
            if param =="election":
                self.election = params[param]
        if contest_id != 0:
            self.contest = contest_id
        else:
            self.contest = False

    """ This function categorizes the results supplied by contest."""

    def getList(self):
        output = {}
        contests = models.Contest.all()
        a = ''
        clist = []
        if self.contest is not False:
            contests.filter("iebc_code = ", self.contest)
            output['contests'] = list(contests)
        elif self.type in ["constituency", "ward", "county"]:
            contests.filter("location_id = ", self.type_id)
            for c in contests:
                clist.append({
                        "contest": c.race_title,
                        "code": c.iebc_code,
                        "contestType": c.race_type
                    })
                output['contests'] = clist
        elif self.type =="post":
            contests.filter("race_type = ", self.type_id)
            for c in contests:
                clist.append({
                        "contest": c.race_title,
                        "code": c.iebc_code,
                        "contestType": c.race_type
                    })
                output['contests'] = clist
        output['status'] = "SUCCESS"
        

        return output

        

""" The Voter class takes an id and returns voter information or elections results."""
class Voter:
    def __init__(self, theID=False, ftype=False):
        self.id = theID
        self.type = ftype
        self.false = ('', ' ', False, '0')

    def getList(self):
        output = {}
        if self.type not in self.false:
            infoByVID = models.Voter.all().filter("voterID = ", self.id)
            infoByID = models.Voter.all().filter("idNumber = ", self.id)
            infoByPNO = models.Voter.all().filter("passport = ", self.id)
            infoBymID = models.Voter.all().filter("milID = ", self.id)
            voter = ""
            if len(list(infoByVID)) > 0:
              voter = infoByVID
            elif len(list(infoByID)) > 0:
              voter = infoByID
            elif len(list(infoByPNO)) > 0:
              voter = infoByPNO
            elif len(list(infoBymID)) > 0:
              voter = infoBymID
            output['status'] = 'SUCCESS'
            ps = models.PollingStation.all().filter("iebc_code = ", voter[0].pollingStation)[0]
            voter_location = Parent(ps.key(),"pollingstation").getParent()
            prezo = models.Contest.all().filter("race_type = ", getContentType("Presidential"))
            governor = models.Contest.all().filter("location_id = ", voter_location['county'].iebc_code).filter("race_type = ", getContentType("Governor"))
            senator = models.Contest.all().filter("location_id = ", voter_location['county'].iebc_code).filter("race_type = ", getContentType("Governor"))
            womenrep = models.Contest.all().filter("location_id = ", voter_location['county'].iebc_code).filter("race_type = ", getContentType("WomenRep"))
            mp = models.Contest.all().filter("location_id = ", voter_location['constituency'].iebc_code).filter("race_type = ", getContentType("MP"))
            caw = models.Contest.all().filter("location_id = ", voter_location['ward'].iebc_code).filter("race_type = ", getContentType("CAW"))
            psContests = {
                    "%s"%(prezo[0].race_title): [prezo[0].iebc_code, voter_location['county'].iebc_code],
                    "%s"%(governor[0].race_title): [governor[0].iebc_code, voter_location['county'].iebc_code],
                    "%s"%(senator[0].race_title): [senator[0].iebc_code, voter_location['county'].iebc_code],
                    "%s"%(womenrep[0].race_title): [womenrep[0].iebc_code, voter_location['county'].iebc_code],
                    "%s"%(mp[0].race_title): [mp[0].iebc_code, voter_location['constituency'].iebc_code],
                    "%s"%(caw[0].race_title): [caw[0].iebc_code, voter_location['ward'].iebc_code]
                }
            if self.type =="info": #when the self.type equals info the response will be voter information
                candidatesList = []
                for psC in psContests:
                    candidates = models.Contestant.all().filter("race_id = ", psContests[psC][0])
                    contestCandidates = []
                    for can in candidates:
                        party = party = models.Party.all().filter("iebc_code = ", can.party)[0]
                        contestCandidates.append({
                                "name": "%s %s" % (can.other_name, can.surname),
                                "code": can.iebc_code,
                                "party": party.name,
                                "party_symbol":party.symbol
                            })
                    candidatesList.append({
                            "contest": psC,
                            "candidates": contestCandidates
                        })
                    
                output['voter_info'] = {
                        "name": voter[0].name,
                        "gender": voter[0].gender,
                        "date": voter[0].date,
                        "contestant": voter[0].contestant,
                        "pollingStation": {
                                "streams":ps.no_of_streams,
                                "facility_type":ps.facility_type,
                                "electricity":ps.electricity,
                                "networks": ps.networks,
                                "accessibility":ps.accessibility,
                                "disability":ps.disability,
                                "point": ps.point
                            },
                        "ward": voter_location['ward'].name,
                        "constituency": voter_location['constituency'].name,
                        "county": voter_location['county'].name,
                        "contests":candidatesList
                    } 
            elif self.type == "results":
                voterResults = []
                for psC in psContests:
                    contestRes = []
                    canRes = models.CandidateTotals.all().filter("electoral_district_code = ", psContests[psC][1])
                    for cres in canRes:
                        contestRes.append({
                            "candidate": models.Contestant.all().filter("iebc_code = ", cres.candidate)[0].other_name,
                            "totals": cres.totals
                        })
                    voterResults.append({
                            "contest":psC,
                            "results":contestRes
                        })
                output["results"] = voterResults 
            else:
                  output['status'] = 'TYPE_ERROR'
                  output['message'] =  "Invalid type passed in the URL. Please use info or results for the type"

        else:
            output['status'] = 'TYPE_ERROR'
            output['message'] =  "Please specify a type. i.e. info or results"

        return output
            
""" The results class below is the class that will handle all sorts of results queries sent to the API. The category and category id determine the result response criteria."""
class Results:
    def __init__(self, cat=False, cat_id="", params={}):
        self.cat = cgi.escape(cat)
        self.cat_id = cat_id
        filterParams = ["county", "constituency","ward", "party", "post", "contest", "candidate"]
        self.ftype = ""
        self.ftype_id = 0
        self.election = "E2012"
        for param in params:
            if param in filterParams:
                self.ftype = param#this is the filter type for the url
                self.ftype_id = params[param]#this is the id of the filter given in ftype
            if param =="election":
                self.election = params[param]
        self.false = ('', ' ', False, '0', 0)
        
    """ This function of the results class returns a sum of the results passed to it """
    def getTotals(self, results):
        resultTotal =0;
        for result in results:
            resultTotal += int("%s"%(result.result))

        return resultTotal
    
    ##Get results based on the electoral district .    
    def resultsByED(self):
        eds = models.ElectralDistrict.all()
        if self.cat in ["constituency", "ward"]: #if the filter is of the type electoral district, filter the results by the electoral district defined by self.ftype_id
            if self.ftype in ["constituency", "ward","county"]:
                parent = models.ElectralDistrict.all().filter("iebc_code = ", self.ftype_id)[0]
                eds.ancestor(parent.key())
                
        eds.filter("etype = ", self.cat.lower())
        edsRow = []
        if self.cat_id not in self.false:
            eds.filter("iebc_code = ", self.cat_id)
        for ed in eds:
            contestRow = []
            contestsRes = models.ContestTotal.all()
            contestsRes.filter("electoral_district_code = ", ed.iebc_code)
            contestsRes.filter("election = ", self.election)
            if self.ftype == "post": # if post is defined filter the contest results by post
                contestsRes.filter("post = ", self.ftype_id)
            elif self.ftype == "contest": # if contest is defined filter the contest results by contest
                contestsRes.filter("contest_id = ", self.ftype_id)
            for conRes in contestsRes:
                candidates = models.Contestant.all()
                contestTitle = models.Contest.all().filter("iebc_code = ", conRes.contest_id)[0].race_title
                candidates.filter("race_id = ", conRes.contest_id)
                if self.ftype == "party": # if party is defined filter the contest by party
                    candidates.filter("party = ", self.ftype_id)
                rejectedRes = models.RejectedTotals.all().filter("election = ", self.election).filter("electoral_district_code = ",ed.iebc_code).filter("contest_id = ", conRes.contest_id)
                turnoutRes = models.VoterTurnoutTotals.all().filter("election = ", self.election).filter("electoral_district_code = ",ed.iebc_code).filter("contest_id = ", conRes.contest_id)
                disputedRes = models.DisputedTotals.all().filter("election = ", self.election).filter("electoral_district_code = ",ed.iebc_code).filter("contest_id = ", conRes.contest_id)
                contestResults = {
                        "contest":contestTitle,
                        "disputed":disputedRes[0].totals,
                        "rejected":rejectedRes[0].totals,
                        "turnout":[],
                        "results": []
                    }
                for tR in turnoutRes:
                    contestResults["turnout"] = tR.totals,
                canRes = {}
                for can in candidates:
                    party = models.Party.all().filter("iebc_code = ", can.party)[0]
                    res = models.CandidateTotals.all().filter("candidate = ", can.iebc_code).filter("electoral_district_code = ",ed.iebc_code)
                    canRes = {
                                "candidate": "%s %s"%(can.surname, can.other_name),
                                "candidate_id": can.iebc_code,
                                "party":party.name,
                                "party_id": party.iebc_code
                    }
                    for r in res:
                        canRes["total"]=r.totals                    

                    contestResults['results'] = canRes
                contestRow.append(contestResults)
 
            edsRow.append({
                    "name":ed.name,
                    "results":contestRow
                })
            
        return edsRow
    
    ##This is the function of the results class that handles request for party results"""
    def getResultsByParty(self):
        output = {}
        results = []

        contests = models.Contest.all()
        if self.ftype == "post": # if post is defined filter the contest by post
            contests.filter("race_type = ", self.ftype_id)
        elif self.ftype == "contest": # if contest is defined filter the contest by contest
            contests.filter("iebc_code = ", self.ftype_id)
        elif self.ftype == "candidate":
            canID = self.ftype_id
        #else:
            #contests.filter("race_type = ", "1")
        
        for contest in contests:
            contestRow ={}
            candidates = models.Contestant.all()
            if self.cat_id not in self.false: # check to see whether there is a party id defined
                candidates.filter("party = ", self.cat_id)
            if self.ftype =="candidate": # test whether a candidate is defined
                candidates.filter("iebc_code = ", canID)
            contestResults = {
                        "contest":contest.race_title,
                        "contestID":contest.iebc_code,
                        "results":[]
                    }
            for can in candidates:
                party = models.Party.all().filter("iebc_code = ", can.party)[0]
                res = models.CandidateTotals.all().filter("candidate = ", can.iebc_code).filter("election = ", self.election)
                if self.ftype == "contest":
                    res.filter("electoral_district_code = ", contest.location_id)
                if self.ftype in ["county", "constituency", "ward"]:
                    res.filter("electoral_district_code = ", self.ftype_id)
                for r in res: # loop through the list candidate results
                    contestResults["results"].append({
                            "candidate": "%s %s"%(can.surname, can.other_name),
                            "candidate_id": can.iebc_code,
                            "party":party.name,
                            "party_id": party.iebc_code,
                            "total": r.totals
                        })

            results.append(contestResults)
                
            
        return results
    
    ##This function returns results for the elective post defined by the cat """
    def getResultsByContest(self):
        contests = models.Contest.all()
        if self.cat_id not in self.false:
            contests.filter("iebc_code = ", self.cat_id)
        #else:
            #contests.filter("race_type = ", "1")
            
        if self.ftype == "post": # if post is defined filter the contest by post
            contests.filter("race_type = ", self.ftype_id)
        elif self.ftype == ["county", "constituency", "ward"]:
            contests.filter("location_id = ", self.ftype_id)
        elif self.ftype == "candidate":
            canID = self.ftype_id
        contestRow = []
        for contest in contests:
            rejectedRes = models.RejectedTotals.all().filter("election = ", self.election).filter("contest_id = ", contest.iebc_code)
            disputedRes = models.DisputedTotals.all().filter("election = ", self.election).filter("contest_id = ", contest.iebc_code)
            if self.ftype in ["county", "constituency", "ward"]:
                rejectedRes.filter("electoral_district_code = ", self.ftype_id)
                disputedRes.filter("electoral_district_code = ", self.ftype_id)

            rRes = 0 #the value of disputed results if no results are found
            dRes = 0 #the value of disputed results if no results are found
            for rR in rejectedRes:
                rRes = rR.totals
            for dR in disputedRes:
                dRes = dR.totals
            contestResults = {
                    "results":[],
                    "contest":contest.race_title,
                    "disputed":dRes,
                    "rejected":rRes,
                    "contestID":contest.iebc_code
            }
            candidates = models.Contestant.all()
            if self.cat_id not in self.false: # check to see whether there is a party id defined
                candidates.filter("race_id = ", self.cat_id)
            if self.ftype =="candidate": # test whether a candidate is defined
                candidates.filter("iebc_code = ", canID)

            for candidate in candidates:
                pname = ""
                pcode = ""
                party = models.Party.all().filter("iebc_code = ", candidate.party)
                for p in party:
                    pcode = p.iebc_code
                    pname = p.name
                
                res = models.CandidateTotals.all().filter("candidate = ", candidate.iebc_code).filter("election = ", self.election)
                if self.ftype in ["county", "constituency", "ward"]:
                    res.filter("electoral_district_code = ", self.ftype_id)
                for r in res:
                    contestResults["results"].append({
                                "name":"%s %s"%(candidate.other_name, candidate.surname),
                                "party":pname,
                                "party_id": pcode,
                                "location":r.electoral_district.name,
                                "locationID":r.electoral_district_code,
                                "totals":r.totals
                            })
                    
            
            contestRow.append(contestResults)
            
        return contestRow 
    
    def getList(self):
        
        """ #posts# This is a dictionary of the elective posts and their IEBC Codes """
        
        """#eds# this is a list of electoral district levels """ 
        eds = ['county', 'constituency', 'wards', 'pollingstation']
        output = {}
        results = []
        if self.cat == "contest":
            output = {
                "status":"SUCCESSS",
                "results": self.getResultsByContest()
            }
            
            return output
        #Get results for the electoral districts defined by the cat. Results returned depend on whether the cat_id is set(results within a specified electoral district) or not set(results will be for elective posts on the
        #electoral district defined by cat)"""                
        elif self.cat in eds:
            output = {
                "status":"SUCCESS",
                "result": self.resultsByED()
            }
            return output
        
        #this is the candidate result method
        elif self.cat == "candidate":
            output = {}
            results = []
            candidates = models.Contestant.all()
            if self.cat_id not in self.false:
                candidates.filter("iebc_code = ", self.cat_id)
            if self.ftype == "party":
                candidates.filter("party = ", self.ftype_id)
            elif self.ftype == "post":
                candidates.filter("race_type = ", self.ftype_id)
            elif self.ftype == "contest":
                candidates.filter("race_id = ", self.ftype_id)
    
            for candidate in candidates:
                contest = models.Contest.all().filter("iebc_code = ",candidate.race_id)[0]
                contestResults = {
                        "name":"%s %s"%(candidate.other_name, candidate.surname),
                        "contest":contest.race_title,
                        "contestID":contest.iebc_code,
                        "results":[]
                }
                res = models.CandidateTotals.all().filter("candidate = ", candidate.iebc_code).filter("election = ", self.election)
                if self.ftype in ["county", "constituency", "ward"]:
                    res.filter("electoral_district_code = ", self.ftype_id)
                for r in res:
                    contestResults["results"].append({
                                "location":r.electoral_district.name,
                                "locationID":r.electoral_district_code,
                                "totals":r.totals
                            })
                
                results.append(contestResults)

            output['status'] = 'SUCCESS'
            output['results'] = results
            return output
        
        #Get the results for the party defined by cat_id """
        elif self.cat == "party":
            output = {
                "status":"SUCCESS",
                "result": self.getResultsByParty()
            }
            return output
        
        else:
            elections  = models.Election.all()
            output['status'] = "SUCCESS"
            output['elections'] = list(elections)
            return output
            
