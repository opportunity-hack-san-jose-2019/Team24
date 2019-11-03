import requests
import logging
import json
import base64
import pickle
from argparse import ArgumentParser
import pickle
import os.path
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

argp = ArgumentParser()
argp.add_argument("--url", type=str, default="https://test.salesforce.com/")
argp.add_argument("--username", type=str, default="alyxe.lett@codenation.org.alyxebox")
argp.add_argument("--password", type=str, default="Ixiim*19!")
argp.add_argument("--client_id", type=str, default="3MVG9PbQtiUzNgN6IWvFCmHIpvWitEQ_fd7SM5a5da54PERNu6.nS3nl3aHVEZQWdNbipJtrhMvaJC5kp1Mel")
argp.add_argument("--client_secret", type=str, default="EBD022CAE6699776E5E688272C02FF9099FC8DC3C8B085482CDB64A6EBD4560C")
argp.add_argument("--token", type=str, default="7peG77TFoMYHSdQUAqE0CN3n")
args = argp.parse_args()

def initialize_logger(output_dir):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

loggin = initialize_logger('myLog.log')

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/classroom.coursework.students.readonly', 'https://www.googleapis.com/auth/classroom.rosters.readonly', 'https://www.googleapis.com/auth/classroom.courses.readonly']

def getDataFromGoogleClassRoom():
    """Shows basic usage of the Classroom API.
    Prints the names of the first 10 courses the user has access to.
    """
    creds = None
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1" # BUG
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('classroom', 'v1', credentials=creds)

    # Call the Classroom API

    courses = service.courses().list().execute()
    for course in courses.get('courses', []):
        students = service.courses().students().list(courseId = course['id']).execute()
        course.update( students )
        courseWorks = service.courses().courseWork().list(courseId = course['id']).execute()
        course.update( courseWorks )
        logging.info(course.get('name', ''))
        for courseWork in course.get('courseWork', []):
            logging.info('-- {}'.format(courseWork.get('title', '')))
            dateP = courseWork.get('dueDate', {'year':0, 'month':0, 'day':0})
            timeP = courseWork.get('dueTime', {'hours':0, 'minutes':0})
            courseWork.update({'dueDate': ''})
            courseWork['dueDate'] = str(dateP.get('month', 0)) + '/' + str(dateP.get('day', 0)) + '/' + str(dateP.get('year', 0))
            courseWork.update({'dueTime': ''})
            courseWork['dueTime'] = str(timeP.get('hours', 0)) + ':' + str(timeP.get('minutes', 0))
            studentSubmissions = service.courses().courseWork().studentSubmissions().list(courseId = course['id'], courseWorkId = courseWork['id']).execute()
            courseWork.update( studentSubmissions )

    students = []
    for course in courses.get('courses', []):
        for student_data in course.get('students', []):
            student = {}
            student['courseId__c'] = student_data.get('courseId')
            student['userId__c'] = student_data.get('userId')
            student['familyName__c'] = student_data.get('profile').get('name').get('familyName')
            student['fullName__c'] = student_data.get('profile').get('name').get('fullName')
            student['givenName__c'] = student_data.get('profile').get('name').get('givenName')
            student['verifiedTeacher__c'] = student_data.get('profile').get('verifiedTeacher', False)
            students.append(student)

    course_work_list = []
    for each_course in courses.get('courses', []):
        this_course_work = each_course.get('courseWork', [])
        for each_small_course_work in this_course_work:
            if each_small_course_work.get('studentSubmissions', []) == []:
                continue
            for each_student_submission in each_small_course_work.get('studentSubmissions'):
                course_work = {}
                course_work['alternateLink__c'] = each_small_course_work.get('alternateLink', 'N/A')
                course_work['assignedGrade__c'] = each_student_submission.get('assignedGrade', 0)
                course_work['assigneeMode__c'] = each_small_course_work.get('assigneeMode', 'N/A')
                course_work['courseId__c'] =  each_small_course_work.get('courseId', 'N/A')
                course_work['courseworkId__c'] = each_small_course_work.get('id', 'N/A')
                course_work['creationTime__c'] = each_small_course_work.get('creationTime', 'N/A')
                course_work['creatorUserId__c'] = each_small_course_work.get('creatorUserId', 'N/A')
                course_work['description__c'] = each_small_course_work.get('description', 'N/A')
                course_work['dueDate__c'] = each_small_course_work.get('dueDate', 'N/A')
                course_work['dueTime__c'] = each_small_course_work.get('dueTime', 'N/A')
                course_work['late__c'] = each_student_submission.get('late', False)
                course_work['maxPoints__c'] = each_small_course_work.get('maxPoints', 0)
                course_work['publish_state__c'] = each_small_course_work.get('state', 'N/A')
                course_work['state__c'] = each_student_submission.get('state', 'N/A')
                course_work['submissionModificationMode__c'] = each_small_course_work.get('submissionModificationMode', 'N/A')
                course_work['title__c'] = each_small_course_work.get('title','N/A')
                course_work['topicId__c'] = each_small_course_work.get('topicId','N/A')
                course_work['updateTime__c'] = each_small_course_work.get('updateTime','N/A')
                course_work['userId__c'] = each_student_submission.get('userId','N/A')
                course_work['workType__c'] = each_small_course_work.get('workType', 'N/A')
                course_work_list.append(course_work)

    attributes_course = ['alternateLink', 'calendarId', 'courseGroupEmail', 'courseState',
                         'creationTime', 'descriptionHeading', 'enrollmentCode', 'guardiansEnabled',
                         'id', 'name','ownerId','room','section','teacherGroupEmail','updateTime']

    courses_list = []
    for each_course in courses.get('courses', []):
        each_course_dict = {}
        for each_key in attributes_course:
            if str(each_key) == 'id':
                each_course_dict['courseId__c'] = each_course.get(each_key)
            elif str(each_key) == 'name':
                each_course_dict['courseName__c'] = each_course.get(each_key,'N/A')
            elif isinstance(each_course.get(each_key), list) or isinstance(each_course.get(each_key), dict):
                continue
            elif isinstance(each_course.get(each_key), bool):
                each_course_dict[str(each_key)+'__c'] = each_course.get(each_key, False)
            elif isinstance(each_course.get(each_key), int):
                each_course_dict[str(each_key)+'__c'] = each_course.get(each_key, 0)
            else:
                each_course_dict[str(each_key)+'__c'] = each_course.get(each_key, 'N/A')
        courses_list.append(each_course_dict)

    tables={}
    tables['CourseT24__c'] = courses_list
    tables['CourseWorkT24__c'] = course_work_list
    tables['StudentT24__c'] = students

    return tables

