import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="indoor_db",
    user="baps",
    password="1234"
)

print("Connected")