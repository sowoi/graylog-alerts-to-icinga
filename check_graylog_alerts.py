#!/usr/bin/env python3
# Developer: Massoud Ahmed 
# Additional Authors: Dominik Riva


import sys, socket, argparse, json, requests, urllib3, ipaddress, logging
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from optparse import OptionParser, OptionGroup

LOGGER = logging.getLogger('check_graylog_alert')


UNKNOWN = -1
OK = 0
WARNING = 1
CRITICAL = 2

headers = {
    'X-Requested-By': 'cli',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}

def search_graylog_for_alerts(headers, session_id, host, query, machine, timerange, crit, warn, result,proto):

    base = (proto +"://" + host+ ":"+port+"/api/events/search")
    LOGGER.debug("Using "+ base+ " to search ")

    data = '{"sort_direction": "desc", "timerange": { "type": "relative", "from" : "'+timerange+'"},  "query": "'+query+'",  "sort_by": "timestamp"}'   

    searching = requests.post(base, headers=headers, data=data, verify=False, auth=(session_id, 'session'))
    result = []
    resultJson = searching.json()
    for events in resultJson['events']:
         LOGGER.debug("Found event "+ str(resultJson['events']))
         extract = events['event']['fields']

         keys = unpackGraylogKeys(*extract.keys())       
         values = unpackGraylogKeys(*extract.values())
         alertExtract = "Alert "+str(events['event']['message']) + " found. Triggerd on "+str(events['event']['timestamp']) + " with values "+values+" ("+keys+") "
         if machine == "all":       
          result.append(alertExtract)
         else:
             if machine in alertExtract:
                 LOGGER.debug("Found machine "+ machine + " in event " + str(resultJson['events']))
                 result.append(alertExtract)
    if len(result) > 0:
        if machine != "all":
         resultEvaluation="CRITICAL. "+str(len(result))+ " Alert(s) found for " + machine + " : \n"+ str(("\n").join(result))
         crit = 1
        else:
         resultEvaluation="CRITICAL. "+str(len(result))+ " Alert(s) found: \n"+ str(("\n").join(result))
         crit = 1
    else:
        if machine != "all":
         resultEvaluation="OK. No alerts found for machine "+ machine + " within last " + timerange + " seconds"
        else:
         resultEvaluation="OK. No alerts found within last " + timerange + " seconds"
         LOGGER.debug("No alerts for "+ machine)

    return resultEvaluation.replace("=",":").replace("()","").replace("|"," "),crit
        

def unpackGraylogKeys(*args):
    return(','.join(args))


def create_session(headers, host,user,password):
    # create session id for api request

    base = ("https://" + host+ ":" + port + "/api/system/sessions")
    LOGGER.debug("Using "+ base+ " in order to create session id ")
    proto = "https"
    data = '{"username":"'+user+'", "password":"'+password+'", "host":""}'
    try:
     session = requests.post(base, headers=headers, data=data, verify=False)
     session = session.json()
     session_id = session['session_id']
     LOGGER.debug("Successfully created session_id "+ str(session['session_id']))
     LOGGER.debug("Valid until " + str(session['valid_until']))
    except Exception as ex:
     LOGGER.debug(ex)
     try:
      base = ("http://" + host+ ":"+port+"/api/system/sessions")
      LOGGER.debug("https did not work. Using "+ base+ " instead")
      proto="http"
      data = '{"username":"'+user+'", "password":"'+password+'", "host":""}'
      session = requests.post(base, headers=headers, data=data)
      session = session.json()
      session_id = session['session_id']
      LOGGER.debug("Successfully created session_id "+ str(session['session_id']))
      LOGGER.debug("Valid until " + str(session['valid_until']))
     except Exception as ex:
      LOGGER.debug(ex)
      LOGGER.debug("ERROR: Could not create session_id!")
      exit(2)

    return proto,session['session_id']







if __name__ == "__main__":

        desc='''%prog checks graylog stream for alerts. you need to setup alerts beforehand. \n Example: %prog -H 192.168.134.11 -u admin -p secret -m testmachine -t 33 '''
        parser = OptionParser(description=desc)
        gen_opts = OptionGroup(parser, "Generic options")
        host_opts = OptionGroup(parser, "Host options")
        port_opts = OptionGroup(parser, "Port options")
        user_opts = OptionGroup(parser, "User options")
        password_opts = OptionGroup(parser, "Password options")
        machine_opts = OptionGroup(parser, "Machine options")
        time_opts = OptionGroup(parser, "Timerange options")
        query_opts = OptionGroup(parser, "Query options")
        parser.add_option_group(gen_opts)
        parser.add_option_group(host_opts)
        parser.add_option_group(port_opts)
        parser.add_option_group(user_opts)
        parser.add_option_group(password_opts)
        parser.add_option_group(machine_opts)
        parser.add_option_group(time_opts)
        parser.add_option_group(query_opts)


        #-d / --debug
        gen_opts.add_option("-d", "--debug", dest="debug", default=False, action="store_true", help="enable debugging outputs (default: no)")

        #-H / --host
        host_opts.add_option("-H", "--host", dest="host", default="", action="store", metavar="HOST", help="defines graylog  hostname or IP")

	#-P / --port
        port_opts.add_option("-P", "--port", dest="port", default="9000", action="store", metavar="PORT", help="defines graylog  port")

        #-u / --user
        user_opts.add_option("-u", "--user", dest="graylog_user",  default="admin", action="store",metavar="USER", help="graylog user with access to API and event stream  (default: admin)")

        #-p / --password
        password_opts.add_option("-p", "--password", dest="graylog_password", default="", action="store", metavar="PASSWORD", help="graylog user password (default: none)")

        #-q / --query
        query_opts.add_option("-q", "--query", dest="graylog_search_query", default=" ", action="store", metavar="QUERY", help="graylog search query (default: show all queries)")

        #-m / --machine
        machine_opts.add_option("-m", "--machine", dest="graylog_machine", default="all", action="store", type="string", metavar="MACHINE", help="machine to check for in graylog stream  (default: all)")

        #-t / --time
        time_opts.add_option("-t", "--time", dest="timerange", action="store", default="86400", metavar="TIMERANGE", type="string", help="timerange since now in seconds (default 86400)")

        #parse arguments
        (options, args) = parser.parse_args()

        host = options.host
        port = options.port
        user = options.graylog_user
        password = options.graylog_password
        query = options.graylog_search_query
        machine = options.graylog_machine
        timerange = options.timerange
        crit = 0
        warn = 0
        result = ""
        #set loggin
        if options.debug:
          logging.basicConfig(level=logging.DEBUG)
          LOGGER.setLevel(logging.DEBUG)
        else:
          logging.basicConfig()
          LOGGER.setLevel(logging.INFO)
        
        proto,session_id = create_session(headers, host, user, password)
        result,crit = search_graylog_for_alerts(headers, session_id, host, query, machine, timerange, crit, warn, result, proto)
        if crit == 1:
            print(result)
            sys.exit(2)
        else:
            print(result)
            sys.exit(0)
