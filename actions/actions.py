# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from os import name
import sqlite3
import re
from datetime import datetime, timedelta

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

class ActionCheckModality(Action):

	def name(self) -> Text:
		return "action_check_modality"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		conn = create_connection("pizzeria.db")

		modality = tracker.slots.get("modality")

		if modality.lower() == "take-away" or modality.lower() == "take away":
			return[FollowupAction(name='action_tell_pick_time')]
		
		if modality.lower() == "delivery":
			dispatcher.utter_message(text=f"Nice. I need some information!")
			return[FollowupAction(name='delivery_form')]


class ValidateDeliveryForm(FormValidationAction):
	def name(self) -> Text:
		return "validate_delivery_form"
	
	def validate_address(
		self,
		slot_value: Any,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: DomainDict,
	) -> Dict[Text, Any]:

		conn = create_connection("pizzeria.db")
		
		#pattern for address
		pattern = re.compile(r'street|square', re.IGNORECASE)
		#checking the validity
		if pattern.search(slot_value.lower()):
			dispatcher.utter_message(text=f"Correct address!")
			return {"address": slot_value}
		else:
			dispatcher.utter_message(text=f"The provided address is not correct. For our system, it must contain 'street' or 'square'!")
			return {"address": None}
	
	def validate_number_address(
		self,
		slot_value: Any,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: DomainDict,
	) -> Dict[Text, Any]:
	  
		conn = create_connection("pizzeria.db")

		dispatcher.utter_message(text=f"Number of the address stored!.")
		return {"number_address": slot_value}

	def validate_phone(
		self,
		slot_value: Any,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: DomainDict,
	) -> Dict[Text, Any]:
	  
		conn = create_connection("pizzeria.db")

		pattern = re.compile(r'^\+39\d{10}$')
		if pattern.match(slot_value.lower()):
			dispatcher.utter_message(text=f"Perfect! In case of problems you will be called on {slot_value}.")
			return {"phone": slot_value}
		else:
			dispatcher.utter_message(text=f"I'm sorry, but the provided phone number is not valid!")
			return {"phone": None}

	def validate_doorbell(
		self,
		slot_value: Any,
		dispatcher: CollectingDispatcher,
		tracker: Tracker,
		domain: DomainDict,
	) -> Dict[Text, Any]:
	  
		conn = create_connection("pizzeria.db")
		complete_info = ''

		if len(slot_value) < 1:
			dispatcher.utter_message(text=f"Sorry but I need some information. It can't be empty.")
			return {"doorbell": None}
		else:
			for i in slot_value:
				complete_info = complete_info+i.lower()+ ', '
			#remove useless punctuation, like ', '
			if complete_info.endswith(', '):
				complete_info = complete_info[:-2]
			if len(complete_info) < 3:
				dispatcher.utter_message(text=f"Sorry but the information seems to be incorrect or too short (min 4 letters).")
				return {"doorbell": None}
			else:
				dispatcher.utter_message(text=f"Thanks! We will ring this doorbell. See you soon!")
				return {"doorbell": complete_info}

class ActionRecapDelivery(Action):

	def name(self) -> Text:
		return "action_recap_delivery"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		address = tracker.slots.get("address")
		nr_address = tracker.slots.get("number_address")
		phone = tracker.slots.get("phone")
		doorbell = tracker.slots.get("doorbell")

		dispatcher.utter_message(text=f"So. The order will be delivered to {nr_address} {address}. Doorbell: {doorbell[0]}. In case of problems, we will call the number {phone}. Is it correct?")
		return []

class ActionChangeDelivery(Action):

	def name(self) -> Text:
		return "action_change_delivery"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		
		dispatcher.utter_message(text=f"Perfect. Due to too much information requested, however, I ask you to provide all the information again. Thanks!")
		return[SlotSet("address", None), SlotSet("number_address", None), SlotSet("phone", None), SlotSet("doorbell", None), FollowupAction(name='delivery_form')]

class ActionCalcDeliveryTime(Action):

	def name(self) -> Text:
		return "action_calc_delivery_time"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		
		#time in minutes
		preparation_time = 15
		delivery_time = 20

		order_time = datetime.now()
		ready_time = order_time + timedelta(minutes=preparation_time)
		arriving_time = ready_time + timedelta(minutes=delivery_time)
		ready_time = ready_time.strftime("%H:%M")
		arriving_time = arriving_time.strftime("%H:%M")


		dispatcher.utter_message(text=f"The order will be ready by {ready_time}.")
		dispatcher.utter_message(text=f"Taking into account the delivery time, the order will arrive at the address by {arriving_time}.")

		return []

