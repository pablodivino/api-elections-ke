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

from google.appengine.ext import db

from dataprovider import Parent

""" This shows the relationship between the various kinds """
edRelations = {
            "county": False,
            "constituency":"county",
            "ward":"constituency",
            "pollingstation":"ward",
            "candidate":"pollingstation",
            "results":"pollingstation",
            "voter":"pollingstation"
}

"""eClasses is a dictionary of db models"""
eClasses = {
          "country":models.ElectralDistrict.all,
          "county":models.ElectralDistrict.all,
          "constituency":models.ElectralDistrict.all,
          "ward":models.ElectralDistrict.all,
          "electoraldistrict":models.ElectralDistrict,
          "electivepost":models.ElectivePost.all,
          "pollingstation":models.PollingStation.all,
          "party":models.Party.all,
          "results":models.Results.all,
          "candidate":models.Contestant.all,
          "contest":models.Contest.all
}

"""Checks to see whether the entity already exists"""
def checkExist(model, test, codes):
    #model refers to the db model to perform the test on.
    #test this is the property of the model to use to test for exist
    #codes - this property holds a list of codes one for the entity the other for the parent and the parent type
    check = {} #this is a variable that holds the check results
    pKey = 0 #the variable holding the value of the parent key

    #grab the parent key.for the entity whose test property is defined bt codes[1]
    parent_entity = eClasses[codes[2]]()
    parent_entity.filter("iebc_code = ", codes[1])
        
    for k in parent_entity.fetch(1):
        pKey = k.key()
        
    #check to see if the entity exists in the datastore
    entity = eClasses[model]()
    if model != "results":
        entity.filter(test + ' = ', codes[0])
    else:
        entity.filter('resultID = ', test)
    existEn = False
    for en in entity.fetch(1):
        existEn = en

    if existEn is not False:
        check['status']= "True"
        check['entity'] = existEn
        check['parent'] = pKey
    else: 
        check['status']= "False"
        check['parent'] = pKey

    return check


def putEPosts(jFile):#this function handles entry of elective posts into the API
    epArray = jFile["results"]
    output = {}
    existItem = []
    for ep in epArray:#loop through the list of elective posts, check if they exist before saving them to the datastore
        testCodes = [ep["code"], ep['code'], "elective_post"]
        entityExist = checkExist("elective_post", "iebc_code", testCodes)
        if entityExist['status']=="False":
            epS = models.Party(key_name = ep["code"])
            # Test that the dict contains the key for a given model property
            if ep.has_key("code"):
                epS.iebc_code = ep["code"]
            if ep.has_key("name"):
                epS.post_name = ep["name"]
            epS.put()
        else:
            existItem.append(ep)
    output = {
            "exist":existItem
        }
    return output

def putContests(jFile):#this is the function used to input contests
    contestArray = jFile["results"]
    for contest in contestArray:
        testCodes = [contest['code'], contest['location_id'], contest['location_title']]
        entityExist = checkExist("contest", "iebc_code", testCodes)
        if entityExist['parent'] !=0:
            contest = models.Contest(key_name=contest['code'], parent=entityExist['parent'])
        elif entityExist['parent'] ==0:
            contest = models.Contest(key_name=contest['code'])
            contest.iebc_code = contest['code']
            contest.race_title = contest['race_title']
            contest.race_type = contest['race_type']
            contest.location_type = contest['location_type']
            contest.location_id = contest['location_id']
            contest.put()
        
