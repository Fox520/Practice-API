import os
import json
from ..db_api import DB_API
from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields

app = Flask(__name__, static_url_path="")
api = Api(app)

class SellerAuthAPI(Resource):
    def __init__(self):
        # self.db = DB_API(os.environ["ECO_HOST"], os.environ["ECO_DATABASE"], os.environ["ECO_USER"], os.environ["ECO_PWD"])
        self.db = DB_API("localhost", "dreamer", "dreamer", "asdf")
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('email_or_phone', type=str, location='json')
        self.reqparse.add_argument('password_hash', type=str, location='json')
        self.reqparse.add_argument('display_name', type=str, location='json')
        self.reqparse.add_argument('identifier_number', type=str, location='json')
        self.reqparse.add_argument('identifier_type', type=str, location='json')
        self.reqparse.add_argument('organisation_id', type=int, location='json')
        self.reqparse.add_argument('is_email', type=bool, location='json')
        super(SellerAuthAPI, self).__init__()
    
    def post(self, action):
        args = self.reqparse.parse_args()
        if action == "login":
            return jsonify(self.login(args["email_or_phone"], args["password_hash"]))
        if action == "create-account":
            return jsonify(self.create_account(args["email_or_phone"], args["password_hash"], args["display_name"], args["identifier_number"], args["identifier_type"], args["organisation_id"], args["is_email"]))
        if action == "valid-seller":
            # check if the seller is in the database
            return jsonify(self.does_seller_exist(args["seller_id"]))

        # default
        return "Unknown action"
    
    def login(self, email_or_phone, pwd_hash) -> dict:
        response = self.db.login_seller(email_or_phone, pwd_hash)
        if response is None:
            return {"result":False, "reason":"User not registered"}
        if response[0] == False:
            # we don't want to show the user that nasty error so be vague
            return {"result":False, "reason": "an error occured"}
        template = {
            "seller_id": response[0],
            "organisation_id": response[1],
            "email_or_phone": response[2],
            "info": response[3]
        }
        return {"result": True, {"output":template}}
    
    def create_account(self, email_or_phone: str, pwd_hash: str, display_name: str, id_num: str, id_type: str, org_id: int = None, is_email=True) -> dict:
        response = self.db.add_seller(email_or_phone, pwd_hash, display_name, id_num, id_type, org_id, is_email)
        if response[0] is None:
            # we don't want to show the user that nasty error so be vague
            return {"result":False, "reason":"An error occured while creating your account. Please try again."}
        if response[0] == False:
            return {"result":False, "reason": response[1]}
        return {"result": True, "seller_id":response[1]}
    
    def does_seller_exist(self, seller_id):
        return self.db.does_seller_exist(seller_id)


# Not sure yet what this resource should be for; therefore commenting out for now
class SellerAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('seller_id', type=int, location='json')
        self.reqparse.add_argument('org_id', type=int, location='json')
        self.reqparse.add_argument('email_or_phone', type=str, location='json')
        self.reqparse.add_argument('info', type=dict, location='json')
        self.reqparse.add_argument('organisation_name', type=dict, location='json')
        super(SellerAPI, self).__init__()

    def get(self, action):
        # returns tuples within a list [(organisation_id, organisation_name, info)] <- info is dictionary/map
        if action == "get_organisations":
            return jsonify(self.get_all_organisations())
        return "void"

    def post(self, action):
        if action == "create-organisation":
            return jsonify(self.create_organisation(args["organisation_name"], args["info"]))

        return "void"
    
    def create_organisation(self, seller_id, org_name, info):
        if not self.db.does_seller_exist(seller_id):
            return {"result": False, "reason": "Unknown account trying to add"}
        response = self.db.add_organisation(org_name, info)
        if response[0] == False:
            return {"result": False, "reason": "An error occured"}
        return {"result": True, "organisation_id":response[1]}

    def get_all_organisations(self):
        return self.db.get_all_organisations()

if __name__ == '__main__':
    app.run(debug=True)