class ActionTellPickTime(Action):

	def name(self) -> Text:
		return "action_tell_pick_time"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		
		preparation_time = 15
		order_time = datetime.now()
		ready_time = order_time + timedelta(minutes=preparation_time)

		#set the time in the right format
		ready_time = ready_time.strftime("%H:%M")
		order_time = order_time.strftime("%H:%M")
		
		dispatcher.utter_message(text=f"Perfect. The order will be ready by {ready_time}. Is ok for you?")
		return [SlotSet("order_time", order_time), SlotSet("ready_time", ready_time)]

class ActionCheckPickTime(Action):

	def name(self) -> Text:
		return "action_check_pick_time"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		
		#time in minutes
		exact_time = tracker.slots.get("complete_time")
		asked_minutes = tracker.slots.get("min_time")

		#times saved by the system
		order_time = tracker.slots.get("order_time")
		ready_time = tracker.slots.get("ready_time")

		order_time = datetime.strptime(order_time, "%H:%M")
		ready_time = datetime.strptime(ready_time, "%H:%M")

		if exact_time != None:
			exact_time = datetime.strptime(exact_time, "%H:%M")
			if exact_time <= ready_time:
				diff = ready_time - exact_time
				exact_time = exact_time.strftime("%H:%M")
				if diff < timedelta(minutes=5):
					dispatcher.utter_message(text=f"Yeah, no problem! The order will be ready by {exact_time}.")
				else:
					r_time = ready_time-timedelta(minutes=5)
					r_time = r_time.strftime("%H:%M")
					if r_time != exact_time:
						dispatcher.utter_message(text=f"I'm sorry but I can't by {exact_time}. I can still try to be 5 minutes early and have the order ready by {r_time}")
					else:
						dispatcher.utter_message(text=f"Yeah, no problem! The order will be ready by {exact_time}.")
			else:
				exact_time = exact_time.strftime("%H:%M")
				dispatcher.utter_message(text=f"Yeah, no problem! The order will be ready by {exact_time}.")
			
		if asked_minutes != None:
			asked_time = order_time + timedelta(minutes=int(asked_minutes))
			if asked_time <= ready_time:
				diff = ready_time - asked_time
				asked_time = asked_time.strftime("%H:%M")
				if diff < timedelta(minutes=5):
					dispatcher.utter_message(text=f"Yeah, no problem! The order will be ready by {asked_time}.")
				else:
					r_time = ready_time-timedelta(minutes=5)
					r_time = r_time.strftime("%H:%M")
					if r_time != asked_time:
						dispatcher.utter_message(text=f"I'm sorry but I can't by {asked_time}. I can still try to be 5 minutes early and have the order ready by {r_time}")
					else:
						dispatcher.utter_message(text=f"Yeah, no problem! The order will be ready by {asked_time}.")
			else:
				asked_time = asked_time.strftime("%H:%M")
				dispatcher.utter_message(text=f"Yeah, no problem! The order will be ready by {asked_time}.")

			
		return []


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

