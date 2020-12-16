#!/usr/bin/env python3

# This python script is a simple tool to compile relevant job information using ZOAU
# You may view this as a "pro" version of the ZOAU Job function as it provides more details

#Import the Z Open Automation Utilities libraries as well as other libraries
from zoautil_py import Datasets, Jobs
from datetime import datetime
from termcolor import colored, cprint
import settings
import subprocess
import click

# Set up the global variables
allJobs = []
uabendList = []
sabendList = []
ccErrList = []
othersList = []
goodList = []


# The CLI options are as follow:
# --users | -u : Filter jobs by user. Default is wildcard search. Else, provide multiple values
# --filter | -f : Filter jobs by error. Options: cc, sabend, uabend, others, good. Default to no filter. May select multiple values.
# -ds : Output Dataset name. Will create or overwrite as necessary
# --output | -o : Output file location and name. Will create the file if it does not exist and overwrite any existing files.
# --no-banner : Do not show banner

# Examples:
# ./job-stat.py : Returns all jobs stats in a table and bar chart form
# ./job-stat.py -u Z07216 -u Z09999 -ds Z07216.OUTPUT(JOBCMPL) : Returns all jobs by users
# Z07216 and Z0999 and output details to Z07216.OUTPUT(JOBCMPL)

@click.command()
@click.option('--users', '-u', multiple=True, default=['*'])
@click.option('--filter', '-f', multiple=True)
@click.option('-ds')
@click.option('-o', '--output')
@click.option('--no-banner', is_flag=True)
def cli(users, filter, ds, output, no_banner):
  if not no_banner:
    printBanner()

  getJobs(users)
  # If there are error filters, filter the results accordingly
  if len(filter) != 0:
    filterJobs(filter)

  # Parse the data and display the remaining data
  displayStats(filter)

# Get all jobs based on user filter first. Date filter will be performed later.
def getJobs(filter):
  global allJobs
  if (type(filter) == tuple):
    if (len(filter) != 0):
      for user in filter:
        jobsList = Jobs.list(owner=user)
        if jobsList != None:
          allJobs.extend(jobsList)
  else:
    # Else, the wildcard will be used
    allJobs = Jobs.list(owner='*')

def printBanner():
 cprint("""
             __      __         _____ __        __ 
            / /___  / /_       / ___// /_____ _/ /_
       __  / / __ \/ __ \______\__ \/ __/ __ `/ __/
      / /_/ / /_/ / /_/ /_____/__/ / /_/ /_/ / /_  
      \____/\____/_.___/     /____/\__/\__,_/\__/  

  """, settings.OSColor, attrs=['bold'])

# Filter the jobs by error codes:
def filterJobs(filters):
  global allJobs, uabendList, sabendList, ccErrList, othersList, goodList

  tempList = []

  for f in filters:
    if f == 'uabend':
      uabendList = list(filter(userAbendFilter, allJobs))
      tempList.extend(uabendList)
    elif f == 'sabend':
      sabendList  = list(filter(systemAbendFilter, allJobs))
      tempList.extend(sabendList)
    elif f == 'cc':
      ccErrList = list(filter(ccErrFilter, allJobs))
      tempList.extend(ccErrList)
    elif f == 'others':
      othersList = list(filter(othersFilter, allJobs))
      tempList.extend(othersList)
    elif f == 'good':
      goodList = list(filter(goodFilter, allJobs))
      tempList.extend(goodList)
    else:
      print(f'Filter {f} not valid. Skipping this.')
  
  allJobs = tempList

# All the separate filters used:
def userAbendFilter(job):
  if (job['status'] == 'ABEND' and job['return'][:1] == 'U'):
    return True
  return False

def systemAbendFilter(job):
  if (job['status'] == 'ABEND' and job['return'][:1] == 'S'):
    return True
  return False

def ccErrFilter(job):
  if (job['status'] == 'CC' and job['return'] != '0000'):
    return True
  return False

