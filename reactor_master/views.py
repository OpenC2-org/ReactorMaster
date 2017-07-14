#####################################################
#__________                      __                 #
#\______   \ ____ _____    _____/  |_  ___________  #
# |       _// __ \\__  \ _/ ___\   __\/  _ \_  __ \ #
# |    |   \  ___/ / __ \\  \___|  | (  <_> )  | \/ #
# |____|_  /\___  >____  /\___  >__|  \____/|__|    #
#        \/     \/     \/     \/                    #
#####################################################

# Django Imports
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# Local Imports
from validators import openc2_validator
from decorators import http_basic_auth
from forms import CreateRelay,CreateJob,CreateTarget
from profiles import Dispatcher
from models import Relay,Capability,CybOXType,Job,JobStatus,Target
import response

# Python Imports
import twilio.twiml
import json
import requests

# Intel Imports
from cybox.core import Observable 
from cybox.objects.address_object import Address
from cybox.objects.network_connection_object import NetworkConnection
from cybox.objects.socket_address_object import SocketAddress
from cybox.objects.port_object import Port
from cybox.objects.uri_object import URI
from cybox.objects.email_message_object import EmailMessage
from cybox.objects.email_message_object import EmailHeader
from mixbox.idgen import set_id_namespace
from mixbox.namespaces import Namespace

# Logging
import logging
logger = logging.getLogger("console")

# Create a single dispatcher on load
dispatcher = Dispatcher()

@csrf_exempt
@http_basic_auth
def service_router(request):

	"""
		Name: service_router
		Desc: Service router is the main view for the /openc2/ endpoint.
			  It's main purpose is to pass off jobs to the dispatcher

	"""

	if request.method != 'POST':
		
		logger.error("None POST request received.")

		return HttpResponse(status=400)

	else:

		try:

			# Parse To JSON			
			openc2_command = json.loads(request.body)
			
		except ValueError:

			# Not a valid JSON
			logger.error("Invalid JSON received from client %s" % request.META.get('REMOTE_ADDR'))
			return HttpResponse(status=400)

		if openc2_validator(openc2_command):


			# Log the message
			logger.info("Inbound message received from %s" % request.META.get('REMOTE_ADDR'))
			logger.info("______________________")
			logger.info(request.body)
			logger.info("______________________")

			# If the user wants an out of band ack
			if "modifiers" in openc2_command:

				if "response" in openc2_command["modifiers"]:

					if openc2_command["modifiers"]["response"] == "ack":

						response.respond_ack(openc2_command["modifiers"])

			# Dispatch
			return dispatcher.dispatch(openc2_command,request.user)

		else:

			return HttpResponse(status=400)

		# TODO: Response
		return HttpResponse(status=200)