class ActionChangePizza(Action):

	def name(self) -> Text:
		return "action_change_pizza"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
		
		conn = create_connection("pizzeria.db")

		old_pizza = tracker.slots.get("pizza_type")
		old_size = tracker.slots.get("pizza_size")

		new_pizza = None
		new_size = None
		extracted_infos = tracker.latest_message['entities']

		for i in extracted_infos:
			if i['value'] != old_size:
					new_size = i['value']
			if i['value'] != old_pizza:
					new_pizza = i['value']

		old_ingredients = PIZZA_INGREDIENTS[old_pizza]

		if new_pizza != None:
			if new_pizza in ALLOWED_PIZZA_TYPES:
				new_ingredients = PIZZA_INGREDIENTS[new_pizza]

		if new_pizza == None and new_size == None:
			dispatcher.utter_message(text=f"You have ordered the same pizza! So, I will leave the {old_size} {old_pizza} as your order.")

		if new_pizza != None and new_size == None:
			if new_pizza.lower() not in ALLOWED_PIZZA_TYPES:
				dispatcher.utter_message(text=f"I don't recognize that pizza. We serve {'/'.join(ALLOWED_PIZZA_TYPES)}.")
				return[SlotSet("pizza_type", None), SlotSet("pizza_size", None), FollowupAction(name='simple_pizza_form')]
			else:
				dispatcher.utter_message(text=f"OK! Your order has changed. You have orderd a {old_size} {new_pizza}")
			
		if new_pizza == None and new_size != None:
			if new_size.lower() not in ALLOWED_PIZZA_SIZES:
				dispatcher.utter_message(text=f"We only accept pizza sizes: baby/medium(m)/large(l).")
				return[SlotSet("pizza_type", None), SlotSet("pizza_size", None), FollowupAction(name='simple_pizza_form')]
			else:
				dispatcher.utter_message(text=f"OK! Your order has changed. You have orderd a {new_size} {old_pizza}")

		if new_pizza != None and new_size != None:
			if new_pizza.lower() not in ALLOWED_PIZZA_TYPES:
				dispatcher.utter_message(text=f"I don't recognize that pizza. We serve {'/'.join(ALLOWED_PIZZA_TYPES)}.")
				return[SlotSet("pizza_type", None), SlotSet("pizza_size", None), FollowupAction(name='simple_pizza_form')]
			elif new_size.lower() not in ALLOWED_PIZZA_SIZES:
					dispatcher.utter_message(text=f"We only accept pizza sizes: baby/medium(m)/large(l).")
					return[SlotSet("pizza_type", None), SlotSet("pizza_size", None), FollowupAction(name='simple_pizza_form')]
			else:
				dispatcher.utter_message(text=f"OK! Your order has changed. You have ordered a {new_size} {new_pizza}")
		
		#update the ingredients in the database
		if new_pizza != None:
			#new pizza
			for i in new_ingredients[1:]:
				if i in ALLOWED_PIZZA_TOPPINGS:
					update_by_slot(conn=conn, table="toppings", slot_name="pizza_toppings", slot_value=i, action="SUB", q=1)
				else:
					update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value=i, action="SUB", q=1)
			#old pizza
			for i in old_ingredients[1:]:
					if i in ALLOWED_PIZZA_TOPPINGS:
						update_by_slot(conn=conn, table="toppings", slot_name="pizza_toppings", slot_value=i, action="SUM", q=1)
					else:
						update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value=i, action="SUM", q=1)

		if new_size != None:
			#new size
			if new_size == "baby":
				update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value="pizza dough", action="SUB", q=0.5)
			if new_size == "medium" or new_size == "m":
				update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value="pizza dough", action="SUB", q=1)
			if new_size == "large" or new_size == "l":
				update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value="pizza dough", action="SUB", q=2)
			#old size
			if old_size == "baby":
				update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value="pizza dough", action="SUM", q=0.5)
			if old_size == "medium" or old_size == "m":
				update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value="pizza dough", action="SUM", q=1)
			if old_size == "large" or old_size == "l":
				update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value="pizza dough", action="SUM", q=2)
				
		#Setting the new values for the slots
		if new_pizza != None and new_size == None:
			return[SlotSet("pizza_type", new_pizza)]
		if new_pizza == None and new_size != None:
			return[SlotSet("pizza_size", new_size)]
		if new_pizza != None and new_size != None:
			return[SlotSet("pizza_type", new_pizza), SlotSet("pizza_size", new_size)]

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
				dispatcher.utter_message(text=f"OK! I'll add some {topping} to your {size} {pizza}. Is it correct?")
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
				dispatcher.utter_message(text=f"OK! I'll add a {drink} to your order. Is it correct?")
				update_by_slot(conn=conn, table="drinks", slot_name="drink", slot_value=drink, action="SUB", q=1)
		return[]