class AccessToSalesforce:

    def __init__(self, args):
        self.url = args.url
        self.username = args.username
        self.passwd = args.password
        self.id = args.client_id
        self.secret = args.client_secret
        self.token = args.token

        self.access_token = None
        self.instance_url = None

    def getAccessToken(self):

        if self.access_token is None or self.instance_url is None:
            params = {
                "grant_type": "password",
                "client_id": self.id, # Consumer Key
                "client_secret": self.secret, # Consumer Secret
                "username": self.username, # The email you use to login
                "password": self.passwd+self.token # Concat your password and your security token
            }
            r = requests.post("{}/{}".format(self.url, "services/oauth2/token"), params=params)
            self.access_token = r.json().get("access_token")
            self.instance_url = r.json().get("instance_url")
        else:
            pass

        return self.access_token, self.instance_url

class RESTfulWeb:
    def sf_api_call(self, action, parameters={}, method='get', data={}):
        """
        Helper function to make calls to Salesforce REST API.
        Parameters: action (the URL), URL params, method (get, post or patch), data for POST/PATCH.
        """
        headers = {
            'Content-type': 'application/json',
            'Accept-Encoding': 'gzip',
            'Authorization': 'Bearer %s' % access_token
        }
        if method == 'get':
            r = requests.request(method, instance_url+action, headers=headers, params=parameters, timeout=30)
        elif method == 'delete':
            r = requests.request(method, instance_url+action, headers=headers, params=parameters, timeout=30)
        elif method in ['post', 'patch']:
            r = requests.request(method, instance_url+action, headers=headers, json=data, params=parameters, timeout=10)
        else:
            # other methods not implemented in this example
            raise ValueError('Method should be get or post or patch.')
        logging.info('Debug: API %s call: %s' % (method, r.url) )
        if r.status_code < 300:
            if method == 'patch' or method == 'delete':
                return None
            else:
                return r.json()
        else:
            raise Exception('API error when calling %s : %s' % (r.url, r.content))

    def updateAnObject(self, _id, _data, _object="ClassT24__c"):
        return self.sf_api_call('/services/data/v40.0/sobjects/{}/{}'.format(_object, _id), data=_data, method='patch')

    def deleteAnObject(self, _id, _object="ClassT24__c"):
        return self.sf_api_call('/services/data/v40.0/sobjects/{}/{}'.format(_object, _id), method='delete')

    def postAnObject(self, _data, _object="ClassT24__c"):
        return self.sf_api_call('/services/data/v40.0/sobjects/{}'.format(_object), data=_data, method='post')

    def queryObjects(self,  _qeury, _object="ClassT24__c"):
        return self.sf_api_call('/services/data/v40.0/query', _qeury, method='get')

    def queryGenerate(self,  _fields="%s", _object="ClassT24__c", _rules=None, _order=None):
        target = "SELECT {} FROM {}".format(_fields, _object)
        if _rules is not None:
            target += " WHERE {}".format(_rules)

        return {'q':target}

    def updateAllData(self, allData):

        for tableType in allData:
            instanceList = allData[tableType]

            for instanceData in instanceList:

                if ( tableType == "CourseT24__c"):
                    courseId__c = instanceData['courseId__c']
                    q = self.queryGenerate(_fields="Id", _object="CourseT24__c", _rules="courseId__c = \'{}\'".format(courseId__c))
                    result = self.queryObjects(q, _object=tableType).get('records')
                    print(result)
                    if (len(result) != 0):
                        self.updateAnObject(result[0].get('Id'), instanceData, _object=tableType)
                    else:
                        self.postAnObject(instanceData, _object=tableType)
                elif ( tableType == "StudentT24__c"):
                    courseID__c = instanceData['courseId__c']
                    userId__c = instanceData['userId__c']
                    q = self.queryGenerate(_fields="Id", _object="StudentT24__c",
                                      _rules="courseId__c = \'{}\' AND userId__c = \'{}\'".format(courseID__c, userId__c))
                    result = self.queryObjects(q, _object=tableType).get('records')
                    if (len(result) != 0):
                        self.updateAnObject(result[0].get('Id'), instanceData, _object=tableType)
                    else:
                        self.postAnObject(instanceData, _object=tableType)
                elif ( tableType == "CourseWorkT24__c"):
                    courseId__c = instanceData['courseId__c']
                    userId__c = instanceData['userId__c']
                    courseworkId__c = instanceData['courseworkId__c']
                    q = self.queryGenerate(_fields="Id", _object="CourseWorkT24__c",
                                      _rules="courseId__c = \'{}\' AND userId__c = \'{}\' AND courseworkId__c = \'{}\'".format(courseId__c, userId__c, courseworkId__c))
                    result = self.queryObjects(q, _object=tableType).get('records')
                    if (len(result) != 0):
                        self.updateAnObject(result[0].get('Id'), instanceData, _object=tableType)
                    else:
                        self.postAnObject(instanceData, _object=tableType)

    def deleteAllDataOnCertainTable(self, _object):
        q = self.queryGenerate(_fields="Id", _object=_object)
        results = self.queryObjects(q, _object=_object)
        for record in results.get('records'):
            id = record.get('Id')
            self.deleteAnObject(id, _object=_object)

        return self.queryObjects(self.queryGenerate( _fields="Id", _object=_object), _object=_object)


