#####################################################
#__________                      __                 #
#\______   \ ____ _____    _____/  |_  ___________  #
# |       _// __ \\__  \ _/ ___\   __\/  _ \_  __ \ #
# |    |   \  ___/ / __ \\  \___|  | (  <_> )  | \/ #
# |____|_  /\___  >____  /\___  >__|  \____/|__|    #
#        \/     \/     \/     \/                    #
#####################################################
from __future__ import unicode_literals

from django.db import models
import json

# Logging
import logging
from django.utils import timezone
logger = logging.getLogger("console")

class OpenC2Action(object):

	"""
	Name: OpenC2Action
	Desc: This is used more as a profile decorator, it never gets stored in the database.
		  The main functionality is to create signatures for profiles, and then identify new
		  messages against the profile to see if it is capable of actionin the OpenC2 command.
	"""

	def __init__(self,name):

		self.name = name
		self.function_signatures = []
		self.function = None


	def sig_match(self, message, function_signature):

		# Should work to the following logic:
		#							|	Specifier In Profile Signature	|	Specifier Not In Profile Signature 
		# Specifier In message		|				Match				|		Match - Generic Profile			(But use profile logic to check specifiers; this saves writing a profile for every firewall etc)
		# Specifier Not In message	|				No Match			|				Match	

		# Check actions
		if function_signature["action"] != message["action"]:

			return False

		# Check Targets
		if function_signature["target"]["type"] != message["target"]["type"]:

			return False

		if "specifiers" in function_signature["target"]:

			for target_spec in function_signature["target"]["specifiers"]:

				if target_spec in message["target"]["specifiers"]:

					if function_signature["target"]["specifiers"][target_spec] != message["target"]["specifiers"][target_spec]:

						return False

				else:

					return False

		# Check Actuators
		if "actuator" in function_signature:

			if function_signature["actuator"]["type"] != message["actuator"]["type"]:

				return False

			if "specifiers" in function_signature["actuator"]:

				for actuator_spec in function_signature["actuator"]["specifiers"]:

					if actuator_spec in message["actuator"]["specifiers"]:

						if function_signature["actuator"]["specifiers"][actuator_spec] != message["actuator"]["specifiers"][actuator_spec]:

							return False
					else:
						return False
		return True

	def identify(self, message):

		# Identify functions capable of handling this message

		for func_sig in self.function_signatures:

			if self.sig_match(message,func_sig["sig"]):

				logger.info("A %s profile matched signature %s" % (self.name,json.dumps(func_sig["sig"])))

				return True

		return False


	def register(self, sig, function):

		self.function_signatures.append({"sig":sig,"function":function})
		self.function = function

	def __call__(self,target, actuator, modifier):

		return self.function(target, actuator, modifier)


class Relay(models.Model):

	# Freindly name for the host
	name = models.CharField(max_length=200)

	# OpenC2 URL
	url = models.CharField(max_length=400)

	# Creds for performing the action
	username = models.CharField(max_length=200,null=True,blank=True)
	password = models.CharField(max_length=200,null=True,blank=True)

class CybOXType(models.Model):

	#Cybox identifier
	identifier = models.CharField(max_length=50)

	template = models.TextField(max_length=1000,default="{}")

class Capability(models.Model):

	# Descriptor
	name = models.CharField(max_length=200)

	# Actuator
	actuator = models.CharField(max_length=200)

	# Openc2 action - eg. DENY
	action = models.CharField(max_length=50)

	# Requires what type of cybox object
	requires = models.ForeignKey(CybOXType,null=False,blank=False)

	# ID of the actuator on the relay
	remote_id = models.IntegerField()

	# Name of the actuator given by the relay
	remote_name = models.CharField(max_length=200)

	# Which profile executes this code
	via = models.ForeignKey(Relay)

	# Is this live after sync
	active = models.BooleanField(default=True)

class Target(models.Model):

	# Name of the target (usually auto generated)
	name = models.CharField(max_length=140)

	# What type of object is this
	cybox_type = models.ForeignKey(CybOXType)

	# Raw CyBox JSON
	raw_message = models.TextField(max_length=500)

class JobStatus(models.Model):

	# Defined by loaddata
	status = models.CharField(max_length=40)

class Job(models.Model):

	# Job - Received/Created OpenC2 action to launch and monitor

	# Capability this job leverages
	capability = models.ForeignKey(Capability)

	# Who/What is this job targetting
	target = models.ForeignKey(Target)

	# Full openc2 command in JSON
	raw_message = models.TextField(max_length=5000)

	# When was it launched
	created_at = models.DateTimeField(default=timezone.now, blank=True)

	# When was it sent
	sent_at = models.DateTimeField(blank=True,null=True)

	# Upstream response details if the orchestrator receives a task via the API
	upstream_respond_to = models.CharField(max_length=5000, null=True)
	upstream_command_ref = models.CharField(max_length=100, null=True)

	# Status of the job - Success/Pending/Sent/Failed
	status = models.ForeignKey(JobStatus)

	# Which user created this (Allows for accountability in teams if the job was created manually)
	created_by = models.ForeignKey("auth.User")


class Response(models.Model):

	# Many-to-One response object to link data from downstream to jobs on the orchestrator

	# Which job
	job = models.ForeignKey(Job)

	# Response data JSON
	raw_message = models.CharField(max_length=5000)

	# Time we got this response
	created_at = models.DateTimeField(default=timezone.now, blank=True)
