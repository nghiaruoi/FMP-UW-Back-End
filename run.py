from flask import Flask, json, jsonify, request
from flask_restful import abort, Api, Resource
import requests
from config import Config
import base64

app = Flask(__name__)
api = Api(app)

GRAPHQL_ENDPOINT = "https://www.ratemyprofessors.com/graphql"


def getProfName(department, course_number, section, term):
    url = f'https://ws.admin.washington.edu/student/v5/course/2024,{term},{department},{course_number}/{section}'
    headers = {'Authorization': 'Bearer 7F3A58DB-4847-44B9-85B3-E73CE883E974'}

    # Make the API call
    response = requests.get(url, headers=headers)

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract relevant information
    course_title = soup.find('span', {'class': 'CourseTitle'}).text.strip()
    instructor_name_element = soup.find('ul', {'class': 'Instructors'})

    if instructor_name_element:
        instructor_name = instructor_name_element.find('span', {'class': 'name'}).text.strip()
        result = {
            'course_title': course_title,
            'instructor_info': instructor_name
        }
    else:
        result = {'course_title': course_title, 'instructor_info': "Instructor information is unavailable."}

    return result


@app.route('/process', methods=['POST'])
def process():
    class_info = courseSplitter(request.form['class'])
    section = request.form['section']
    term = request.form['term']

    # Validate class_info and section or add additional error checking if needed
    if len(class_info) != 2 or not section:
        error_message = "Please enter a valid class in the format 'DEPARTMENT,COURSE_NUMBER' and provide a section."
        return render_template('index.html', error_message=error_message)

    department, course_number = class_info
    result = getProfName(department, course_number, section, term)
    return render_template('result.html', result=result)

def courseSplitter(nameOfClass):
    #Check this - does strip return a value or not?
    nameOfClass = nameOfClass.strip()
    if (nameOfClass.find(",") != -1):
        return nameOfClass.split(",")
    else:
        pos = -1
        for i in nameOfClass:
            pos+=1

            try:
                i = int(i)
            except Exception as e:
                continue
            else:
                break
        return [nameOfClass[0:pos].strip(), nameOfClass[pos:].strip()]

def extract_first_last_names(full_name):
    if full_name.find(":") != -1:
        #convert to a name
        full_name = full_name[full_name.index(":")+1:]

    # Split the full name by spaces and extract the first and last names
    names = full_name.split()
    if len(names) >= 2:
        first_name = names[0]
        last_name = names[-1]
    else:
        # If there are not enough parts, use the full name
        first_name = full_name
        last_name = full_name
    return first_name, last_name

@app.route('/rate_my_professor/<professor_info>')
def rate_my_professor(professor_info):
    # Extract first and last names
    first_name, last_name = extract_first_last_names(professor_info)

    # Open a new tab searching for the first and last names on Rate My Professor
    search_url = f'https://www.ratemyprofessors.com/search/professors?q={first_name}%20{last_name}'
    print(search_url)
    return redirect(search_url)


class Professor(Resource):
    def get(self):
        professor_name = request.args.get("professor")
        school_id = request.args.get("school")

        query = """
        query NewSearchTeachersQuery($text: String!, $schoolID: ID!) {
              newSearch {
                teachers(query: {text: $text, schoolID: $schoolID}) {
                  edges {
                    cursor
                    node {
                      id
                      firstName
                      lastName
                      school {
                        name
                        id
                      }
                    }
                  }
                }
              }
            }
        """
        variables = {"text": professor_name, "schoolID": school_id}

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic %s" % Config.AUTH_TOKEN,
        }

        response = requests.post(
            url=GRAPHQL_ENDPOINT,
            json={"query": query, "variables": variables},
            headers=headers,
        )

        return json.dumps(response)


class ProfessorByID(Resource):
    def get(self, id):
        professor_id = id
        query = """
       query RatingsListQuery($id: ID!) {node(id: $id) {... on Teacher {school {id} courseCodes {courseName courseCount} firstName lastName numRatings avgDifficulty avgRating department wouldTakeAgainPercent}}}


        """
        professor_query = base64.b64encode(("Teacher-%s" % professor_id)
                                                              .encode('ascii')).decode('ascii')
        variables = {"id": professor_query}
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic %s" % Config.AUTH_TOKEN,
        }

        response = requests.post(
            url=GRAPHQL_ENDPOINT,
            json={"query": query, "variables": variables},
            headers=headers,
        )
        
        professor_data = json.loads(response.text)["data"]["node"]
        courses_data = professor_data["courseCodes"]

        return courses_data
        

# api.add_resource(Professor, "/professor")
api.add_resource(ProfessorByID, "/professor/<id>")


if __name__ == "__main__":
    app.run(debug=True)
