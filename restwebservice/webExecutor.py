import cherrypy
import logging
import pickle
import os.path
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/classroom.coursework.students.readonly', 'https://www.googleapis.com/auth/classroom.rosters.readonly', 'https://www.googleapis.com/auth/classroom.courses.readonly']

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


class MyWebService(object):

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def process(self):
        data = self.getDataFromGoogleClassRoom()
        return json.dumps(data)

    def getDataFromGoogleClassRoom(self):
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


if __name__ == '__main__':
    config = {'server.socket_host': '0.0.0.0'}
    cherrypy.config.update(config)
    cherrypy.quickstart(MyWebService())