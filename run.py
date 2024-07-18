from flask import Flask, jsonify, request
import json
from flask_restful import reqparse, abort, Api, Resource
import requests
from requests.auth import HTTPBasicAuth
from config import Config
import json

app = Flask(__name__)
api = Api(app)

GRAPHQL_ENDPOINT = "https://www.ratemyprofessors.com/graphql"


class Professor(Resource):
    def get(self):
        professor_name = request.args.get("professor")
        school_id = request.args.get("school")

        url = "https://www.ratemyprofessors.com/graphql"

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
            "Authorization": "Basic %s"%Config.AUTH_TOKEN,
        }

        response = requests.post(
            url=GRAPHQL_ENDPOINT,
            json={"query": query, "variables": variables},
            headers=headers,
        )

        return response.text


api.add_resource(Professor, "/professor")

if __name__ == "__main__":
    app.run(debug=True)