@login_required(login_url="login")
@csrf_exempt
def home(request):

	"""
		Name: home
		Desc: Main GUI view

	"""

	# Forms:Job,target and relay creation
	create_job_form = CreateJob(request=request,prefix="create_job")
	create_target_form = CreateTarget(request=request,prefix="create_target")
	create_relay_form = CreateRelay(request=request,prefix="create_relay")

	if request.method == "POST":

		# Remove a relay
		if "delete_relay_id" in request.POST:

			try:

				Relay.objects.get(pk=request.POST["delete_relay_id"]).delete()

			except ObjectDoesNotExist, e:

				pass

		# Create new relay
		if "create_relay-name" in request.POST:

			# Actuator creation
			create_relay_form =  CreateRelay(request.POST,request=request,prefix="create_relay")
			if create_relay_form.is_valid():

				host = create_relay_form.save()
				host.save()

			# TODO - Call a sync here

		# Job Creations
		if "create_job-raw_message" in request.POST:

			new_job = Job(capability=Capability.objects.get(pk=request.POST["create_job-capability"]),
						  target=Target.objects.get(pk=request.POST["create_job-target"]),
						  raw_message="Pending",
						  status=JobStatus.objects.get(status="Pending"),
						  created_by=request.user)

			new_job.save()

			# Now we have a pk - update the id

			command = json.loads(request.POST["create_job-raw_message"])
			command["modifiers"]["command-ref"] = new_job.id

			logger.info("Job Created\n%s" % json.dumps(command))

			new_job.raw_message = json.dumps(command,sort_keys=True,indent=4).replace("\t", u'\xa0\xa0\xa0\xa0\xa0')
			new_job.save()

		# Target Creations
		
		namespace_url = getattr(settings, "NAMESPACE_URL", None)
		namespace_id = getattr(settings, "NAMESPACE_ID", None)
		
		set_id_namespace(Namespace(namespace_url, namespace_id))

		if "create_target-cybox_type" in request.POST:

			cybox_type = CybOXType.objects.get(pk=request.POST["create_target-cybox_type"])

			if cybox_type.identifier == "cybox:NetworkConnectionObjectType":

				obs = NetworkConnection()

				# Source
				sock = SocketAddress()
				sock.ip_address = request.POST["create_target-source_address"]
				sock.ip_address.category = "ipv4-addr"
				sock.ip_address.condition = "Equals"
				sport = Port()
				sport.port_value = int(request.POST["create_target-source_port"])
				sock.port = sport
				obs.source_socket_address = sock

				# Dest
				sock = SocketAddress()
				sock.ip_address = request.POST["create_target-destination_address"]
				sock.ip_address.category = "ipv4-addr"
				sock.ip_address.condition = "Equals"
				dport = Port()
				dport.port_value = int(request.POST["create_target-destination_port"])
				sock.port = dport
				obs.destination_socket_address = sock

				name = "Network Connection %s:%s -> %s:%s (%s)" % ( request.POST["create_target-source_address"],
																	request.POST["create_target-source_port"],
																	request.POST["create_target-destination_address"],
																	request.POST["create_target-destination_port"],
																	request.POST["create_target-protocol"])

				raw_message = Observable(item=obs,title=name).to_json()

			elif cybox_type.identifier == "cybox:AddressObjectType":

				name = "Address %s " % (request.POST["create_target-address"])
				raw_message = Observable(item=Address(address_value=request.POST["create_target-address"], category=Address.CAT_IPV4),title=name).to_json()
			
                        elif cybox_type.identifier == "cybox:URIObjectType":
                            name = "URI %s " % (request.POST["create_target-uri"])
                            obs = URI()
                            obs.value = request.POST["create_target-uri"]
                            obs.type_ = URI.TYPE_URL
                            obs.condition = "Equals"
                            raw_message = Observable(item=obs,title=name).to_json()

                        elif cybox_type.identifier == "cybox:EmailMessageObjectType":
                            name = "Email %s " % (request.POST["create_target-email_subject"])
                            obs = EmailMessage()
                            obs.raw_body = request.POST["create_target-email_message"]
                            obs.header = EmailHeader()
                            obs.header.subject = request.POST["create_target-email_subject"]
                            obs.header.subject.condition = "StartsWith"
                            obs.header.to = request.POST["create_target-email_to"]
                            obs.header.from_ = request.POST["create_target-email_from"]
                            raw_message = Observable(item=obs,title=name).to_json()
			else:

				# Should never reach here
				raw_message = {}
				name = "Undefined Object"

			create_target_form = CreateTarget(request.POST,request=request,prefix="create_target")

			if create_target_form.is_valid():

				target = create_target_form.save(commit=False)
				
				target.name = name

				target.raw_message = raw_message

				target.save()

	# Get data for the tables
	relays = Relay.objects.all()
	capabilities = Capability.objects.filter(active=True)

	return render(request,"reactor_master/home.html", {
		"create_relay_form":create_relay_form,
		"relays":relays,
		"create_job_form":create_job_form,
		"create_target_form":create_target_form,		
		"capabilities":capabilities,
		})

@login_required(login_url="login")
@csrf_exempt
def job(request,id):

	"""
		Name: job
		Desc: Single job view
	"""

	job = Job.objects.get(pk=id)

	r = []
	for response in job.response_set.all():

		response.raw_message = response.raw_message.replace("\\n","\n")
		r.append(response)

	return render(request,"reactor_master/job.html", {
		"job":job,
		"responses":r,
		})

