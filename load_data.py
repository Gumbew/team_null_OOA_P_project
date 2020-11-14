import os
import uuid

import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch import helpers

import settings

es_client = Elasticsearch()
index_name = "recipes"
doc_type = "recipe"

es_client.indices.create(index=index_name, ignore=400, body=settings.mappers[index_name])
source_path = os.environ.get("DATA_SOURCE_PATH", None)

actions = [
    {
        "_id": uuid.uuid4(),  # random UUID for _id
        "_type": doc_type,  # document _type
        "_source": row.where(row.notnull(), None).to_dict()
    }
    for _, row in pd.read_csv(source_path).iterrows()
]

try:
    # make the bulk call using 'actions' and get a response
    response = helpers.bulk(es_client, actions, index=index_name, doc_type=doc_type)
    print("\nactions RESPONSE:", response)
except Exception as e:
    print("\nERROR:", e)
