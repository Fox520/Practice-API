from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields

# import resources
from endpoints.seller import SellerAPI, SellerAuthAPI

app = Flask(__name__, static_url_path="")
api = Api(app)

api.add_resource(SellerAPI, '/api/tasks', endpoint='tasks')
api.add_resource(SellerAuthAPI, '/api/tasks/<int:id>', endpoint='task')


if __name__ == '__main__':
    app.run(debug=True)
