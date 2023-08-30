#!/usr/bin/python2.7

# grouper_find_members
# get the list of group members, select one of these options:
# all members
# effective (indirect)
# immediate (direct)
# composite
# nonimmediate

import httplib2
import json
import configparser
from pprint import pprint
from pennperson_lsp import return_user_details


def parseConfFile(f):
    config = configparser.ConfigParser()
    config.read(f)
    return (config['DEFAULT']['servicehost'],
            config['DEFAULT']['u'],
            config['DEFAULT']['p'])


def main():
    # group for api call
    thisGroup = 'penn:isc:security:apps:group_securityLiaisons_dev'
    # OPTIONS: 'ALL', 'EFFECTIVE', 'IMMEDIATE', 'COMPOSITE', 'NONIMMEDIATE'
    thisFilter = 'ALL'

    # initialize httplib2
    http = httplib2.Http()

    # set the grouper URI (dev or prod), username, password
    grouper_ws_uri = grouperWSParameters(http)

    # get group members
    getMembers = grouperGetMembersWithFilter(
        http, grouper_ws_uri, thisGroup, thisFilter)
    result = getMembers['WsGetMembersResults']['resultMetadata']
    if getMembers and result['resultCode'] == 'SUCCESS':
        if 'wsSubjects' not in getMembers['WsGetMembersResults']['results'][0]:
            # no members found using this member filter
            print("None")
            exit(0)
        members = getMembers['WsGetMembersResults']['results'][0]['wsSubjects']
        li = []
        for nmembers in range(0, len(members)):
            member = members[nmembers]
            name = member['name']
            subjectId = member['id']
            details = return_user_details(subjectId)
            if details is not None:
                (affil, pennid, username, name, email, res,
                 schctr, orgcode, customer, lspemail) = details
                if len(customer) == 0:
                    customer = 'Unknown'
            else:
                continue

            # there are three member types, identified by their source
            # if source=idm then subjectId contains the UNI
            #  and name contains the person's name
            # if source=g:gsa then subjectId contains the UUID of the subgroup
            #  and name contains the groupd ID path of the subgroup
            # if source=externalUsers then subjectId contains the email address
            #  and name contains the person's name
            li.append({'name': name, 'pennkey': subjectId,
                      'email': email, 'schctr': customer})
        return li
    else:
        print("group not found (does not exist or is not accessible)")


def grouperGetMembersWithFilter(http, grouper_ws_uri, groupName, memberFilter):
    body = {
        "WsRestGetMembersRequest": {
            "includeSubjectDetail": "T",
            "memberFilter": memberFilter,
            "wsGroupLookups": [{
                "groupName": groupName
            }]
        }
    }
    result = grouperWSRequest(http, grouper_ws_uri+"/groups", "POST", body)
    return result


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
    pprint(content)
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
