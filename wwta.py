import json
from collections import OrderedDict
#officebear2000

STORY = {}


class Room(object):
	def __init__(self, name, description):
		self.name = name
		self.description = description
		self.contents = OrderedDict()
		
	def add_item(self, id, item):
		self.contents[id] = item
	
	def remove_item(self, id):
		success = False
		try:
			del self.contents[id]
			success = True
		except:
			success = False
			
		#if we can't delete the item, try deleting items in items.
		if success == False:
			for ident, item in self.contents.iteritems():
				if success == False:
					success = item.remove_item(id)
		
		return success
		
	
	def get_item(self, id):
	
		return_item = False
	
		try:
			return_item = self.contents[id]
		except:
			return_item = False
		
		#if the item isn't directly available in the room, look in it's items.
		if return_item == False:
			#print "Looking through items in room"
			for ident, item in self.contents.iteritems():
				#print ident, item
				
				if return_item == False:
					return_item = item.get_item(id)
				
				
		return return_item
	
	def describe(self):
		return_string = "%s\n" % self.description
		
		if len(self.contents) > 0:
			return_string += "You can see:\n"
			for ident, item in self.contents.iteritems():
				return_string += " - %s\n" % item.name
			
		return return_string
		
class Item(object):
	def __init__(self, name, description, container_type='internal'):
		self.name = name
		self.description = description
		self.contents = OrderedDict()
		self.container_type = container_type
		self.locked = False
		self.grabbable = False
		self.custom_properties = {}
		
	def add_item(self, id, item):
		self.contents[id] = item
	
	def remove_item(self, id):
		try:
			del self.contents[id]
			return True
		except:
			#print "Cannot delete that item"
			return False
	
	def get_item(self, id):
	
		#print "Getting sub-item %s" % id
	
		return_item = False
		try:
			return_item = self.contents[id]
		except:
			return_item = False
			
		#print "Name: %s" % return_item
			
		#If this item is an internal container and locked, don't return anything
		if self.container_type == 'internal' and self.locked == True:
			return False
			
		if return_item != False:
			return return_item
		else:
			return False
			

		
	def add_custom_prop(self, property, value):
		self.custom_properties[property] = value;
	def get_custom_prop(self, property):
		try:
			return self.custom_properties[property]
		except:
			return False
	def del_custom_prop(self, property):
		try:
			del self.custom_properties[property]
			return True
		except:
			return False

	
	def describe(self):
		return_string = "%s" % self.description
		
		if self.container_type == 'surface':
			adjunct = "On"
		elif self.container_type == 'attached':
			adjunct = "Attached to"
		else:
			adjunct = "In"
		
		if len(self.contents) > 0:
			
			if self.locked:
				return_string += "\nIt is locked"
		
			if self.locked and self.container_type == 'internal':
				return_string += " so you cannot see what is %s it" % adjunct
			else:
				return_string += "\n%s it there is:" % adjunct
				for ident, item in self.contents.iteritems():
					return_string += "\n - %s" % item.name
		
		return return_string

		
class Player(object):
	def __init__(self, name):
		self.name = name
		self.health = STORY['player']['start_health']
		self.inventory = OrderedDict()
		
	def add_to_inventory(self, ident, item):
		self.inventory[ident] = item
		print "%s is now in your pocket." % item.name
		
	def describe_inventory(self):
		return_string = "You pockets contain:\n"
		if len(self.inventory) > 0:
			for ident, item in self.inventory.iteritems():
				return_string += " - %s\n" % item.name
		else:
			return_string += "Bugger all."
			
		return return_string
		
	def get_inventory_item(self, id):
		return_item = False
		try:
			return_item = self.inventory[id]
		except:
			return_item = False
			
		return return_item
		
	def remove_inventory_item(self, id):
		success = False
		try: 
			del self.inventory[id]
			success = True
		except:
			success = False
			
		return success
		
	def adjust_health(self, amount):
		self.health += amount
		if self.health > 100:
			self.health = 100
		if self.health <= 0:
			self.die()
			
		print "Your health is now %s%%" % self.health
		return self.health
		
	def die(self):
		if self.health <= 0:
			print "YOU DEAD"
		
		
		
		
