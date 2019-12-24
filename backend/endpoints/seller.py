from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields

app = Flask(__name__, static_url_path="")
api = Api(app)

class SellerAuthAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('email_or_phone', type=str, location='json')
        self.reqparse.add_argument('password_hash', type=str, location='json')
        super(SellerAuthAPI, self).__init__()
    
    def post(self):
        return ""

class SellerAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, location='json')
        self.reqparse.add_argument('description', type=str, location='json')
        self.reqparse.add_argument('done', type=bool, location='json')
        super(SellerAPI, self).__init__()

    # Return everything about seller
    def get(self, id):
        return ""

    def put(self, id):
        return ""

    def delete(self, id):
        return ""


if __name__ == '__main__':
    app.run(debug=True)
