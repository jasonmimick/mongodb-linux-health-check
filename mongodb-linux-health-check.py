#
# mdiag-processor
#
# This script will analyse the output of mdiag.sh,
# and produce a report showing the result of each test.
#
#

#Appropriate NUMA zone_reclaim_mode setting
#SELinux disabled
#Swap enabled
#Appropriate ulimits: number of open files (nofile)
#Appropriate ulimits: number of processes (nproc)
#ulimits configured to be retained after restart
#Appropriate TCP keepalive timeout
#Appropriate kernel.pid_max setting
#Appropriate kernel.threads-max setting
#Appropriate fs.file-max setting
#Transparent HugePages (THP) "enabled" flag is not set to "always"
#Transparent HugePages (THP) "defrag" flag is not set to "always"
#Transparent HugePages (THP) "khugepaged defrag" flag is disabled
#MongoDB server configuration is stored in config file
##Single MongoDB server process (mongod or mongos) on host
#Memory ballooning drivers are not present
#No MongoDB traffic is impeded by iptables
#Supported Operating System
#Recommended Operating System

import sys
import os
import subprocess
import shlex
import traceback
import argparse
import datetime
import platform
from pprint import pprint
import yaml
import json
def run_test_cmd(test):
    result = {}
    process = subprocess.Popen( shlex.split(test["cmd"]),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    output,error = process.communicate()
    result["test_rc"] = process.returncode
    result["test_output"] = output
    result["test_error"] = error
    return result

def check_test_pass(test,rtc):
    result = {}
    result['overall']=False
    return result

def check_test_fail(test,rtc):
    result = {}
    result['overall']=False
    return result

def run_test(test,args):
    result = {}
    result["test"] = test['test']
    if args.verbose:
        result["test_input"]=test
    try: 
        rtc = run_test_cmd(test) 
        result["cmd_result"] = rtc 
        result["test_pass"] = check_test_pass(test,rtc)
        result["test_fail"] = check_test_fail(test,rtc)
    except Exception as ex:
        result["exception"] = "%s\n%s" % (ex, traceback.format_exc())
    return result

def generate_report(test_results):
    report = []
    header = {}
    header['report'] = "AEM MongoDB Linux System Health Check"
    header['timestamp'] = "%s" % datetime.datetime.now()
    header['timestamp_utc'] = "%s" % datetime.datetime.utcnow()
    header['hostname'] = "%s" % platform.node()
    header['platform'] = "%s" % ",".join(platform.uname())
    report.append(header)
    for result in test_results:
        section = {}
        section['test'] = "%s" % result['test']
        if 'exception' in result:
            section['exception'] = "%s" % result['exception']
        else:
            section['pass'] = "%s" % result['test_pass']
            section['fail'] = "%s" % result['test_fail']
            if args.verbose:
                section['test_output'] = "%s" % result["cmd_result"]["test_output"]
                section['test_error'] = "%s" % result["cmd_result"]["test_error"]
        report.append(section)
    return report

def output_report(format,report):
    if format == "yaml":
        yaml.dump(report, sys.stdout, default_flow_style=False)
    elif format == "json":
        json.dump(report, sys.stdout, indent=4)
    else:    # default, does pretty
        pprint(report)
        
        

desc = "mongodb-linux-health-check"
epilog = '''mongodb-linux-health check is a tool which runs
system commands to validate recommended settings found in the
MongoDB Production Notes. The output of this tool is for 
informational purposes only and not intended to be an official
or certified report. The tool does require root-level privileges 
to function properly.
'''
parser = argparse.ArgumentParser(description=desc,
                                 epilog=epilog)
parser.add_argument("--verbose",
                    action='store_true',
                    default=False,
                    help='Output verbose report.')
parser.add_argument("--format",
                    choices=[ 'pretty', 'yaml', 'json' ],
                    default='pretty',
                    help='Specify the report output format')
parser.add_argument("--tests",
                    default='mongodb-linux-hc-tests-v0.0.1.yaml',
                    help='Override default yaml file with test definitions')
args = parser.parse_args()

tests = yaml.load( open(os.path.join(sys.path[0], args.tests) ) )
results = []
run_log = []
if args.verbose:
    run_log.append( { "info" : "Verbose mode enabled" })
for test in tests:
   test_run = {}
   if args.verbose:
       test_run["test"] = test['test']
       test_run["start_ts"] = "%s" % datetime.datetime.now()
   results.append( run_test(test,args) )
   if args.verbose:
       test_run["stop_ts"] = "%s" % datetime.datetime.now()
       run_log.append(test_run)
report = generate_report(results)
if args.verbose:
   report.append( { "verbose_run_log" : run_log } )
output_report(args.format, report)
