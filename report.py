#!/usr/bin/env python
# -*- coding: utf-8 -*-

# API docs can be found here
# https://github.com/toggl/toggl_api_docs/blob/master/reports.md

import argparse
import settings
import json
import urllib
import logging
import datetime

_date_format = "%Y-%m-%d"

class Toggl(object):
    baseURL='https://toggl.com/'
    date_format = '%Y-%m-%d' #YYYY-MM-DD

    def __init__(self, api_token):
        self.logger = logging.getLogger(__name__)
        self.api_token = api_token
        chunks = self.baseURL.split("//", 1)
        if len(chunks) < 2: #no https? in url
            chunks[:0] = 'https:',
        self.baseURL = ''.join((chunks[0], "//", ":".join((self.api_token, 'api_token@')), chunks[1]))

    def _build_url(self, api_func, params):
        # build ULR of API request, which looks like:
        # https://${base_url}/{api_func}?param1=foo&param2=bar
        query = '' if params is None else '?' + urllib.urlencode(params)
        url =  ''.join((self.baseURL, api_func, query))
        self.logger.debug("_build_url: %s:"%url)
        return url

    def _get_json(self, url):
        try:
            response = urllib.urlopen(url)
        except IOError:
            self.logger.error('Failed to open url: %s'%url)
            raise
        response_text = response.read()
        self.logger.debug("Response from Toggl: %s"%response_text)
        response_json = json.loads(response_text)
        if 'error' in response_json:
            self.logger.error("""Error getting Toggl data:
            message: %(message)s
            tip: %(tip)s
            code: %(code)s"""%response_json['error'])
            raise
        return response_json

    def _request(self, api_func, params=None):
        url = self._build_url(api_func, params)
        return self._get_json(url)

    def get_workspaces(self):
        #get workspaces list
        data = self._request('api/v8/workspaces')

        #filter out personal workspaces:
        workspaces = [{'name': w['name'], 'id': w['id']} for w in data \
                            if 'personal' not in w['name'] and w['admin']]

        #get number of people in workspace
        print "\n\n\n"
        for workspace in workspaces:
            users = self._request('api/v8/workspaces/%s/users'%workspace['id'])
            workspace['members'] = sum([u['email'] not in settings.admin_emails for u in users])

        return workspaces

    def get_projects(self, workspace_id):
        data = self._request('api/v8/workspaces/%s/projects'%workspace_id)


    def weekly_report(self, workspace_id, since, until):
        """
        Toggl weekly report for a given team
        """
        #TODO: to support students failing the program, check number of team members for every week
        return self._request('reports/api/v2/weekly', {
            'workspace_id'  : workspace_id,
            'since'         : since.strftime(self.date_format),
            'until'         : until.strftime(self.date_format),
            'user_agent' : 'github.com/user2589/Toggl.py',
            'order_field': 'title', #title/day1/day2/day3/day4/day5/day6/day7/week_total
            'display_hours': 'decimal', #decimal/minutes
        })


def last_sunday(date):
    return date - datetime.timedelta(days = date.weekday()+1)

def week_list(start_date, end_date):
    """
    returns list of datetime tuples (monday, sunday) for every week in requested interval
    """
    w = []
    sunday = last_sunday(start_date)
    while sunday < end_date:
        monday = sunday - datetime.timedelta(days=6)
        w.append((monday, sunday))
        sunday += datetime.timedelta(days=7)
    return w

def create_chart():
    """
    Build chart URL using Google Static Chart API
    https://developers.google.com/chart/image/docs/chart_params
    """
    {
        'cht' : 'lc', # lc = line chart
    }
    pass

if __name__ =='__main__':
    logging.basicConfig(level=logging.DEBUG)
    #parse parameters
    parser = argparse.ArgumentParser(description='Create weekly time report for CMU SE programm for the past week.'
            ' HTML printed to stdout')
    parser.add_argument('-d', '--date', help='system date override, YYYY-MM-DD')
    args = parser.parse_args()
    if args.date is None:
        date = datetime.datetime.now()
        logging.debug("No date specified, using system date: %s"%date.strftime(_date_format))
    else:
        try:
            date = datetime.datetime.strptime(args.date, _date_format)
        except ValueError:
            parser.exit(1, "Invalid date\n")

    start_date = datetime.datetime.strptime(settings.start_date, _date_format)
    end_date = datetime.datetime.strptime(settings.end_date, _date_format)

    if date < start_date or date > end_date:
        parser.exit(1, "Date (%s) is out of the %s..%s range.\n Check dates in settings.py\n"%(
                date.strftime(_date_format), settings.start_date, settings.end_date))

    #create report
    report_builder = Toggl(settings.api_token)
    workspaces = report_builder.get_workspaces()
    projects = []

    # super_report has 3 dimensions: weeks, course (aka project), and team (aka workspace), i.e.:
    # for week in weeks:
    #    for course in courses:
    #        for team in teams:
    #            time = super_report[week][team][course]
    # week is a Monday of the reported week in _date_format
    super_report = {}

    # for each team request reports up to 'date', build list of project and aggregate stats
    # courses not in settings.core counted as meta project 'electives'
    weeks = week_list(start_date, end_date)

    for (monday, sunday) in weeks:

        if sunday > date:
            break
        week = monday.strftime(settings.report_date_format)
        super_report[week] = {}

        for workspace in workspaces:
            team = workspace['name']
            super_report[week][team] = {}
            super_report[week][team]['electives'] = 0
            report = report_builder.weekly_report(workspace['id'], monday, sunday)

            for project in report['data']:

                #project['totals'] is in miliseconds, divide by 3600000 to convert to hours
                hours = float(project['totals'][-1])/(3600000*workspace['members'])

                course = project['title']['project']
                if course in settings.core_courses:
                    super_report[week][team][course] = hours
                else:
                    super_report[week][team]['electives'] += hours


    logging.debug("Raw report JSON:\n %s"%json.dumps(super_report))

    #generate report file
    template_vars = {
        'core_courses'  : json.dumps(list(settings.core_courses)),
        'week_labels'   : json.dumps([monday.strftime(settings.report_date_format) for (monday, sunday) in weeks]),
        'report_data'   : json.dumps(super_report),
    }

    print settings.template%locals()