@login_required(login_url="login")
@csrf_exempt
def sync(request):

	"""
		Name: sync
		Desc: 	Post endpoint to sync to downstream relays. This takes the relays that have been configured by the users,
				sends them an openc2:openc2 query to get the relays capabilities, then updates its local record of capabilities
	"""
	discovery_message = {"action": "query","actuator": {"specifiers": {},"type": "openc2:openc2"},"modifiers": {},"target": {"type":"openc2:openc2"}}

	for relay in Relay.objects.all():

		logger.info("Syncing with relay %s" % relay.name)
		
		headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

		r = requests.post(relay.url, data=json.dumps(discovery_message),headers=headers,auth=(relay.username, relay.password))

		if r.status_code == 200:

			# Decode the list response
			logger.info(r.text)
			capabilities = json.loads(r.text)

			# Keep a list of which capabilities we see so we can deactivate old ones
			active_capabilities = []

			for capa in capabilities:

				for host in capa["actuator"]["specifiers"]["available"]:

					# Look it up in active capabilities
					try:

						live_capa = Capability.objects.get( actuator=capa["actuator"]["type"],
															action=capa["action"],
															requires=CybOXType.objects.get(identifier=capa["target"]["type"]),
															remote_id=host["id"],
															remote_name=host["name"],
															active=True)
						logger.info("UPDATED: %s - %s (%s) -%s via %s" % (capa["action"],capa["actuator"]["type"],host["name"],capa["target"]["type"],relay.name))
					
					except ObjectDoesNotExist:

						# Create this capability
						cybox,created = CybOXType.objects.get_or_create(identifier=capa["target"]["type"])
						live_capa = Capability(name="%s - %s via %s" % (host["action_tag"],host["name"],relay.name),
											 actuator=capa["actuator"]["type"],
											 action=capa["action"],
											 requires=cybox,
											 remote_id=host["id"],
											 remote_name=host["name"],
											 via=relay
											 )

						live_capa.save()
						logger.info("CREATED: %s - %s (%s) -%s via %s" % (capa["action"],capa["actuator"]["type"],host["name"],capa["target"]["type"],relay.name))
					
					active_capabilities.append(live_capa.id)

			# Remove inactive capas
			Capability.objects.filter().exclude(pk__in=active_capabilities).update(active=False)


		else:

			return HttpResponse(json.dumps({"success":False}))

	return HttpResponse(json.dumps({"success":True}))

@login_required(login_url="login")
@csrf_exempt
def relay(request,relay_id):

	"""
		Name: relay
		Desc: Single relay view
	"""

	relay = Relay.objects.get(pk=relay_id)

	jobs = Job.objects.filter(capability__via=relay,capability__active=True)

	return render(request,"reactor_master/relay.html", {
		"relay":relay,
		"jobs":jobs,
		})


@login_required(login_url="login")
@csrf_exempt
def rest_make_command(request,capa_id,target_id):

	"""
		Name: rest_make_command
		Desc: Used to get the JSON representation for a capability and target
	"""

	try:

		capa = Capability.objects.get(pk=capa_id)
		target = Target.objects.get(pk=target_id,cybox_type=capa.requires)

		openc2_command = {
			"action": capa.action, 
			"actuator": {
				"specifiers": {
					"id":capa.remote_id,
					"name":capa.remote_name,
				}, 
				"type": capa.actuator
			}, 
			"modifiers": {
					"respond-to": getattr(settings, "OPENC2_RESPONSE_URL", None)
			}, 
			"target": {
				"specifiers": json.loads(target.raw_message), 
				"type": capa.requires.identifier
			}
		}

		return HttpResponse(json.dumps(openc2_command))

	except ObjectDoesNotExist:

		return HttpResponse("{}")

	except Exception,e:

		return HttpResponse("{}")

@login_required(login_url="login")
@csrf_exempt
def rest_get_targets(request,capa_id):

	"""
		Name: rest_get_targets
		Desc: This takes a capability and finds all valid targets so they can be put in a drop down
	"""

	capa = Capability.objects.get(pk=capa_id)

	targets = Target.objects.filter(cybox_type=capa.requires)

	target_ids = []

	for target in targets:

		target_ids.append(target.id)

	return HttpResponse(json.dumps(target_ids))

@csrf_exempt
def cron_launcher(request):

	"""
		Name: cron_launcher
		Desc: 	This is hacky - i call these with wget locally, but its a simple way to execute
				scheduled jobs without needing alot of third party libraries.
				This function should be called every 60 seconds, it launches pending jobs
	"""

	for job in Job.objects.filter(status__status="Pending"):

		headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

		job.status = JobStatus.objects.get(status="Sent")
		job.sent_at = timezone.now()
		job.save()

		try:
		
			# TODO: Send this async
			r = requests.post(job.capability.via.url, data=job.raw_message,headers=headers,auth=(job.capability.via.username, job.capability.via.password))
		
		except:
			
			job.status = JobStatus.objects.get(status="Failed")
			job.sent_at = timezone.now()
			job.save()

		else:

			if r.status_code != 200:

				job.status = JobStatus.objects.get(status="Failed")
				job.sent_at = timezone.now()
				job.save()

	return HttpResponse("Ok.")
