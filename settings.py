ELASTIC_HOST = "localhost"
ELASTIC_PORT = 9200

mappers = {
    "recipes": {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1
        },
        "mappings": {
            "recipe": {
                "properties": {
                    "name": {"type": "text"},
                    "id": {"type": "integer"},
                    "minutes": {"type": "integer"},
                    "contributor_id": {"type": "integer"},
                    "submitted": {"type": "date"},
                    "tags": {"type": "text"},
                    "nutrition": {"type": "text"},
                    "meal_nutrition": {"type": "float"},
                    "n_steps": {"type": "integer"},
                    "steps": {"type": "text"},
                    "description": {"type": "text"},
                    "ingredients": {"type": "text"},
                    "n_ingredients": {"type": "integer"},
                }
            }
        }
    }
}
