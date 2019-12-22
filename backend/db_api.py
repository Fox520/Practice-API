import re
import json
import psycopg2
import string
import random
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
        mid = self.cur.fetchone()[0]
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
            return (False, e.pgcode)
        return (True, "organisation added")
    
    def get_all_organisations(self) -> [(int, str)]:
        self.cur.execute("select * from organisation")
        rows = self.cur.fetchall()
        result = []
        for r in rows:
            # r -> (org_id, organisation_name)
            result.append(r)
        return result
    
    def add_seller(self, email_or_phone: str, pwd_hash: str, display_name: str, id_num: str, id_type: str, org_id: int = None, is_email=True) -> (bool, str):
        if None or "" in [email_or_phone, pwd_hash, display_name, id_num, id_type]:
            return (False, "fill in required fields")
        if is_email and not validate_email(email_or_phone): return False, "invalid email provided"
        try:
            info = json.dumps({"display_name":display_name, "identification_number": id_num, "identification_type": id_type})
            self.cur.execute("INSERT INTO seller(org_id, email_or_phone, password_hash, info) VALUES (%s,%s,%s,%s)", (org_id, email_or_phone,pwd_hash,info))
            self.con.commit()
        except psycopg2.Error as e:
            return (False, e.pgcode)
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
            return (False, e.pgcode)
        return (True, "Feedback submited")
    
    def get_product_feedbacks(self, product_id: int) -> [(int, int, str or None, str)]:
        self.cur.execute("select feedback_id from PRODUCT_FEEDBACK_JUNCTION_TABLE where product_id=%s", (product_id,))
        fids = self.cur.fetchall()
        result = []
        for f in fids:
            self.cur.execute("select * from feedback where feedback_id=%s", (f,))
            for out in self.cur.fetchone():
                result.append(out)
        return result
    
    def add_product(self, seller_id: int, affiliations_allowed: bool, info: dict, media_id: int = None) -> (bool, str, int or None):
        if None or "" in [seller_id, info]: return (False, "Please fill in required information.", None)
        try:
            self.cur.execute("INSERT INTO product(seller_id, media_id) VALUES (%s,%s) RETURNING product_id", (seller_id, media_id))
            pid = self.cur.fetchone()[0]
            # add product/relevant information here
            self.cur.execute("INSERT INTO product_information(product_id, affiliations_allowed, info) VALUES (%s,%s,%s) RETURNING product_info_id", (pid,affiliations_allowed,json.dumps(info)))
            # prod_info_id = self.cur.fetchone()[0]
            self.con.commit()
            return (True, "product added", pid)
        except psycopg2.Error as e:
            return (False, e.pgerror, e.pgcode)

    def get_product_information(self, product_id: int) -> [(int, int, dict, str)] or None:
        self.cur.execute("select * from product_information where product_id=%s", (product_id,))
        return self.cur.fetchone()
    
    def get_all_products(self) -> [(int, int, dict, str)] or None:
        return self.cur.execute("select * from product_information").fetchall()
    
    def get_all_products_from_category(self, category) -> [(int, int, dict, str)] or []:
        self.cur.execute("select * from product_information where info->>'category' =%s", (category,))
        rows = self.cur.fetchall()
        result = []
        for r in rows:
            result.append(r)
        return result
    
    def get_all_products_from_seller(self, seller_id):
        try:
            self.cur.execute("""
            SELECT
                p.product_id,
                m.info,
                pi.affiliations_allowed,
                pi.info
            FROM
                product_information pi
            INNER JOIN product p ON p.product_id = pi.product_id
            INNER JOIN media m ON m.product_id = pi.product_id
            WHERE
                p.seller_id=%s
            """, (seller_id,))
            rows = self.cur.fetchall()
            result = []
            for r in rows:
                result.append(r)
            return (True, result)
        except psycopg2.Error as e:
            return (False, e.pgcode)
    
    def get_category_listing(self) -> [str] or []:
        self.cur.execute("select distinct info->>'category' from product_information")
        rows = self.cur.fetchall()
        result = []
        for r in rows:
            result.append(r[0])
        return result
    
    def add_affiliator(self, email_or_phone, pwd_hash) -> (bool, str, int):
        try:
            self.cur.execute("INSERT INTO affiliator(email_or_phone, password_hash) VALUES (%s,%s) RETURNING affiliator_id;", (email_or_phone, pwd_hash))
            affiliator_id = self.cur.fetchone()[0]
            self.con.commit()
            return (True, "affiliator added", affiliator_id)
        except psycopg2.Error as e:
            return (False, e.pgerror, e.pgcode)
    
    def add_affiliation_code_to_product(self, affiliator_id, product_id) -> (bool, str, str):
        try:
            self.cur.execute("select affiliations_allowed from product_information where product_id=%s", (product_id,))
            is_allowed = self.cur.fetchone()[0]
            if not is_allowed: return (False, "Affiliations not allowed on this product")
            affiliation_code = generate_code()
            self.cur.execute("INSERT INTO PRODUCT_AFFILIATOR_JUNCTION_TABLE(affiliator_id, product_id, affiliation_code) VALUES (%s,%s,%s)", (affiliator_id, product_id, affiliation_code))
            self.con.commit()
            return (True, "success", affiliation_code)
        except psycopg2.Error as e:
            return (False, e.pgerror, e.pgcode)

    def get_products_with_affiliations_available(self):
        self.cur.execute("select * from product_information where affiliations_allowed=%s", (True,))
        rows = self.cur.fetchall()
        result = []
        for r in rows:
            result.append(r)
        return result
    
    def get_affiliator_products(self, affiliator_id: int) -> [(int, dict)] or []:
        self.cur.execute("""
        SELECT
            p.seller_id,
            jt.affiliation_code,
            pi.info
        FROM
            PRODUCT_AFFILIATOR_JUNCTION_TABLE jt
        INNER JOIN product_information pi ON pi.product_id = jt.product_id
        INNER JOIN product p ON p.product_id = jt.product_id
        WHERE
            jt.affiliator_id=%s
        """, (affiliator_id,))
        rows = self.cur.fetchall()
        result = []
        for r in rows:
            result.append(r)
        return result
    
    def get_number_of_affiliation_orders(self, affiliator_id: int ,affiliation_code: str) -> (bool, int or str):
        '''
        Finds the number of orders which use the specified affiliation code
        '''
        try:
            self.cur.execute("""
            SELECT
                COUNT(od.product_affiliator_pkey)
            FROM
                ORDER_DETAIL od
            INNER JOIN PRODUCT_AFFILIATOR_JUNCTION_TABLE jt ON jt.product_affiliator_pkey = od.product_affiliator_pkey
            WHERE
                jt.affiliator_id=%s AND jt.affiliation_code=%s
            """, (affiliator_id, affiliation_code))
            return (True, self.cur.fetchone()[0])
        except psycopg2.Error as e:
            return (False, e.pgcode)
    
    def get_affiliators_for_product(self, product_id: int) -> [(int, str)]:
        # should be used by seller
        try:
            self.cur.execute("select affiliator_id, affiliation_code from PRODUCT_AFFILIATOR_JUNCTION_TABLE where product_id=%s", (product_id,))
            rows = self.cur.fetchall()
            result = []
            for r in rows:
                result.append(r)
            return (True, "success", result)
        except psycopg2.Error as e:
            return (False, e.pgerror, e.pgcode)

    def add_order(self, product_id: int, shipping_address: dict, buyer_id: str, info: dict, affiliation_code: str = None, order_date: str = None) -> (bool, str, int):
        if None in [shipping_address]: return (False, "Provide a shipping address.")
        try:
            self.cur.execute("INSERT INTO orders(product_id, order_date, shipping_address) VALUES (%s,%s,%s) RETURNING order_id;",
                            (product_id, datetime.today().strftime("%Y-%m-%d") if order_date is None else order_date, json.dumps(shipping_address)))
            order_id = self.cur.fetchone()[0]
            # now add to the details table
            if affiliation_code is not None:
                affiliator_id = self._get_affiliator_id_from_code(product_id, affiliation_code)
                # check if code not exist, yes this logic is correct
                if affiliator_id in [None, -1]:
                    self.con.rollback()
                    return (False, "Invalid affiliation code", -1)
            else:
                affiliator_id = None

            self.cur.execute("INSERT INTO order_detail(order_id, buyer_id, affiliator_id, info) VALUES (%s,%s,%s,%s)",
                            (order_id, buyer_id, affiliator_id, json.dumps(info)))
            self.con.commit()
            return (True, "order created", order_id)
        except psycopg2.Error as e:
            msg = e.pgerror
            if e.pgcode == "23503":
                msg = "Buyer not found"
            return (False, msg, e.pgcode)
    
    def _get_affiliator_product_id_from_code(self,product_id: int ,affiliation_code: str) -> int or None:
        try:
            self.cur.execute("select product_affiliator_pkey from PRODUCT_AFFILIATOR_JUNCTION_TABLE where product_id=%s AND affiliation_code=%s", (product_id,affiliation_code))
            result = self.cur.fetchone()
            return None if result is None else result[0]
        except psycopg2.Error:
            return -1
    
    def add_buyer(self, buyer_id: str, info: dict) -> (bool, str):
        if None or "" in [buyer_id]:
            return (False, "No buyer id entered")
        try:
            self.cur.execute("INSERT INTO buyer(buyer_id, info) VALUES (%s,%s) RETURNING buyer_id", (buyer_id, json.dumps(info)))
            buyer_id = self.cur.fetchone()[0]
            self.con.commit()
            return (True, buyer_id)
        except psycopg2.Error as e:
            return (False, e.pgerror)


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

def generate_code(letters_size=3, number_size=3):
    return ''.join(random.choice(string.ascii_uppercase) for _ in range(letters_size)) + \
            ''.join(random.choice(string.digits) for _ in range(number_size))
