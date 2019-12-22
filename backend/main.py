#TODO: - use mobile phone to create account
#       - referral link AAA000
import json
from db_api import DB_API

db = DB_API("localhost", "dreamer", "dreamer", "asdf")

# print(db.add_media(["http://link1.com", "http://link2.com/hello.png"]))


# retrieve links for a product
# result = db.get_product_media(12)
# print(result)

# add organisation
# res = db.add_organisation("choppies")
# print(res)

# retrieve all organisations
# res = db.get_all_organisations()
# print(res)
# add seller
res = db.add_seller("me@mail.com", "hassssh", "Johnny", "12345", "personal id")
print(res)

# res = db.add_feedback(0, 3, "akshd")
# print(res)

# res = db.add_product(4,{"dimensions": "80x30"},1)
# print(res)

# res = db.get_product_information(8)
# print(res)

db.close()