class ActionChangeDrink(Action):

	def name(self) -> Text:
		return "action_change_drink"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		conn = create_connection("pizzeria.db")

		old_drink = tracker.slots.get("drink")
		new_drink = None

		extracted_drink = tracker.latest_message['entities']

		for i in extracted_drink:
			if i['value'] != old_drink:
				new_drink = i['value']

		if new_drink == None:
			dispatcher.utter_message(text=f"You have ordered the same drink! So, I will leave the {old_drink} as your order.")

		if new_drink != None:
			if new_drink.lower() not in ALLOWED_DRIKS:
				dispatcher.utter_message(text=f"We don't have this type of drink. We serve {'/'.join(ALLOWED_DRIKS)}.")
				return[SlotSet("drink", None), FollowupAction(name='utter_ask_drink')]
			else:
				#update the ingredients in the database
				update_by_slot(conn=conn, table="drinks", slot_name="drink", slot_value=old_drink, action="SUM", q=1)
				update_by_slot(conn=conn, table="drinks", slot_name="drink", slot_value=new_drink, action="SUB", q=1)
				dispatcher.utter_message(text=f"OK! Your order has changed. You have ordered a {new_drink}.")
				return[SlotSet("drink", new_drink)]
				
		return []

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
		drink = tracker.slots.get("drink")

		menu_price = MENU[type_pizza]
		if drink != None:
			menu_price = menu_price + MENU[drink]
			
		if size_pizza == "baby":
			final_bill = round((menu_price/2) + 1, 0)
		if size_pizza == "medium" or size_pizza == "m":
			final_bill = round(menu_price, 0)
		if size_pizza == "large" or size_pizza == "l":
			final_bill = round((menu_price*2) - 1, 0)
		if topping_pizza is not None:
			final_bill += 1
			
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
	
class ActionDeleteOrder(Action):

	def name(self) -> Text:
		return "action_delete_order"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		conn = create_connection("pizzeria.db")

		pizza = tracker.slots.get("pizza_type")
		size = tracker.slots.get("pizza_size")
		topping = tracker.slots.get("pizza_topping")
		drink = tracker.slots.get("drink")
		
		#Pizza type management
		if pizza != None:
			ingredients = PIZZA_INGREDIENTS[pizza]
			for i in ingredients[1:]:
				print(i)
				if i in ALLOWED_PIZZA_TOPPINGS:
					update_by_slot(conn=conn, table="toppings", slot_name="pizza_toppings", slot_value=i, action="SUM", q=1)
				else:
					update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value=i, action="SUM", q=1)

		#Pizza size management
		if size != None:
			if size == "baby":
				update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value="pizza dough", action="SUM", q=0.5)
			if size == "medium" or size == "m":
				update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value="pizza dough", action="SUM", q=1)
			if size == "large" or size == "l":
				update_by_slot(conn=conn, table="ingredients", slot_name="pizza_ingredients", slot_value="pizza dough", action="SUM", q=2)

		#Pizza topping management
		if topping != None:
			update_by_slot(conn=conn, table="toppings", slot_name="pizza_toppings", slot_value=topping, action="SUM", q=1)
		
		#Drink management
		if drink != None:
			update_by_slot(conn=conn, table="drinks", slot_name="drink", slot_value=drink, action="SUM", q=1)

		dispatcher.utter_message(text=f"Your order has been succesfully deleted!")

		#Let's restart the order process
		return [SlotSet("pizza_type", None), SlotSet("pizza_size", None), SlotSet("pizza_topping", None), SlotSet("drink", None), FollowupAction(name='simple_pizza_form')]
		#return ["pizza_type": None, "pizza_size": None, "pizza_topping": None, "drink": None, FollowupAction(name='simple_pizza_form')]


class ActionRecapOrder(Action):

	def name(self) -> Text:
		return "action_recap_order"

	def run(self, dispatcher: CollectingDispatcher,
			tracker: Tracker,
			domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

		#Possibile implementazione con il database: creare una table per tutti gli ordini confermati (+ con il passare del tempo l'ordine viene segnato come completato)
		conn = create_connection("pizzeria.db")

		pizza = tracker.slots.get("pizza_type")
		size = tracker.slots.get("pizza_size")
		topping = tracker.slots.get("pizza_topping")
		drink = tracker.slots.get("drink")
		
		#order: pizza, topping and drink
		if pizza != None and size != None and topping != None and drink != None:
			dispatcher.utter_message(text=f"You have ordered a {size} {pizza} with {topping}. You have also ordered a {drink}. Is it correct?")
		#order: pizza and topping
		if pizza != None and size != None and topping != None and drink == None:
			dispatcher.utter_message(text=f"You have ordered a {size} {pizza} with {topping}. Is it correct?")
		#order: pizza and drink
		if pizza != None and size != None and topping == None and drink != None:
			dispatcher.utter_message(text=f"You have ordered a {size} {pizza}. You have also ordered a {drink}. Is it correct?")
		#order: pizza
		if pizza != None and size != None and topping == None and drink == None:
			dispatcher.utter_message(text=f"You have ordered a {size} {pizza}. Is it correct?")

		return []