class Map(object):
	def __init__(self, start_room):
		self.rooms = {}
		self.item_ref = {}

		# Process Rooms from story
		# print STORY['rooms']

		for room_id,room in STORY['rooms'].iteritems():
			# Add each room to the stack
			#print "Adding room: %s" % room_id
			self.rooms[room_id] = Room(
				room['name'],
				room['description'],
			)

			# Process items using our process items func, while pretending room is an item
			self.process_items(room, self.rooms[room_id], room_id)

		self.start_room = self.rooms[start_room]


	def process_items(self, item_json, item_obj, room_id):

		if 'items' in item_json:
			for item_id,item in item_json['items'].iteritems():

				new_item = Item(item['name'], item['description'])

				if 'container_type' in item:
					new_item.container_type = item['container_type']

				if 'grabbable' in item and item['grabbable'] == 'true':
					new_item.grabbable = True

				if 'locked' in item and item['locked'] == 'true':
					new_item.locked = True

				if 'custom_props' in item:
					for prop_id,prop in item['custom_props'].iteritems():
						new_item.add_custom_prop(prop_id, prop)

				# Adding to item ref using room id and item id
				self.item_ref["%s.%s" % (room_id,item_id)] = new_item
				item_obj.add_item(item_id, new_item)

				# Start another process loop for any nested objects
				self.process_items(item, item_obj.contents.get(item_id), room_id)



