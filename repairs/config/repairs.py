from __future__ import unicode_literals

from frappe import _


def get_data():
	return [
		{
			"label": _("Requests"),
			"items": [
				{
					"type": "doctype",
					"name": "Warranty Claim"
				}
			]
		},
		{
			"label": _("Setup"),
			"items": [
				{
					"type": "doctype",
					"name": "Repair Settings"
				}
			]
		}
	]
