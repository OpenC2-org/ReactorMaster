#####################################################
#__________                      __                 #
#\______   \ ____ _____    _____/  |_  ___________  #
# |       _// __ \\__  \ _/ ___\   __\/  _ \_  __ \ #
# |    |   \  ___/ / __ \\  \___|  | (  <_> )  | \/ #
# |____|_  /\___  >____  /\___  >__|  \____/|__|    #
#        \/     \/     \/     \/                    #
#####################################################
# Name: 
#	
#	response.py
#
# Descriptions: 
#	
#	This profile is a basic response receiver, it just reveives and logs responses, and notifies upstream where necassary
#
#
# Sample Files
#	
#	- ./samples/response_ack.json

from reactor_master.decorators import openc2_action
from django.conf import settings
from reactor_master.models import Job,JobStatus,Response
from django.core.exceptions import ObjectDoesNotExist
from reactor_master.response import  make_response_message,respond_message
# Logging
import logging
import json
logger = logging.getLogger("console")

@openc2_action(target_list=[{"type":"openc2:Data"}])
def response(target, actuator, modifier):


	"""
		Name: Response
		Desc: 	This is used to handle response messages sent to the master orchestrator.
				It's job is to store the data sent from downstream and associate it to the job.
				If there is an upstream host that sent us this message it will handle passing the
				response data upstream back to the caller.
	"""

	if "command-ref" in modifier and "type" in modifier:

		# Lookup the job

		try:

			target_job = Job.objects.get(pk=modifier["command-ref"])
			target_job.status = JobStatus.objects.get(status="Success")
			target_job.save()

			if "value" in modifier:
			
				logger.info("Response message received: command:%s type:%s value:%s" % (modifier["command-ref"],modifier["type"],modifier["value"]))
				new_response = Response(job=target_job,
										raw_message=json.dumps(modifier["value"], sort_keys=True, indent=4))

			else:

				logger.info("Response message received: command:%s type:%s " % (modifier["command-ref"],modifier["type"]))
				new_response = Response(job=target_job,
										raw_message=modifier["type"])

			new_response.save()
			
			# If the job has an upstream responder - respond to that
			if target_job.upstream_command_ref:

				logger.info("Responding to upstream.")
				respond_message(make_response_message(target_job.upstream_command_ref,"simple",modifier["value"]),target_job.upstream_respond_to)


		except ObjectDoesNotExist:

			logger.info("No related job found?")

		except Exception,e:

			logger.info("Response Error")

	else:

		logger.warning("RESPONSE Message received that was missing the correct command-ref / type feilds")