class Engine(object):
	def __init__(self, map, config):
		self.map = map
		self.playing = True
		self.current_room = map.start_room
		self.player = Player(STORY['player']['name'])
		self.introduction = config['intro']
		self.instructions = config['instructions']
		self.seperator = config['seperator']
		
	def play(self):
		
		print self.seperator
		print self.introduction
		print self.seperator
		print self.instructions
		print self.seperator
		
		#Process any player starting items

		for item_id, item in STORY['player']['items'].iteritems():
			new_item = Item(item['name'], item['description'])

			if 'container_type' in item:
				new_item.container_type = item['container_type']

			if 'grabbable' in item and item['grabbable'] == 'true':
				new_item.grabbable = True

			if 'locked' in item and item['locked'] == 'true':
				new_item.locked = True

			if 'custom_props' in item:
				for prop_id,prop in item['custom_props'].iteritems():
					new_item.add_custom_prop(prop_id, prop)

			self.player.add_to_inventory(item_id, new_item)

		
		while self.playing == True:
		
			if self.player.health <= 0:
				self.playing == False
				return True
			
			#introduce room
			print "You are in the %s" % self.current_room.name
			print self.current_room.describe()
			
			room_changed = False
			
			while room_changed == False:
				print self.seperator
				print "What do you want to do? (%s%%) >" % self.player.health,
				user_action = raw_input()
				print self.seperator
				action = action_interpreter(user_action)
				
				if action['action'] == 'waddleto' or action['action'] == 'wt':
					print "Walking"
					
				elif action['action'] == 'lookat' or action['action'] == 'l':
				
					if action['action_subject'] == 'room' or action['action_subject'] == 'area':
						print "%s - %s" % (self.current_room.name, self.current_room.describe())
					else:	
					
				
						try:
							item = self.current_room.get_item(action['action_subject'])
						except:
							item = False
						
						if item == False:
							try:
								item = self.player.get_inventory_item(action['action_subject'])
							except:
								pass	
					
						if item:
							print item.describe()
						else:
							print "There is no item called that to look at."
				
				elif action['action'] == 'read' or action['action'] == 'r':
					item = self.current_room.get_item(action['action_subject'])
					
					if item == False:
						item = self.player.get_inventory_item(action['action_subject'])
						
					if item:
						text = item.get_custom_prop('text_content')
						if text:
							print "It says:\n-----\n%s\n-----" % text
						else:
							print "There is nothing to read."
					else:
						print "There is no object called that that you can read."
					
				elif action['action'] == 'use' or action['action'] == 'u':
						
						
					item = self.current_room.get_item(action['action_subject'])
						
					if item == False or item.get_custom_prop('remotely_usable') != True:
						item = self.player.get_inventory_item(action['action_subject'])
						
					if action['action_object']:
						
						use_item = self.player.get_inventory_item(action['action_object'])
						
						if item:
						
							if use_item:
								
								#Key Item
								if item.get_custom_prop('passcode'):
									if item.get_custom_prop('passcode') == use_item.get_custom_prop('passcode'):
										unlocked_item = self.map.item_ref[item.get_custom_prop('unlocks')]
										unlocked_item.locked = False
										print "The %s is now unlocked" % unlocked_item.name
									else:
										print "You can't use this on anything! You really are a nob-head."
								else:
									print "You can't use things on this!"
								
								
								
							else:
								print "You do not have that item to use."
						else:
							print "There is no item called that you can use things on."
						
						
						#Any use x on x statements
						
						#Keys
						
					
					else:
							
						if item:
							
							#Food based items
							if item.get_custom_prop('energy'):
								print "Eating %s" % item.name
								if item.get_custom_prop('use_feedback'):
									print item.get_custom_prop('use_feedback')
								self.player.adjust_health(item.get_custom_prop('energy'))
								
								uses = item.get_custom_prop('uses')
								uses -= 1
								if uses <= 0:
									print "The %s is finished" % item.name
									success = self.player.remove_inventory_item(action['action_subject'])
								else:
									item.del_custom_prop('uses')
									item.add_custom_prop('uses', uses)
								
							#Key based items
							if item.get_custom_prop('unlocks') and not item.get_custom_prop('unlocks_with'):
								unlocked_item = self.map.item_ref[item.get_custom_prop('unlocks')]
								unlocked_item.locked = False
								print "The %s is now unlocked" % unlocked_item.name
								
							if item.get_custom_prop('unlocks_with'):
								print "You need to use something on this for it to work"
								
							if item.locked:
								print "You cannot use this. It is locked."
								
							if item.locked == False and item.get_custom_prop('starts_room'):
								if item.get_custom_prop('auto_locks') == 1:
									item.locked = True
								self.current_room = self.map.rooms[item.get_custom_prop('starts_room')]
								room_changed = True
								
							
						else:
							print "There is no object called that that you can use.  (You might need to pick it up first)"					
					
					
				elif action['action'] == 'pickup' or action['action'] == 'p':
					item = self.current_room.get_item(action['action_subject'])
					if item and item.grabbable == True:
						self.player.add_to_inventory(action['action_subject'], item)
						del_success = self.current_room.remove_item(action['action_subject'])
					elif item and item.grabbable == False:
						print "You can't pick that up, that would be ridiculous!"
					else:
						print "There is no item called that to pick up!"
						
						
				
				elif action['action'] == 'inventory' or action['action'] == 'i':
					print self.player.describe_inventory()
				
				elif action['action'] == 'instructions':
					print self.instructions
				
				elif action['action'] == 'quit':
					room_changed = True
					self.playing = False
					print "Byeeeeeeeeeeee!"
				else:
					print "You can't do that!"




		
def action_interpreter(user_input):
	#get the first word
	user_input_list = user_input.split(' ')
	action_obj = {}
	action_obj['action'] = user_input_list.pop(0)
	action_obj['action_subject'] = False
	action_obj['action_object'] = False
	
	#join the other bits back together
	user_input = ' '.join(user_input_list)
	
	#remove nasty characters
	user_input = user_input.replace("'", "")
	
	if action_obj['action'] in ['u','use'] and ' on ' in user_input:
		action_obj.update({'action_subject' : user_input.split(' on ')[1].lower().replace(' ','_'),
				'action_object' : user_input.split(' on ')[0].lower().replace(' ','_')})
	elif len(user_input) > 0:
		action_obj['action_subject'] = user_input.lower().replace(' ','_')
	
	#print action_obj

	return action_obj

print "Starting..."

# Load Story
with open('story.json', 'r') as fp:
	STORY = json.load(fp)
room_map = Map(STORY['start_room'])
game = Engine(room_map, STORY['config'])
game.play()

