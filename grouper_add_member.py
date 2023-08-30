#!/usr/bin/python2.7

# grouper_add_member
# add the specified UNI or group to the target group

import httplib2
import json
import configparser
from pprint import pprint


def parseConfFile(f):
    config = configparser.ConfigParser()
    config.read(f)
    return (config['DEFAULT']['servicehost'],
            config['DEFAULT']['u'],
            config['DEFAULT']['p'])


def main(memberId):
    # group for api call
    thisMember = memberId
    thisGroup = 'penn:isc:security:apps:group_securityLiaisons_dev'

    # initialize httplib2
    http = httplib2.Http()

    # set the grouper URI (dev or prod), username, password
    grouper_ws_uri = grouperWSParameters(http)

    # verify that the target group exists and is accessible by this user
    if grouperGetUuid(http, grouper_ws_uri, thisGroup) == 0:
        print(thisGroup +
              " group not found (does not exist or is not accessible)")
        exit(1)

    # examine thisMember to decide whether it is a UNI or a group
    # does thisMember string contain a colon?
    if thisMember.find(':') == -1:
        # thisMember does not contain a colon so it must be a UNI
        addMember = grouperAddMember(
            http, grouper_ws_uri, thisGroup, thisMember)
        result = addMember['WsAddMemberResults']['results'][0]['resultMetadata']
        if addMember and result['success']:
            if result['resultCode'] == 'SUCCESS_ALREADY_EXISTED':
                print(thisMember+' is already a member of '+thisGroup)
            elif result['resultCode'] == 'SUCCESS':
                print(thisMember+' is now a member of '+thisGroup)
        else:
            print('unable to add '+thisMember+' as a member of '+thisGroup)
    else:
        # thisMember contains a colon so it must be a group id path
        thisMemberUuid = grouperGetUuid(http, grouper_ws_uri, thisMember)
        if thisMemberUuid == 0:
            print(thisMember +
                  " group not found (does not exist or is not accessible)")
            exit(1)
        # add the UUID of thisMember as a member of thisGroup
        addMember = grouperAddMember(
            http, grouper_ws_uri, thisGroup, thisMemberUuid)
        result = addMember['WsAddMemberResults']['results'][0]['resultMetadata']
        if addMember and result['success']:
            if addMember and result['resultCode'] == 'SUCCESS_ALREADY_EXISTED':
                print(thisMember+' is already a member of '+thisGroup)
            elif addMember and result['resultCode'] == 'SUCCESS':
                print(thisMember+' is now a member of '+thisGroup)
        else:
            print('unable to add '+thisMember+' as a member of '+thisGroup)


def grouperAddMember(http, grouper_ws_uri, groupName, subjectId):
    # add group member
    body = {
        "WsRestAddMemberRequest": {
            "wsGroupLookup": {
                "groupName": groupName
            },
            "replaceAllExisting": "F",
            "subjectLookups": [
                {
                    "subjectId": subjectId
                }
            ]
        }
    }
    result = grouperWSRequest(http, grouper_ws_uri +
                              "/groups/"+groupName+"/members", "PUT", body)
    return result


def grouperGetUuid(http, grouper_ws_uri, groupName):
    # get UUID for the specified group
    thisuuid = 0
    body = {
        "WsRestFindGroupsRequest": {
            "wsQueryFilter": {
                "groupName": groupName,
                "queryFilterType": "FIND_BY_GROUP_NAME_EXACT",
            }
        }
    }
    findGroups = grouperWSRequest(
        http, grouper_ws_uri + "/groups", "POST", body)
    result = findGroups['WsFindGroupsResults']['resultMetadata']
    if findGroups and result['success'] and \
            'groupResults' in findGroups['WsFindGroupsResults']:
        thisuuid = findGroups['WsFindGroupsResults']['groupResults'][0]['uuid']
    return thisuuid


def grouperWSRequest(http, url, method, body):
    # send a request to the Grouper Web Service
    content_type = 'application/x-www-form-urlencoded'
    if method == "POST" or method == "PUT":
        content_type = 'text/x-json; charset=UTF-8'

    try:
        resp, content = http.request(uri=url,
                                     method=method,
                                     body=json.dumps(body),
                                     headers={'Content-Type': content_type})
        if resp.status == 200 or resp.status == 201:
            result = json.loads(content.decode('utf-8'))
            return result
    except httplib2.ServerNotFoundError as err:
        print("Unable to connect to Grouper Web Service")
        print(err)
        return None
    # http request failed, print the response status and content
    print("http response status "+str(resp.status))
    # print("http response content "+content)
    return None


def grouperWSParameters(http):
    # set the Grouper Web Service username and password
    confFile = 'penngroups.ini'
    pennIDargs = "/grouperWs/servicesRest/v2_4_000"  # /subjects/PENNID/groups
    servicehost, u, p = parseConfFile(confFile)
    grouper_username = u
    grouper_password = p
    http.add_credentials(name=grouper_username, password=grouper_password)

    # the Grouper Web Service URI should point to dev or prod Grouper
    devGrouperURI = servicehost + pennIDargs
    return devGrouperURI


if __name__ == '__main__':
    main()
