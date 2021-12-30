import decimal
import os

from boto3.dynamodb.conditions import Key
from flask import Flask, jsonify, make_response, request
import boto3
import json
import traceback

app = Flask(__name__)

product_table = os.environ.get('PRODUCT_TABLE')
deployment_region = os.environ.get('DEPLOYMENT_REGION')


@app.route("/")
def hello_from_root():
    return jsonify(message='Hello from root!')


@app.route("/products")
def get_products():
    """
    API GET endpoint for all products. No required parameters.
    :return: json of all products in table
    """
    # initialize connection with dynamodb table
    dynamodb = boto3.resource('dynamodb', region_name=deployment_region)
    table = dynamodb.Table(product_table)

    try:
        # scan table for values
        resp = table.scan()
        # pull items out as pandas dataframe
        items = resp['Items']

        while 'LastEvaluatedKey' in resp.keys():
            print('requesting more values')
            resp = table.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
            items.append(resp['Items'])
        # print(items)
        # fetch from dynamo db based on product id
        ret_json = items.to_json(orient='records')
    except Exception:
        ret_json = json.dumps({
            "message": "Internal Error",
            "error": traceback.format_exc()
        })
    return jsonify(ret_json)


@app.route("/products/<string:product_id>")
def get_product_from_id(product_id):
    """
    API GET endpoint for products that accepts one param for the product id
     and returns formatted json of data

    :param product_id: String id of the product id found in table
    :return: json body of data for product
    """
    # initialize connection with dynamodb table
    dynamodb = boto3.resource('dynamodb', region_name=deployment_region)
    table = dynamodb.Table(product_table)

    # query table for a matching product id
    resp = table.query(
        KeyConditionExpression=Key('id').eq(product_id)
    )
    # fetch from dynamo db based on product id
    items = resp['Items'][0]

    # form data into response format
    ret = {
        'id': items['id'],
        'name': items['original_title'],
        'current_price': {
            'value': items['price'],
            'currency_code': items['currency']
        }
    }

    return jsonify(ret)


@app.route("/products/<string:product_id>", methods=['PUT'])
def put_product_from_id(product_id):
    """
    API PUT request for products that accepts one param the id of the product
    and a body with "newPrice" as a key with the value being the updated price

    :param product_id: String id of the product id found in table
    :return: json body response from table upon update
    """
    body = request.get_json()

    # initialize connection with dynamodb table
    dynamodb = boto3.resource('dynamodb', region_name=deployment_region)
    table = dynamodb.Table(product_table)

    # send an update request to the table to update price
    response = table.update_item(
        Key={'id': product_id},
        UpdateExpression='set price=:p',
        ExpressionAttributeValues={':p': body['newPrice']},
        ReturnValues="UPDATED_NEW"
    )

    print(response)
    return jsonify(response)


@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)
