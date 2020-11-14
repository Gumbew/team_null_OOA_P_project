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