def calculateTotals(result):#this is function is used to calculate candidate totals at each electoral district level
    pKey = ""#this will hold the key for the polling station
    results = result["results"]
    ps = models.PollingStation.all()
    ps.filter("iebc_code = ", result["psid"])
    contest = models.Contest.all()
    contest.filter("iebc_code = ", result["raceID"])
    pCon = "" # this will hold contest entity that the results are for
    #get the contest for the results
    for c in contest:
        pCon = c
    #get the polling station for the ruslts
    for p in ps:
        pKey = p.key()

    ancestors = Parent(pKey, 'pollingstation').getParent()#get the ancestors for the polling station
    for anc in ancestors:
        contestres = ancestors[anc].results.filter("contest_id = ", result["raceID"]).filter("election = ", result["election"])
        rejectedRes = 0 #this holds the entity for the rejected results for this ed
        disputedRes = 0 #this holds the entity for the disputed results for this ed
        candidateRes = 0 #this holds a list of entities for candidate results
        for cres in contestres:
            rejectedRes = cres.rejected_totals
            disputedRes = cres.disputed_totals
            candidateRes = cres.candidate_totals
            turnOutRes = cres.turnout

        ckeyname = "%s%s%s"%(result['election'],ancestors[anc].iebc_code, result['raceID'])#generates a keyname for this contest
        #contestT is the contest for which the results are for
        contestT = models.ContestTotal(key_name=ckeyname,
                                      contest_id=result['raceID'],
                                      election=result['election'],
                                      electoral_district=ancestors[anc],
                                      electoral_district_code=ancestors[anc].iebc_code,
                                      post = pCon.race_type).put()

        prevRejT = 0 # set the value of the previous rejected total to 0
        prevDisT = 0 # set the value of the previous disputed total to 0
        prevturnoutT = 0 # set the value of the previous turn total to 0
        prevRej = 0 # set the value of the previous rejected value from the PollingStation to 0
        prevDis = 0 # set the value of the previous disputed value from the PollingStation to 0
        prevturnout = 0 # set the value of the previous turnout from the PollingStation to 0
        if candidateRes != 0:
            for rT in rejectedRes:# set the value of prevRejT to the value of the totals of the rejected votes for the contest in this ed
                prevRejT = rT.totals
        if candidateRes != 0:
            for dT in disputedRes:# set the value of prevDisT to the value of the totals of the rejected votes for the contest in this ed
                prevDisT = dT.totals
        if candidateRes != 0:
            for t in turnOutRes:# set the value of turnoutT to the value of the totals of the turnout for the ed
                prevturnoutT = t.totals
    
        for r in results:
            prevResT = 0 # set the value of a candidates previous result to 0
            if candidateRes != 0:
                for canres in candidateRes.filter("candidate = ", r["CandidateID"]): #get the candidate totals for the candidate defined by r.CandidateID
                    prevResT = canres.totals
                
            testCodes = ["",result["psid"], "pollingstation"]
            testKey = "%s%s%s%s"%(r["CandidateID"], result["election"], result["psid"], result["status"])
            entityExist = checkExist("results", testKey, testCodes)#get the previous result for the candidate 
            if entityExist.has_key('entity'):
                prev_res = entityExist['entity'].result
                prevDis = entityExist['entity'].ps_disputed
                prevRej = entityExist['entity'].ps_rejected
                prevturnout = entityExist['entity'].ps_turnout
            else:
                prev_res = 0
                
            newCanT = int(prevResT)-int(prev_res)+int(r['votes'])
            newrejT = int(prevRejT) - int(prevRej) + int(result['rejected']) #this is the new rejected total for this contest in this ed
            newdisT = int(prevDisT) - int(prevDis) + int(result['disputed']) #this is the new disputed total for this contest in this ed
            newturnoutT = int(prevturnoutT) - int(prevturnout) + int(result['turnout']) #this is the new turnout total for this  ed
                
            models.CandidateTotals(key_name="%s%s"%(ckeyname,r["CandidateID"]),
                                      candidate=r["CandidateID"],
                                      totals=newCanT,
                                      contest=contestT,
                                      contest_id=result['raceID'],
                                      election=result['election'],
                                      electoral_district=ancestors[anc],
                                      electoral_district_code=ancestors[anc].iebc_code,
                                      post = pCon.race_type).put()# store the new candidate totals
            
            
        newrejT = int(prevRejT) - int(prevRej) + int(result['rejected']) #this is the new rejected total for this contest in this ed
        newdisT = int(prevDisT) - int(prevDis) + int(result['disputed']) #this is the new disputed total for this contest in this ed
        newturnoutT = int(prevturnoutT) - int(prevturnout) + int(result['turnout']) #this is the new turnout total for this  ed

        models.RejectedTotals(key_name=ckeyname,
                              totals=newrejT,
                              contest_id=result['raceID'],
                              election=result['election'],
                              electoral_district=ancestors[anc],
                              electoral_district_code=ancestors[anc].iebc_code,
                              post = pCon.race_type,
                              contest=contestT).put()# store the new rejected total to the datastore
        models.DisputedTotals(key_name=ckeyname,
                              totals=newdisT,
                              contest_id=result['raceID'],
                              election=result['election'],
                              electoral_district=ancestors[anc],
                              electoral_district_code=ancestors[anc].iebc_code,
                              post = pCon.race_type,
                              contest=contestT).put()# store the new disputed total to the datastore
        
        models.VoterTurnoutTotals(key_name=ckeyname,
                              totals=newturnoutT,
                              contest_id=result['raceID'],
                              election=result['election'],
                              electoral_district=ancestors[anc],
                              electoral_district_code=ancestors[anc].iebc_code,
                              post = pCon.race_type,
                              contest=contestT).put()# store the new disputed total to the datastore
        
