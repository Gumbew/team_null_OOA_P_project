import pprint
from typing import List

from elasticsearch import Elasticsearch

import settings


class ElasticClient(object):
    _conn = None

    def __new__(cls):
        if not cls._conn:
            cls._conn = cls.connect()
        instance = super(ElasticClient, cls).__new__(cls)
        return instance

    @staticmethod
    def connect():
        return Elasticsearch([{'host': settings.ELASTIC_HOST, 'port': settings.ELASTIC_PORT}])

    def disconnect(self):
        self._conn.close()

    def recipe_search(self, recipe_name) -> List[dict]:
        search_query = {
            'query': {
                "fuzzy": {
                    "name": {
                        "value": recipe_name,
                        "boost": 1.0,
                        "fuzziness": 2,
                        "prefix_length": 0,
                        "max_expansions": 100
                    }
                }
            }
        }
        res = self._conn.search(index="recipes", body=search_query)
        return res


el = ElasticClient()

pprint.pprint(el.recipe_search("carrot"))
