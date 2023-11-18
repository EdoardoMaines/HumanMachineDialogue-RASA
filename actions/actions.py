# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import sqlite3

from typing import Text, List, Any, Dict

from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.events import EventType
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, FollowupAction



ALLOWED_PIZZA_SIZES = [
	"baby",
	"medium",
	"large",
	"m",
	"l"
]

ALLOWED_PIZZA_TYPES = [
	"margherita",
	"marinara",
	"salami",
	"veggie"
]

ALLOWED_DRIKS = [
	"coke",
	"still water",
	"sparkling water",
	"fanta",
	"lemon iced tea",
	"peach iced tea"
]

PIZZA_INGREDIENTS = {
	"margherita": ["pizza dough", "tomato sauce", "mozzarella"],
    "marinara": ["pizza dough", "tomato sauce"],
	"salami": ["pizza dough", "tomato sauce", "mozzarella", "salami"],
	"veggie": ["pizza dough", "tomato sauce", "vegetables"]
}

ALLOWED_PIZZA_TOPPINGS = [
	"mozzarella",
	"mushrooms",
	"ham",
	"salami",
	"spicy salami",
	"olives",
	"vegetables",
	"grilled vegetables"
]

MENU = {
	"margherita": 6,
	"marinara": 5.5,
	"salami": 7,
	"veggie": 8.5,
	"coke": 2,
	"still water": 1.5,
	"sparkling water": 1.5,
	"fanta": 2,
	"lemon iced tea": 2,
	"peach iced tea": 2
}

def create_connection(db_file):

	conn = None
	try:
		conn = sqlite3.connect(db_file)
	except Error as e:
		print(e)

	return conn

def select_by_slot(conn, table, slot_name, slot_value):

    cur = conn.cursor()
    cur.execute(f"""SELECT quantity FROM {table}
				WHERE {slot_name}='{slot_value}'""")
	
    print(f"""SELECT quantity FROM {table}
				WHERE {slot_name}='{slot_value}'""")
	
    rows = cur.fetchall()

    if len(list(rows)) < 1:
        print("There are no resources matching your query!")
    
    for row in rows:
        return[row[0]]
		

def select_by_id(conn, slot_name, slot_value):

    cur = conn.cursor()
    cur.execute(f"""SELECT * FROM login
				WHERE {slot_name}='{slot_value}'""")

    rows = cur.fetchall()
    if len(list(rows)) < 1:
        print("There are no resources matching your query!")

    for row in rows: 
    	return[row]

def update_by_slot(conn, table, slot_name, slot_value, action, q):

    cur = conn.cursor()

    get_query_result = select_by_slot(conn, table, slot_name, slot_value)
    print("RESULT: ", get_query_result)
    if action == "SUB":
        new_quantity = (get_query_result[0])-q
    if action == "SUM":
        new_quantity = (get_query_result[0])+q

    cur.execute(f"""UPDATE {table}
				SET quantity='{new_quantity}'
				WHERE {slot_name}='{slot_value}'""")
    conn.commit()

    return[]

class ValidateSimplePizzaForm(FormValidationAction):
	def name(self) -> Text:
		return "validate_simple_pizza_form"
	
	def validate_pizza_type(
		self,
		slot_value: Any,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: DomainDict,
	) -> Dict[Text, Any]:

		conn = create_connection("pizzeria.db")


		if slot_value.lower() not in ALLOWED_PIZZA_TYPES:
			dispatcher.utter_message(text=f"I don't recognize that pizza. We serve {'/'.join(ALLOWED_PIZZA_TYPES)}.")
			return {"pizza_type": None}

		print(slot_value)
		#dispatcher.utter_message(text=f"OK! You want to have a {slot_value}.")
		ingredients = PIZZA_INGREDIENTS[slot_value]
		print("INGREDIENTI: ", ingredients)
		for i in ingredients[1:]:
			print(i)
			if i in ALLOWED_PIZZA_TOPPINGS:
				update_by_slot(conn=conn, table="toppings", slot_name="pizza_toppings", slot_value=i, action="SUB", q=1)
			else:
				update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value=i, action="SUB", q=1)
		
		return {"pizza_type": slot_value}
		
	def validate_pizza_size(
		self,
		slot_value: Any,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: DomainDict,
	) -> Dict[Text, Any]:
	  
		conn = create_connection("pizzeria.db")

		if slot_value.lower() not in ALLOWED_PIZZA_SIZES:
			dispatcher.utter_message(text=f"We only accept pizza sizes: baby/medium(m)/large(l).")
			return {"pizza_size": None}
		if slot_value == "baby":
			update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value="pizza dough", action="SUB", q=0.5)
		if slot_value == "medium" or slot_value == "m":
			update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value="pizza dough", action="SUB", q=1)
		if slot_value == "large" or slot_value == "l":
			update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value="pizza dough", action="SUB", q=2)
		type = tracker.get_slot("pizza_type")
		topping = tracker.get_slot("pizza_topping")
		if topping == None:
			dispatcher.utter_message(text=f"OK! You want to have a {slot_value} {type}.")
		else:
			dispatcher.utter_message(text=f"OK! You want to have a {slot_value} {type} with {topping}.")
		
		return {"pizza_size": slot_value}


