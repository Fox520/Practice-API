from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields

# import resources
from endpoints.seller import SellerAPI, SellerAuthAPI

app = Flask(__name__, static_url_path="")
api = Api(app)

# api.add_resource(SellerAPI, '/api/seller/<str:action>')
api.add_resource(SellerAuthAPI, '/api/seller/<str:action>')



if __name__ == '__main__':
    app.run(debug=True)
