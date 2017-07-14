#####################################################
#__________                      __                 #
#\______   \ ____ _____    _____/  |_  ___________  #
# |       _// __ \\__  \ _/ ___\   __\/  _ \_  __ \ #
# |    |   \  ___/ / __ \\  \___|  | (  <_> )  | \/ #
# |____|_  /\___  >____  /\___  >__|  \____/|__|    #
#        \/     \/     \/     \/                    #
#####################################################

from django.test import TestCase

from reactor_master.validators import openc2_validator
from reactor_master.profiles import Dispatcher
from django.http import HttpResponse
import os
import json

# Create your tests here.
class SampleJSONTests(TestCase):

	def test_all_sample_jsons_for_validity(self):
		"""Loops through all sample JSONs and ensures all result in a 200"""

		for filename in os.listdir("./samples"):
			if filename.endswith(".json"): 

				with open('./samples/'+filename, 'r') as content_file:
					
					json_raw = content_file.read()

					self.assertTrue(openc2_validator(json.loads(json_raw)))
				
			else:
				
				continue

		
	def test_all_sample_jsons_in_dispatcher(self):
		"""Loops through all sample JSONs and ensures all result in a 200"""

		for filename in os.listdir("./samples"):
			if filename.endswith(".json"): 
			#if filename.endswith("us.json"): 

				with open('./samples/'+filename, 'r') as content_file:
					
					json_raw = content_file.read()

					openc2_command = json.loads(json_raw)

					dispatcher = Dispatcher()				
					print "Testing %s" % (filename)
					self.assertEquals(200,dispatcher.dispatch(openc2_command).status_code)

			else:
				
				continue
