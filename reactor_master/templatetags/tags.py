#!/usr/bin/env python

from django import template
from reactor_master.models import Relay,Job,Capability,Target


register = template.Library()

@register.assignment_tag
def relays():
    return Relay.objects.all()


@register.assignment_tag
def jobs():
    return Job.objects.all()

@register.assignment_tag
def rec_jobs():
    return Job.objects.all().order_by("-id")[:10]

@register.assignment_tag
def rec_targets():
    return Target.objects.all().order_by("-id")[:10]

@register.assignment_tag
def capabilities():
    return Capability.objects.all()

@register.assignment_tag
def targets():
    return Target.objects.all()