if __name__ == "__main__":
    auth = AccessToSalesforce(args)
    access_token, instance_url = auth.getAccessToken()

    #logging.info("Access Token:", access_token)
    #logging.info("Instance URL", instance_url)

    restService = RESTfulWeb()
    isUpdateAll = True
    if isUpdateAll:
        allData = getDataFromGoogleClassRoom()

        readyAllData = {'CourseT24__c':[], 'StudentT24__c':[], 'CourseWorkT24__c':[]}

        course_fields = "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}".format(
            'alternateLink__c',
            'calendarId__c',
            'courseGroupEmail__c',
            'courseID__c',
            'courseName__c',
            'courseState__c',
            'creationTime__c',
            'descriptionHeading__c',
            'enrollmentCode__c',
            'guardiansEnabled__c',
            'ownerId__c',
            'room__c',
            'section__c',
            'teacherGroupEmail__c',
            'updateTime__c')
        results = restService.queryObjects(_qeury={'q':'SELECT {} from CourseT24__c'.format(course_fields)})
        records = results.get('records')

        isdel = False
        for newrecord in allData['CourseT24__c']:
            flag = True

            for record in records:
                if not isdel:
                    del record['attributes']
                comLen = len(record.items() & newrecord.items())
                if comLen == 15:
                    flag = False
            isdel = True
            if flag:
                readyAllData['CourseT24__c'].append(newrecord)

        student_fields = "{}, {}, {}, {}, {}, {}".format(
            'courseId__c',
            'familyName__c',
            'fullName__c',
            'givenName__c',
            'userId__c',
            'verifiedTeacher__c')
        isdel = False
        results = restService.queryObjects(_qeury={'q':'SELECT {} from StudentT24__c'.format(student_fields)})
        for newrecord in allData['StudentT24__c']:
            flag = True
            for record in results.get('records'):
                if not isdel:
                    del record['attributes']

                comLen = len(record.items() & newrecord.items())
                if comLen == 6:
                    flag = False
            isdel = True
            if flag:
                readyAllData['StudentT24__c'].append(newrecord)

        courseworks_fields = "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}".format(
            'alternateLink__c',
            'assignedGrade__c',
            'assigneeMode__c',
            'courseId__c',
            'courseworkId__c',
            'creationTime__c',
            'creatorUserId__c',
            'description__c',
            'dueDate__c',
            'dueTime__c',
            'late__c',
            'maxPoints__c',
            'publish_state__c',
            'state__c',
            'submissionModificationMode__c',
            'title__c',
            'topicId__c',
            'updateTime__c',
            'userId__c',
            'workType__c')
        isdel = False
        results = restService.queryObjects(_qeury={'q':'SELECT {} from CourseWorkT24__c'.format(courseworks_fields)})
        for newrecord in allData['CourseWorkT24__c']:
            flag = True

            for record in results.get('records'):
                if not isdel:
                    del record['attributes']
                comLen = len(record.items() & newrecord.items())
                if comLen == 20:
                    flag = False
                elif (comLen == 18 or comLen == 19) and (int(record['assignedGrade__c']) == int(newrecord['assignedGrade__c']) or
                                       int(record['maxPoints__c']) == int(newrecord['maxPoints__c'])):
                    flag = False
            isdel = True
            if flag:
                readyAllData['CourseWorkT24__c'].append(newrecord)

        for r in readyAllData['CourseWorkT24__c']:
            if r in results.get('records'):
                print(r)

        logging.info('Records are pending to be updated')
        logging.info('CourseT24__c:{}',format(len(readyAllData['CourseT24__c'])))
        logging.info('StudentT24__c:{}',format(len(readyAllData['StudentT24__c'])))
        logging.info('CourseWorkT24__c:{}',format(len(readyAllData['CourseWorkT24__c'])))

        restService.updateAllData(readyAllData)
    else:
        restService.deleteAllDataOnCertainTable('CourseT24__c')
        restService.deleteAllDataOnCertainTable('StudentT24__c')
        restService.deleteAllDataOnCertainTable('CourseWorkT24__c')
