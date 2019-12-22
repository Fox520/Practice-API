#TODO: - referral link AAA000
import json
from db_api import DB_API
from db_api import generate_code

db = DB_API("localhost", "dreamer", "dreamer", "asdf")

# retrieve links for a product
# result = db.get_product_media(12)
# print(result)
# print(db.add_media(["http://link1.com", "http://abc.com/a.png"]))

# add organisation
# db.add_organisation("game")
# db.add_organisation("checkers")
# db.add_organisation("toyota")
# # print(res)

# # retrieve all organisations
# # res = db.get_all_organisations()
# # print(res)
# # add seller
# print(db.add_seller("me@mail.com", "hassssh", "Johnny", "12345", "national_id", is_email=True))
# print(res)

# res = db.add_feedback(0, 3, "akshd")
# print(res)

# print(db.add_product(1, True, {"dimensions": "80x30", "category": "clothing"},1))
# print(db.add_product(1, True, {"weight": "10kg", "category":"tech"},2))
# print(db.add_product(1, False, {"color": "green", "category":"shoes"},1))

# print(res)

# res = db.get_product_information(8)
# print(res)

print(db.add_affiliator("2648123456", "serccure"))

# print(db.get_category_listing())
# print(db.get_all_products_from_category("clothing"))

# print(db.get_products_with_affiliations_available())
# print(db.add_affiliation_code_to_product(1, 8))
# print(db.get_affiliator_products(1))

# print(db.add_buyer("abcd", {"dislay_name":"Toto"}))

# print(db._get_affiliator_id_from_code(8, "EVD539"))

# print(db.add_order(product_id=8, shipping_address={"address 1": "driveway"},
#         buyer_id="abcd", info={"free_shipping":True}, affiliation_code="EVD539"))

print(db.get_number_of_affiliation_orders(1, "EVD539"))

db.close()