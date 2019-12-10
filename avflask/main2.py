import requests

# url = 'http://127.0.0.1:5000/reviews'
#
# data = {
#     "data": {
#         "type": "review",
#         "attributes": {
#             "text": "I read this book",
#         }
#     }
# }
#
# resp = requests.post(url, json=data)
#
# print(resp.json())


url = "http://127.0.0.1:5000/books"

data = {
    "data": {
        "type": "book",
        "attributes": {
            "name": "This Is A Book",
            "author": "AN Author",
            "isbn": "ISBNISBNISBN",
            "publish_date": "1990-12-18"
        },
        "relationships": {
            "reviews": {
                "data": [
                    {
                        "type": "review",
                        "id": "1"
                    }
                ]
            }
        }
    }
}

resp = requests.post(url, json=data)

print(resp.json())