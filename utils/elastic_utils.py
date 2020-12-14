import pprint
from typing import List

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Bool, Range

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

    def recipe_fuzzy_search_by_name(self, recipe_name) -> List[dict]:
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
        res = self._conn.search(index="recipes", body=search_query)["hits"]["hits"]
        found_recipes = [
            {
                "ingredients": recipe["_source"]["ingredients"],
                "minutes": recipe["_source"]["minutes"],
                "name": recipe["_source"]["name"],
                "nutrition": recipe["_source"]["nutrition"],
                "steps": recipe["_source"]["steps"],
            }
            for recipe in res
        ]
        return found_recipes

    def search_recipes(self, filter_query, skip=0, limit=2, scan=False, random_meal=False):
        q = Bool(must=filter_query)
        s = Search(index="recipes")
        s = s.using(self._conn)
        s = s.query(q)

        if scan:
            results = [item.to_dict() for item in s.scan()]
        elif random_meal:
            s = s.query(filter_query).query(
                {
                    "function_score": {
                        "query": {"match_all": {}},
                        "random_score": {},
                    }})
            s = s.extra(size=1)
            results = [item.to_dict() for item in s]

        else:
            s = s[skip:limit]
            results = [item.to_dict() for item in s]

        return results

    def get_daily_menu(self, daily_calories):
        daily_calories = [
            # breakfast calories range
            (daily_calories * 0.15, daily_calories * 0.2),
            # lunch calories range
            (daily_calories * 0.45, daily_calories * 0.5),
            # dinner calories range
            (daily_calories * 0.2, daily_calories * 0.3),
        ]

        menu = []
        for meal in daily_calories:
            menu.append(
                    self.search_recipes(
                        Range(**{"meal_nutrition": {'gte': meal[0], 'lte': meal[1]}}),
                        random_meal= True,
                    )[0]

            )

        return menu

    @staticmethod
    def get_total_calories(menu):
        total = 0
        for meal in menu:
            total += meal['meal_nutrition']

        return total

# Example

# el = ElasticClient()
# daily_menu = el.get_daily_menu(2000)
#
# pprint.pprint(daily_menu)
# print(el.get_total_calories(daily_menu))