class ValidateLoginForm(FormValidationAction):
	def name(self) -> Text:
		return "validate_login_form"
	
	def validate_id(
		self,
		slot_value: Any,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: DomainDict,
	) -> Dict[Text, Any]:

		conn = create_connection("pizzeria.db")
		slot_name = "id"
		
		#get id e password in order to check if is correct [0][0] = id, [0][1] = password, [0][2] = user_name
		get_query_result = select_by_id(conn, slot_name, slot_value)

		if slot_value.lower() != get_query_result[0][0]:
			dispatcher.utter_message(text="Incorrect ID!")
			return {"id": None}

		dispatcher.utter_message(text=f"Correct ID!")
		return {"id": slot_value}
		
	def validate_password(
		self,
		slot_value: Any,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: DomainDict,
	) -> Dict[Text, Any]:

		conn = create_connection("pizzeria.db")
		slot_name = "password"

		#get id e password in order to check if is correct [0][0] = id, [0][1] = password, [0][2] = user_name
		get_query_result = select_by_id(conn, slot_name, slot_value)

		if slot_value.lower() != get_query_result[0][1]:
			dispatcher.utter_message(text="Incorrect password!")
			return {"password": None}

		dispatcher.utter_message(text="Correct password!")
		return {"password": slot_value, "is_logged": True}

class ActionLoginSlots(Action):

	def name(self) -> Text:
		return "action_login_slots"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		conn = create_connection("pizzeria.db")
		slot_name = "id"
		slot_value = tracker.slots.get(slot_name)

		#get id e password in order to check if is correct [0][0] = id, [0][1] = password, [0][2] = user_name
		get_query_result = select_by_id(conn, slot_name, slot_value)

		dispatcher.utter_message(text=f"Successfully logged in! Hi {get_query_result[0][2].capitalize()}.")
		return[]

class ActionAskTopping(Action):

	def name(self) -> Text:
		return "action_ask_topping"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		topping = tracker.slots.get("pizza_topping")

		if topping == None:
			return[FollowupAction(name='utter_ask_topping')]
		else:
			return[FollowupAction(name='action_check_topping')]


class ActionCheckTopping(Action):

	def name(self) -> Text:
		return "action_check_topping"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		conn = create_connection("pizzeria.db")

		pizza = tracker.slots.get("pizza_type")
		size = tracker.slots.get("pizza_size")
		topping = next(tracker.get_latest_entity_values("pizza_topping"), None)

		if topping == None:
			dispatcher.utter_message(text=f"OK! I won't add anything to your {size} {pizza}.")
		else:
			if topping.lower() not in ALLOWED_PIZZA_TOPPINGS:
				dispatcher.utter_message(text=f"I'm sorry! We don't have toppings of this kind. You can add {'/'.join(ALLOWED_PIZZA_TOPPINGS)}.")
				return[FollowupAction(name='utter_ask_topping')]
			else:
				dispatcher.utter_message(text=f"OK! I'll add some {topping} to your {size} {pizza}.")
				update_by_slot(conn=conn, table="toppings", slot_name="pizza_toppings", slot_value=topping, action="SUB", q=1)
		return[]

class ActionCheckDrink(Action):

	def name(self) -> Text:
		return "action_check_drink"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		conn = create_connection("pizzeria.db")

		drink = tracker.slots.get("drink")

		if drink == None:
			dispatcher.utter_message(text=f"OK, no drinks, marked!")
		else:
			if drink.lower() not in ALLOWED_DRIKS:
				dispatcher.utter_message(text=f"I'm sorry! We don't serve this drink. We have: {'/'.join(ALLOWED_DRIKS)}.")
				return[FollowupAction(name='utter_ask_drink')]
			else:
				dispatcher.utter_message(text=f"OK! I'll add a {drink} to your order.")
				update_by_slot(conn=conn, table="drinks", slot_name="drink", slot_value=drink, action="SUB", q=1)
		return[]
	
class ActionInfoDrinks(Action):

	def name(self) -> Text:
		return "action_info_drinks"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		
		dispatcher.utter_message(text=f"Yes, of course. Here are our drinks: {'/'.join(ALLOWED_DRIKS)}.")

		return [FollowupAction(name='utter_ask_drink')]

