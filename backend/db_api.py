import re
import json
import psycopg2
import traceback
from urllib.parse import urlparse
from datetime import datetime

REGEX_EMAIL = "^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"

class DB_API(object):
    def __init__(self, host, database, user, password):
        self.con = psycopg2.connect(
                    host = host,
                    database = database,
                    user = user,
                    password = password
                )
        self.cur = self.con.cursor()
    
    def add_media(self, links:[str]) -> (bool, str):
        for u in links:
            if not validate_url(u): return (False, str(u)+" not a valid url")
        l = {"links": links}
        self.cur.execute("INSERT INTO media(info) VALUES (%s)", (json.dumps(l),))
        self.con.commit()
        return (True, "success added media")
    
    # TODO: fix logic
    def get_product_media(self, product_id:int) -> [str]:
        self.cur.execute("select media_id from product where product_id=%s", (product_id,))
        mid = self.cur.fetchone()
        self.cur.execute("select info from media where media_id=%s", (mid,))
        # [({'links': ['link1', 'link2']},)]
        rows = self.cur.fetchall()[0][0]
        # {'links': ['link1', 'link2']} <- dict
        return rows["links"]
    
    def add_organisation(self, org_name: str) -> (bool, str):
        try:
            self.cur.execute("INSERT INTO organisation(organisation_name) VALUES (%s)", (org_name,))
            self.con.commit()
        except psycopg2.Error as e:
            return (False, e.pgerror)
        return (True, "organisation added")
    
    def get_all_organisations(self) -> [(int, str)]:
        self.cur.execute("select * from organisation")
        rows = self.cur.fetchall()
        result = []
        for r in rows:
            # r -> (org_id, organisation_name)
            result.append(r)
        return result
    
    def add_seller(self, email: str, pwd_hash: str, display_name: str, id_num: str, id_type: str, org_id: int = None) -> (bool, str):
        if None or "" in [email, pwd_hash, display_name, id_num, id_type]:
            return (False, "fill in required fields")
        if not validate_email(email): return False, "invalid email provided"
        try:
            info = json.dumps({"display_name":display_name, "identification_number": id_num, "identification_type": id_type})
            self.cur.execute("INSERT INTO seller(org_id, email, password_hash, info) VALUES (%s,%s,%s,%s)", (org_id, email,pwd_hash,info))
            self.con.commit()
        except psycopg2.Error as e:
            return (False, e.pgerror)
        return (True, "seller added")
    
    def add_feedback(self, product_id: int, rating: int, review: str) -> (bool, str):
        if None or "" in [product_id, rating]: return (False, "Enter valid values")
        if rating < 1 or rating > 5: return (False, "Rating out of range")
        date_posted = datetime.today().strftime("%Y-%m-%d")
        try:
            self.cur.execute("INSERT INTO feedback(rating, review, date_posted) VALUES (%s,%s,%s) RETURNING feedback_id", (rating, review,date_posted))
            feedback_id = self.cur.fetchone()[0]
            self.cur.execute("INSERT INTO PRODUCT_FEEDBACK_JUNCTION_TABLE(product_id, feedback_id) VALUES (%s,%s)", (product_id, feedback_id))
            self.con.commit()
        except psycopg2.Error as e:
            return (False, e.pgerror)
        return (True, "feedback submited")
    
    def get_product_feedbacks(self, product_id: int) -> [(int, int, str or None, str)]:
        self.cur.execute("select feedback_id from PRODUCT_FEEDBACK_JUNCTION_TABLE where product_id=%s", (product_id,))
        fids = self.cur.fetchall()
        result = []
        for f in fids:
            self.cur.execute("select * from feedback where feedback_id=%s", (f,))
            for out in self.cur.fetchone():
                result.append(out)
        return result
    
    def add_product(self, seller_id: int, info, media_id: int = None) -> (bool, str, int or None):
        if None or "" in [seller_id, info]: return (False, "Please fill in required information.", None)
        pid = None
        try:
            self.cur.execute("INSERT INTO product(seller_id, media_id) VALUES (%s,%s) RETURNING product_id", (seller_id, media_id))
            pid = self.cur.fetchone()[0]
            # add product/relevant information here
            self.cur.execute("INSERT INTO product_information(product_id, info) VALUES (%s,%s) RETURNING product_info_id", (pid, json.dumps(info)))
            # prod_info_id = self.cur.fetchone()[0]
            self.con.commit()
        except psycopg2.Error as e:
            # print(traceback.format_exc())
            return (False, e.pgerror, None)
        return (True, "product added", pid)

    def get_product_information(self, product_id: int) -> [(int, int, dict, str)] or None:
        self.cur.execute("select * from product_information where product_id=%s", (product_id,))
        return self.cur.fetchone()
    
    def add_buyer(self, buyer_id: str, info: dict) -> (bool, str):
        if None or "" in [buyer_id]:
            return (False, "No buyer id entered")
        try:
            self.cur.execute("INSERT INTO buyer(buyer_id, info) VALUES (%s,%s)", (buyer_id, info))
            self.con.commit()
        except psycopg2.Error as e:
            return (False, e.pgerror)
        return (True, "buyer added")


    def close(self):
        self.cur.close() if self.cur is not None else None
        self.con.close() if self.con is not None else None


def validate_url(url: str) -> bool:
  try:
    result = urlparse(url)
    return all([result.scheme, result.netloc])
  except ValueError:
    return False

def validate_email(email: str) -> bool:
    return re.search(REGEX_EMAIL,email)
