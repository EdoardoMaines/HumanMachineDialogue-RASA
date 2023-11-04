import sqlite3

def create_connection(db_file):

	conn = None
	try:
		conn = sqlite3.connect(db_file)
        
	except Error as e:
		print(e)
    
	return conn

def select_all_task(conn):

    cur = conn.cursor()
    cur.execute("SELECT * FROM toppings")

    rows = cur.fetchall()

    for row in rows:
        print(row)


def select_by_slot(conn, slot_name, slot_value):

    cur = conn.cursor()
    cur.execute(f"""SELECT password FROM login
				WHERE {slot_name}='{slot_value}'""")

    rows = cur.fetchall()
    if len(list(rows)) < 1:
        print("There are no resources matching your query!")
    else:
        for row in rows:
            print(f"Hello! {slot_value} has {row[0]} items")

#select_all_task(create_connection("pizzeria.db"))
select_by_slot(create_connection("../actions/pizzeria.db"), slot_name="id", slot_value="test_id")