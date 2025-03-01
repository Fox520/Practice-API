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
    
    def add_media(self, product_id: int, links:[str]) -> (bool, str):
        try:
            for u in links:
                if not validate_url(u): return (False, str(u)+" not a valid url")
            l = {"links": links}
            self.cur.execute("INSERT INTO media(int, info) VALUES (%s,%s)", (product_id, json.dumps(l)))
            self.con.commit()
            return (True, "success added media")
        except psycopg2.Error as e:
            return (False, e.pgerror, e.pgcode)
    
    def get_product_media(self, product_id:int) -> [str]:
        self.cur.execute("select info from media where product_id=%s", (product_id,))
        # [({'links': ['link1', 'link2']},)]
        rows = self.cur.fetchall()[0][0]
        # {'links': ['link1', 'link2']} <- dict
        return rows["links"]
    
    def add_organisation(self, org_name: str, info: dict) -> (bool, str):
        try:
            self.cur.execute("INSERT INTO organisation(organisation_name, info) VALUES (%s) RETURNING org_id", (org_name,json.dumps(info)))
            org_id = self.cur.fetchone()[0]
            self.con.commit()
            return (True, org_id)
        except psycopg2.Error as e:
            return (False, e.pgcode)
    
    def get_all_organisations(self) -> [(int, str, dict)]:
        self.cur.execute("select * from organisation")
        rows = self.cur.fetchall()
        result = []
        for r in rows:
            result.append(r)
        return result
    
    def add_seller(self, email_or_phone: str, pwd_hash: str, display_name: str, id_num: str, id_type: str, org_id: int = None, is_email=True) -> (bool, str or int):
        if None or "" in [email_or_phone, pwd_hash, display_name, id_num, id_type]:
            return (False, "Fill in required fields")
        if is_email and not validate_email(email_or_phone): return False, "invalid email provided"
        try:
            info = json.dumps({"display_name":display_name, "identification_number": id_num, "identification_type": id_type})
            self.cur.execute("INSERT INTO seller(org_id, email_or_phone, password_hash, info) VALUES (%s,%s,%s,%s) RETURNING seller_id", (org_id, email_or_phone,pwd_hash,info))
            seller_id = self.cur.fetchone()[0]
            self.con.commit()
            return (True, seller_id)
        except psycopg2.Error as e:
            return (None, e.pgcode)
        return (True, "seller added")
    
    def login_seller(self, email_or_phone, pwd_hash) -> (int, int or None, str, str, dict) or None or (bool, str, str):
        try:
            self.cur.execute("select seller_id, org_id, email_or_phone, info from seller where email_or_phone=%s and password_hash=%s", (email_or_phone, pwd_hash))
            result = self.cur.fetchone()
            return result
        except psycopg2.Error as e:
            return (False, e.pgerror, e.pgcode)
    
    def does_seller_exist(self, seller_id: int) -> bool:
        try:
            self.cur.execute("select exists(select seller_id from seller where seller_id=%s)", (seller_id,))
            result = self.cur.fetchone()[0]
            return result
        except psycopg2.Error as e:
            print(e.pgerror, e.pgcode)
            return False
    
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
    
    # not tested
    def get_all_products_from_seller(self, seller_id: int) -> (bool, [(int,dict,bool,dict)]):
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

    def add_coupon(self, product_id: int, coupon_code: str, percent_reduction: float) -> (bool, str, int or str):
        if coupon_code in [None, ""]: return (False, "Coupon code cannot empty.")
        if percent_reduction > 1 or percent_reduction < 0.01: return (False, "Invalid percentage")
        try:
            self.cur.execute("INSERT INTO coupon(product_id, coupon_code, percent_reduction) VALUES (%s,%s,%s) RETURNING coupon_id", (product_id, coupon_code, percent_reduction))
            coupon_id = self.cur.fetchone()[0]
            self.con.commit()
            return (True, "success", coupon_id)
        except psycopg2.Error as e:
            return (False, e.pgerror, e.pgcode)
    
    def add_question(self, product_id: int, question: str, answer: str, date_posted:str = datetime.today().strftime("%Y-%m-%d")):
        if question in [None, ""]: return (False, "Question cannot be empty.")
        if date_posted in [None, ""]: return (False, "Date code cannot be empty.")
        try:
            self.cur.execute("INSERT INTO CustomerQuestionsAndAnswers(product_id, question, date_posted) VALUES (%s,%s,%s) RETURNING qna_id", (product_id, question, date_posted))
            qna_id = self.cur.fetchone()[0]
            self.con.commit()
            return (True, "question successfully posted", qna_id)
        except psycopg2.Error as e:
            return (False, e.pgerror, e.pgcode)
    
    def set_answer_to_question(self, qna_id: int, answer: str) -> (bool, str):
        if answer in [None, ""]: return (False, "Answer cannot be empty.")
        try:
            self.cur.execute("UPDATE CustomerQuestionsAndAnswers SET answer = %s WHERE qna_id=%s", (answer, qna_id))
            self.con.commit()
            return (True, "question successfully posted")
        except psycopg2.Error as e:
            return (False, e.pgerror)

    def add_to_cart(self, buyer_id: str, product_id: str, quantity: int) -> (bool, str, int or str):
        if buyer_id in [None, ""]: return (False, "Buyer id cannot be empty.")
        if product_id in [None, ""]: return (False, "Product id cannot be empty.")
        if quantity < 1: return (False, "Quantity too low")
        # if not get_quantity(product_id) >= quantity: <- prevent buying more than available
        try:
            self.cur.execute("INSERT INTO cart(product_id, buyer_id, quantity) VALUES (%s,%s,%s) RETURNING cart_buyer_pkey", (product_id, buyer_id, quantity))
            cart_buyer_id = self.cur.fetchone()[0]
            self.con.commit()
            return (True, "product placed in cart", cart_buyer_id)
        except psycopg2.Error as e:
            return (False, e.pgerror, e.pgcode)
    
    def remove_product_from_cart(self, buyer_id, product_id) -> (bool, str):
        if buyer_id in [None, ""]: return (False, "buyer_id cannot be empty.")
        if product_id in [None, ""]: return (False, "product_id cannot be empty.")
        try:
            self.cur.execute("DELETE FROM cart WHERE buyer_id=%s AND product_id=%s", (buyer_id, product_id))
            self.con.commit()
            return (True, "Item removed from cart")
        except psycopg2.Error as e:
            return (False, e.pgcode)
    
    def destroy_cart(self, buyer_id):
        if buyer_id in [None, ""]: return (False, "id cannot be empty.")
        try:
            self.cur.execute("DELETE FROM cart WHERE buyer_id=%s", (buyer_id,))
            self.con.commit()
            return (True, "cart destroyed")
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
    
    def add_buyer(self, buyer_id: str, info: dict, email: str=None) -> (bool, str):
        if None or "" in [buyer_id]:
            return (False, "No buyer id entered")
        try:
            self.cur.execute("INSERT INTO buyer(buyer_id, email, info) VALUES (%s,%s,%s) RETURNING buyer_id", (buyer_id, email, json.dumps(info)))
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
