import os

import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch import helpers

es_client = Elasticsearch()


def send_data(data):
    return helpers.bulk(es_client, index="recipes", actions=data)


def read_data_in_chunks(file_path, chunk_size):
    for chunked_df in pd.read_csv(file_path, iterator=True, chunksize=chunk_size):
        chunked_df = chunked_df.where(chunked_df.notnull(), None)
        yield chunked_df.to_dict(orient="records")


es_client.indices.create(index="recipes", ignore=400)
source_path = os.environ.get("DATA_SOURCE_PATH", None)
for chunk in read_data_in_chunks(source_path, 65000):
    send_data(chunk)