def putResults(jFile, varz):#this function handles entry of results into the API
    resArray = jFile["results"]
    output = {}
    existItem = []
    ps_code = resArray["PollingCentreID"]
    election = resArray["election"]
    ps_name = resArray["PollingCentreName"]
    status = resArray["status"]
    race_id = resArray["raceID"]
    disputed = resArray["Disputed"]
    turnout = resArray["Turnout"]
    rejected = resArray["Rejected"]
    results = resArray["results"]
    calculateTotals({
                    "psid": ps_code,
                    "raceID": race_id,
                    "disputed":disputed,
                    "rejected":rejected,
                    "turnout":turnout,
                    "election":election,
                    "status":status,
                    "results":results
    })
    for result in results:#loop through the candidate results list and then store them to the datastore
        testCodes = ["",ps_code, "pollingstation"]
        #the test key below is a string created from the candidate code, election ID, polling station id
        testKey = "%s%s%s%s"%(result["CandidateID"], election, ps_code, status)
        #check whether a result with the testKey exists.
        entityExist = checkExist("results", testKey, testCodes)
        if entityExist['parent'] != 0:
            resS = models.Results(key_name = testKey, parent=entityExist['parent'])
            resS.candidate = result["CandidateID"]
            resS.ps_disputed = int(disputed)
            resS.ps_rejected = int(rejected)
            resS.ps_turnout = int(turnout)
            resS.raceID= race_id
            resS.ps_station = ps_code
            resS.election = election
            resS.result = int(result["votes"])
            resS.election = election
            
            if status in ['yes', 'Yes']:  
                resS.status = "confirmed"
            else: 
                resS.status = "provisional"
            
            resS.resultID = testKey
            resS.put()
        else:
            existItem.append({"Missing Polling station information in result row":res['pollingS']})
    output = {
            "exist":existItem
        }
    return output
                    

def putParties(jFile):#this function handles entry of parties into the API
    pArray = jFile["results"]
    output = {}
    existItem = []
    for p in pArray:#loop through the list of parties, check if they exist before saving them to the datastore
        testCodes = [p["pcode"], p['pcode'], "party"]
        entityExist = checkExist("party", "iebc_code", testCodes)
        if entityExist['status']=="False":
            if entityExist['parent'] != 0:
                pS = models.Party(key_name = p["pcode"], parent=entityExist['parent'])
            else:
                pS = models.Party(key_name = p["pcode"])
            # Test that the dict contains the key for a given model property
            if p.has_key("pcode"):
                pS.iebc_code = p["pcode"]
            if p.has_key("pname"):
                pS.name = p["pname"]
            if p.has_key("symbol"):
                pS.symbol = p["symbol"]
            if p.has_key("color"):
                pS.color = p["color"]
            if p.has_key("male"):
                pS.male = p["male"]
            if p.has_key("female"):
                pS.female = p["female"]
                
            pS.put()
        else:
            existItem.append(p)
    output = {
            "exist":existItem
        }
    return output
        

def putCandidates(jFile):#this function handles entry of candidates into the API
    canArray = jFile["results"]
    output = {}
    existItem = []
    for can in canArray:#loop through the list of candidates, check if they exist before saving them to the datastore
        testCodes = [can["ccode"], can['ps_station'], "pollingstation"]
        entityExist = checkExist("candidate", "iebc_code", testCodes)
        if entityExist['status']=="False":
            if entityExist['parent'] != 0:
                canS = models.Contestant(key_name = can["ccode"], parent=entityExist['parent'])
            else:
                canS = models.Contestant(key_name = can["ccode"])
            # Test that the dict contains the key for a given model property
            if can.has_key("ccode"):
                canS.iebc_code = can["ccode"]
            if can.has_key("cname"):
                canS.name = can["cname"]
            if can.has_key("voter_id"):
                canS.voter_id = can["voter_id"]
            if can.has_key("elective_post"):
                canS.race_id = can["elective_post"]
            if can.has_key("party"):
                canS.party = can["party"]
            if can.has_key("ps_station"):
                canS.p_polling_station = can["ps_station"]
            if can.has_key("independent"):
                canS.independent = can["independent"]
                
            canS.put()
        else:
            existItem.append(can)
    output = {
            "exist":existItem
        }
    return output
        