class ActionChangeTopping(Action):

	def name(self) -> Text:
		return "action_change_topping"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		toppings = []

		conn = create_connection("pizzeria.db")

		pizza = tracker.slots.get("pizza_type")

		old_topping = tracker.slots.get("pizza_topping")
		new_topping = None
		extracted_topping = tracker.latest_message['entities']

		for t in extracted_topping:
			if t['value'] != old_topping:
				new_topping = t['value']

		if new_topping == None:
			dispatcher.utter_message(text=f"You selected the same topping! So, I will leave the {old_topping} on your {pizza}")
		else:
			if new_topping.lower() not in ALLOWED_PIZZA_TOPPINGS:
				dispatcher.utter_message(text=f"I'm sorry! We don't have toppings of this kind. You can add {'/'.join(ALLOWED_PIZZA_TOPPINGS)}.")
				return[FollowupAction(name='utter_change_topping')]
			else:
				#if len(toppings) > 1:
				dispatcher.utter_message(text=f"OK! I replaced the {old_topping} with some {new_topping}.")
				update_by_slot(conn=conn, table="toppings", slot_name="pizza_toppings", slot_value=old_topping, action="SUM", q=1)
				update_by_slot(conn=conn, table="toppings", slot_name="pizza_toppings", slot_value=new_topping, action="SUB", q=1)

				return[SlotSet("pizza_topping", new_topping)]
		return[]
		


class ActionTellMenu(Action):

	def name(self) -> Text:
		return "action_tell_menu"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		menu_list = []
		for pizza, price in MENU.items():
			elem = pizza + ": " + str(price) + '€'
			menu_list.append(elem)

		dispatcher.utter_message(text=f"Here is our menu: {'/'.join(menu_list)}.")

		return []

class ActionInfoTopping(Action):

	def name(self) -> Text:
		return "action_info_toppings"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		pizza_type = tracker.slots.get("pizza_type")
		pizza_size = tracker.slots.get("pizza_size")
		if pizza_type == None or pizza_size == None:
			dispatcher.utter_message(text="Before you can add a topping you must have chosen the type and the size of the pizza")
		dispatcher.utter_message(text=f"Here are the available toppings: {'/'.join(ALLOWED_PIZZA_TOPPINGS)}.")

		return []


class ActionTellPrice(Action):

	def name(self) -> Text:
		return "action_tell_price"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		# check if we are in the form for ordering
		if tracker.active_loop:
			t = next(tracker.get_latest_entity_values("pizza_type"), None)
			if t == None:
				val = tracker.get_slot("pizza_type")
			else:
				val = t
			if val in ALLOWED_PIZZA_TYPES:
				dispatcher.utter_message(text=f"{val} costs {MENU[val]}€.")
			return[]
		else:
			current_pizza = next(tracker.get_latest_entity_values("pizza_type"), None)

			if current_pizza not in ALLOWED_PIZZA_TYPES:
				dispatcher.utter_message(text=f"I don't recognize that pizza. We serve {'/'.join(ALLOWED_PIZZA_TYPES)}.")
			
			dispatcher.utter_message(text=f"{current_pizza} costs {MENU[current_pizza]}€.")

		return []

class ActionTellBill(Action):

	def name(self) -> Text:
		return "action_tell_bill"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		final_bill = 0

		type_pizza = tracker.slots.get("pizza_type")
		size_pizza = tracker.slots.get("pizza_size")
		topping_pizza = tracker.slots.get("pizza_topping")

		menu_price = MENU[type_pizza]

		if size_pizza == "baby":
			final_bill = round((menu_price/2) + 1, 0)
		if size_pizza == "medium" or size_pizza == "m":
			final_bill = round(menu_price, 0)
		if size_pizza == "large" or size_pizza == "l":
			final_bill = round((menu_price*2) - 1, 0)
		if topping_pizza is not None:
			final_bill += 1.5
			
		dispatcher.utter_message(text=f"Here's your bill. Total: {final_bill}€")

		return []
	
class QueryToppingQuantity(Action):

	def name(self) -> Text:
		return "query_topping_quantity"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		conn = create_connection("pizzeria.db")
		extracted_topping = tracker.latest_message['entities']

		for t in extracted_topping:
			slot_value = t['value']
		
		
		if slot_value in ALLOWED_PIZZA_TOPPINGS:
			slot_name = "pizza_toppings"
			get_query_result = select_by_slot(conn, "toppings", slot_name, slot_value)
		else:
			slot_name = "pizza_ingredients"
			get_query_result = select_by_slot(conn, "ingredients", slot_name, slot_value)
		
		print("GET_QUERY_RESULT: ", get_query_result)
		print("GET_QUERY_RESULT[0]: ", get_query_result[0])
		print("slot_value: ", slot_value)


		dispatcher.utter_message(text=f"Hi! There are {get_query_result[0]} pieces of {slot_value} left!")

		return []