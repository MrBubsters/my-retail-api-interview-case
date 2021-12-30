import pandas as pd
import numpy as np
import boto3
from decimal import Decimal
import json

df = pd.read_csv('movies_metadata.csv')



df['currency'] = 'USD'

mean_vote = df['vote_average'].mean()

df['price'] = (df['vote_average'] - df['vote_average'].mean()) + 14
df['price'] = (round(df['price'] * 2) / 2) - .01

movies_json = df.to_dict(orient='records')

movies_json = [{k: v for k, v in row.items() if not pd.isnull(v)} for row in movies_json]
# print(movies_json)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

for movie in movies_json:
    item = json.loads(json.dumps(movie), parse_float=str)
    print(item)

    table = dynamodb.Table('productTableDev')
    table.put_item(
        Item=item
    )