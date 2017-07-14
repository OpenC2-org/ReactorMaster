from django import forms
from models import Relay,Job,Capability,CybOXType,Target
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings


class CapabilityChoice(forms.ModelChoiceField):
	def label_from_instance(self,obj):
		return "%s" % (obj.name)

class TypeChoice(forms.ModelChoiceField):
	def label_from_instance(self,obj):
		return "%s" % (obj.identifier)

class TargetChoice(forms.ModelChoiceField):
	def label_from_instance(self,obj):
		return "%s" % (obj.name)

class CreateRelay(forms.ModelForm):

	password = forms.CharField(widget=forms.PasswordInput())
	
	class Meta:
		model = Relay
		exclude = []

	def __init__(self, *args, **kwargs):

		self.request = kwargs.pop('request', None)
		super(CreateRelay, self).__init__(*args, **kwargs)
		
		for visible in self.visible_fields():
			visible.field.widget.attrs['class'] = 'form-control'

class LoginForm(AuthenticationForm):
	username = forms.CharField(label="Username", max_length=30, 
							   widget=forms.TextInput(attrs={'class': 'form-control',
							   								 'name': 'username'}))

	password = forms.CharField(label="Password", max_length=30, 
							   widget=forms.PasswordInput(attrs={'class': 'form-control',
							   									 'name': 'password'}))

class CreateJob(forms.ModelForm):

	capability = CapabilityChoice(queryset=Capability.objects.filter(active=True), empty_label=None)

	target = TargetChoice(queryset=Target.objects.filter(),empty_label=None)

	class Meta:

		model = Job
		exclude = ["sent_at","status","created_at"]

	def __init__(self, *args, **kwargs):

		self.request = kwargs.pop('request', None)
		super(CreateJob, self).__init__(*args, **kwargs)
		self.fields['raw_message'].widget.attrs['rows'] = 20

		for visible in self.visible_fields():
			visible.field.widget.attrs['class'] = 'form-control'


class CreateTarget(forms.ModelForm):

	cybox_type = TypeChoice(queryset=CybOXType.objects.all(), empty_label=None)

	class Meta:

		model = Target
		exclude = ["name","raw_message"]

	def __init__(self, *args, **kwargs):

		self.request = kwargs.pop('request', None)
		super(CreateTarget, self).__init__(*args, **kwargs)

		for visible in self.visible_fields():
			visible.field.widget.attrs['class'] = 'form-control'

