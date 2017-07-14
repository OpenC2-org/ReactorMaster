#####################################################
#__________                      __                 #
#\______   \ ____ _____    _____/  |_  ___________  #
# |       _// __ \\__  \ _/ ___\   __\/  _ \_  __ \ #
# |    |   \  ___/ / __ \\  \___|  | (  <_> )  | \/ #
# |____|_  /\___  >____  /\___  >__|  \____/|__|    #
#        \/     \/     \/     \/                    #
#####################################################

# Django imports
from django.http import Http404
from django.http import HttpResponse
from django.conf import settings

# Python imports
import collections
import imp
import os
import response
import json

# Local models
from ..models import OpenC2Action,Capability,Relay,Target,CybOXType,Job,JobStatus

# Cybox/STIX/TAXII Stuff
from cybox.core import Observable 
from cybox.objects.address_object import Address

# Logging
import logging
logger = logging.getLogger("console")

class Dispatcher(object):

	def __init__(self):

		"""
			Name: __init__
			Desc: 	Loops through the live modules in settings.py to workout which to load
					on the master this is pretty simple as we only need response.py
					but I have kept this in incase people want to create profiles on the master in the future.
		"""

		logger.info("Initialising master")
		
		self.profiles = collections.deque()

		for module in settings.OPENC2_PROFILES:

			logger.info("Loading profile %s" % module)
			self.profiles.appendleft(imp.load_source(module.split(".")[0], "./reactor_master/profiles/"+module))

	def capabilities(self):

		"""
			Name: capabilities
			Desc: 	This is used to return a JSON of capabilities to any upstream requests.
					It works by looping through the discovered capabilities and building a list
					of JSON OpenC2 commands that can be received.
		"""

		logger.debug("Capabilities called. Upstream is syncing")
		
		# New method - uses defined capabilities
		registered_actuators = []
		info = []

		for capa in Capability.objects.all():

			# Unique OpenC2 Types
			if capa.actuator+capa.action+capa.requires.identifier not in registered_actuators:

				registered_actuators.append(capa.actuator+capa.action+capa.requires.identifier)
				# Get all hosts that have this capabiltiy - you could just look up all this type auto fill
				capable_hosts = Capability.objects.filter(capability__actuator=capa.actuator,capability__action=capa.action,capability__requires=capa.requires)

				supported_hosts = []

				for capable_host in capable_hosts:

					supported_hosts.append({"id":capable_host.remote_id,"name":capable_host.remote_name,"local_name":capa.name})

				capa_dict = {"action":capa.action,"actuator":{"type":capa.actuator,"specifiers":{"available":supported_hosts}},"target":{"type":capa.requires.identifier}}
				info.append(capa_dict)

		return json.dumps(info)


	def dispatch(self,message,user):

		"""
			Name: dispatch
			Desc: 	Dispatch is called by the main /openc2/ api view. It actions which downstream host
					to send a received command to. It creates the job locally so it can be tracker
					and re-dresses the respond-to feilds so it can intercept command success/fail on
					downstream relays/actuators.
		"""

		logger.debug("Dispatcher called")
		capable_handlers = []

		# Check action / target type
		if message["action"] == 'query' and message["target"]["type"] == 'openc2:openc2':
			return HttpResponse(self.capabilities(),status=200)

		# If the message is a down stream response
		if message["action"].lower() == "response":

			response.response(message["target"], message.get("actuator"), message.get("modifiers"))
			return HttpResponse(status=200)

		# This is an action destined for a downstream host
		message['action'] = message['action'].lower()

		# Work out which downstreams are capable of this action
		capable = False

		if "specifiers" in message["actuator"]:

			# If the end user is targetting a specific actuator
			if "id" in message["actuator"]["specifiers"]:

				capable = Capability.objects.filter(actuator=message["actuator"]["type"],action=message["action"],requires__identifier=message["target"]["type"],remote_id=message["actuator"]["specifiers"]["id"],active=True)

			elif "name" in message["actuator"]["specifiers"]:

				capable = Capability.objects.filter(actuator=message["actuator"]["type"],action=message["action"],requires__identifier=message["target"]["type"],remote_name=message["actuator"]["specifiers"]["name"],active=True)

		else:

			capable = Capability.objects.filter(actuator=message["actuator"]["type"],action=message["action"],requires__identifier=message["target"]["type"],active=True)


		if capable:

			# Someone is capable of dealing with this message

			# Odds of the target being in our database is low - so will make a new one anyway
			# TODO: Expand this to handle other types (Network Connection)

			# False / Object
			target = False

			# Address Handling
			if message["target"]["type"] == "cybox:AddressObjectType":

				cybox_address_obs = Observable.from_json(json.dumps(message["target"]["specifiers"]))
				address = str(cybox_address_obs.object_.properties.address_value)
				target = Target(name="Auto Target - %s" % address,
								cybox_type=CybOXType.objects.get(identifier=message["target"]["type"]),
								raw_message=json.dumps(message["target"]["specifiers"]))
				logger.info("Target %s Created" % address)
				target.save()

			elif message["target"]["type"] == "cybox:NetworkConnectionObjectType":
				
				# TODO: Handler
				pass

			# If we have been able to assign a valid target
			if target:

				for capability in capable:

					new_job = Job(capability=capability,
							  target=target,
							  raw_message="Pending",
							  status=JobStatus.objects.get(status="Pending"),
							  created_by = user)
					
					new_job.save()

					command = {
						"action": capability.action, 
						"actuator": {
							"specifiers": {
								"id":capability.remote_id,
								"name":capability.remote_name,
							}, 
							"type": capability.actuator
						}, 
						"modifiers": {
								"respond-to": getattr(settings, "OPENC2_RESPONSE_URL", None)
						}, 
						"target": {
							"specifiers": json.loads(target.raw_message), 
							"type": capability.requires.identifier
						}
					}

					command["modifiers"]["command-ref"] = new_job.id

					logger.info("Job Created - Command - %s" % (json.dumps(command)))

					# Handle upstream respond to - send the copy back to us and pass it on to an upstream
					if "respond-to" in message["modifiers"]:

						new_job.upstream_respond_to = message["modifiers"]["respond-to"]
						new_job.upstream_command_ref = message["modifiers"]["command-ref"]

					new_job.raw_message = json.dumps(command,sort_keys=True,indent=4).replace("\t", u'\xa0\xa0\xa0\xa0\xa0')
					new_job.save()

					return HttpResponse(status=200)
			else:

				logger.error("Failed to identify target")
				return HttpResponse(status=501)
		else:

			return HttpResponse(status=501)



				