def putPStation(jFile):#this function is used to store polling stations into the API
    psArray  = jFile["results"]
    output = {}
    existItem = []
    for ps in psArray:#loop through the pollingstations in the array, check if it exists before storing it to the db
        testCodes = [ps["pscode"], ps["ward"].rstrip(), "ward"]
        entityExist = checkExist("pollingstation", "iebc_code", testCodes)
        if entityExist['status']=="False":
            if entityExist['parent'] != 0:
                pollS = models.PollingStation(key_name = ps["pscode"], parent=entityExist['parent'])

            else:
                pollS = models.PollingStation(key_name = ps["pscode"])
            
            # Test that the dict contains the key for a given model property
            if ps.has_key("pscode"):
                pollS.iebc_code = ps["pscode"]
            if ps.has_key("psname"):
                pollS.name = ps["psname"]
            if ps.has_key("gender"):
                pollS.gender = ps["gender"]
            if ps.has_key("reg_voter"):
                pollS.reg_voters = ps["reg_voter"]
            if ps.has_key("streams"):
                pollS.no_of_streams = ps["streams"]
            if ps.has_key("facility_type"):
                pollS.facility_type = ps["facility_type"]
            if ps.has_key("electricity"):
                pollS.electricity = ps["electricity"]
            if ps.has_key("networks"):
                pollS.networks = ps["networks"]
            if ps.has_key("accessibility"):
                pollS.accessibility = ps["accessibility"]
            if ps.has_key("latitude"):
                pollS.point = "%s,%s"%(str(ps["latitude"]), str(ps["longitude"]))
            pollS.put()
        else:
            existItem.append(ps)
    output = {
            "exist":existItem
        }
    return output

def put(etype, jsonFile, args={}):#this function receives a data type and the Json file, then passes the Json file to the relevant function for storage in DS
    eds = ["county", "constituency", "wards"]
    if etype in eds:
        return putED(jsonFile, etype)
    elif etype == "p_stations":
        return putPStation(jsonFile)
    elif etype == "contests":
        return putContests(jFile)
    elif etype == "candidates":
        return putCandidates(jsonFile)
    elif etype == "parties":
        return putParties(jsonFile)
    elif etype == "results":
        return putResults(jsonFile, args)
    elif etype == "election":
        return putElection(jsonFile, args)
    
def putED(jsonFile, etype):## Stores electoraldistricts into the datastore    
    eds = jsonFile['results']
    for ed in eds:
        if etype == "county":
            testCodes = [ed["iebc_code"], "KE", "country"]
            entityExist = checkExist("county", "iebc_code", testCodes)
            county = models.ElectralDistrict(key_name=ed['iebc_code'], parent=entityExist['parent'])
        elif etype == "constituency":
            testCodes = [ed["iebc_code"], ed["parent"], "county"]
            entityExist = checkExist("constituency", "iebc_code", testCodes)
            county = models.ElectralDistrict(key_name=ed['iebc_code'], parent=entityExist['parent'])
        elif etype == "wards":
            testCodes = [ed["iebc_code"], ed["parent"], "constituency"]
            entityExist = checkExist("ward", "iebc_code", testCodes)
            county = models.ElectralDistrict(key_name=ed['iebc_code'], parent=entityExist['parent'])
        county.name = ed['name']
        county.etype = ed['etype']
        county.iebc_code = ed['iebc_code']
        if ed.has_key("latitude"):
            county.point = "%s,%s" %(ed['latitude'], ed['longitude'])
            
        if ed.has_key("polygon"):
            county.polygon = ed['polygon']

        county.put()

    return {
            "exist": []
        }

def putEP(line):
    entityExist = checkExist("electivepost", "iebc_code", line, 'ElectivePost')
            
