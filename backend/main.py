import json
import psycopg2

# connect to the db
con = psycopg2.connect(
    host = "localhost",
    database = "dreamer",
    user = "dreamer",
    password = "asdf"
)

v = {"verge": ["🐻", "car"]}

# cursor
cur = con.cursor()
cur.execute("INSERT INTO media(info) VALUES (%s)", (json.dumps(v),))
# execute query
# cur.execute("insert into media (info) values (%s)", json.dumps(v, ensure_ascii=False))
con.commit()
cur.execute("select * from media")
rows = cur.fetchall()

for r in rows:
    print(r[0], r[1])

# close cursor
cur.close()

# close the connection
con.close()