def othersFilter(job):
  code = job['status']
  if (code != 'ABEND' and code != 'CC'):
    return True
  return False

def goodFilter(job):
  if (job['status'] == 'CC' and job['return'] == '0000'):
    return True
  return False


def displayStats(filters):
  # declare global variables and local ones
  global allJobs, uabendList, sabendList, ccErrList, othersList, goodList
  goodCount = 0
  userAbend = 0
  systemAbend = 0
  conditionCode = 0
  others = 0

  # If filters are not enabled, we have to manually sieve them out
  print(filters)
  if filters != None and len(filters) == 0:
    uabendList = list(filter(userAbendFilter, allJobs))
    sabendList  = list(filter(systemAbendFilter, allJobs))
    ccErrList = list(filter(ccErrFilter, allJobs))
    othersList = list(filter(othersFilter, allJobs))
    goodList = list(filter(goodFilter, allJobs))

  # Check for the various kind of errors to provide an overview
  # Perform various calculations
  jobCount = len(allJobs)
  systemAbend = len(sabendList)
  userAbend = len(uabendList)
  conditionCode = len(ccErrList)
  others = len(othersList)
  goodCount = len(goodList)

  # for job in allJobs:
  #   # Check Abend code
  #   if (job['status'] == 'ABEND'):
  #     if (job['return'][:1] == 'S'):
  #       systemAbend += 1
  #     elif (job['return'][:1] == 'U'):
  #       userAbend += 1
  #     else:
  #       others += 1
  #   # Check CC codes
  #   elif (job['status'] == 'CC'):
  #     if (job['return'] == '0000'):
  #       goodCount += 1
  #     else:
  #       conditionCode += 1
  #   else:
  #     others += 1

  # The following is used for printing:
  # Set up the table headers and borders first
  count = 0
  table_header = ['Sys Abend', 'User Abend', 'CC Err', 'Others', 'Good!', 'Total', 'Percentage']
  percentage = 0 if jobCount == 0 else round(goodCount / jobCount * 100, 2)
  table_data = [systemAbend, userAbend, conditionCode, others, goodCount, jobCount, percentage]
  # Need to add the number of dividers
  dividers_len = 15 * len(table_header) + len(table_header) + 1

  # Print the top border
  divider_format = "{:-^{num}}"
  cprint(divider_format.format('', num = dividers_len), 'magenta')

  # Print the header itself
  colors = settings.tableColor
  row_format ="{:^15}"
  # Fenceposting...
  print('|', end='')
  for header in table_header:
    cprint(row_format.format(header), colors[count], end='')
    cprint('|', colors[count], end='')
    count += 1
  print('\n' + divider_format.format('', num = dividers_len))
  print('|', end='')

  # Print the data row, again using fencepost technique
  count = 0
  for data in table_data:
    cprint(row_format.format(data), colors[count], end='')
    cprint('|', colors[count], end='')
    count += 1
  print('\n' + divider_format.format('', num = dividers_len), end='\n\n')

  # Print individual breakdown in a nice "bar" chart
  chartDict = {
    'ABEND': {
      'num': 0 if jobCount == 0 else round((systemAbend + userAbend) / jobCount * 100),
      'color': settings.systemAbendColor
    },
    'CC': {
      'num': 0 if jobCount == 0 else round(conditionCode / jobCount * 100),
      'color': settings.conditionCodeColor
    },
    'Others': {
      'num': 0 if jobCount == 0 else round(others / jobCount * 100),
      'color': settings.othersErrColor}
      ,
    'Perfect': {
      'num': 0 if jobCount == 0 else round(goodCount / jobCount * 100),
      'color': settings.goodJobsColor
    }
  }

  cprint('Breakdown:', 'white', attrs=['underline'])
  for category in chartDict:
    cprint('{:<8}'.format(category) + '{:|<{num}} {num}%'.format('', num=chartDict[category]['num']), chartDict[category]['color'])


if __name__ == '__main__':
  cli()