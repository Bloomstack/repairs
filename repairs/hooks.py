# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "repairs"
app_title = "Repairs"
app_publisher = "DigiThinkIT"
app_description = "Repair management app"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "rohan@digithinkit.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/repairs/css/repairs.css"
# app_include_js = "/assets/repairs/js/repairs.js"

# include js, css files in header of web template
# web_include_css = "/assets/repairs/css/repairs.css"
# web_include_js = "/assets/repairs/js/repairs.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Warranty Claim": "public/js/warranty_claim.js"}
doctype_list_js = {"Warranty Claim": "public/js/warranty_claim_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "repairs.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "repairs.install.before_install"
# after_install = "repairs.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "repairs.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Warranty Claim": {
		"before_insert": "repairs.utils.set_missing_values",
		"after_insert": "repairs.utils.receive_stock_item",
		"validate": "repairs.utils.set_iem_owner",
		"on_update": "repairs.utils.assign_warranty_claim"
	},
	"Serial No": {
		"before_submit": "repairs.utils.validate_serial_no_warranty"
	},
	"Stock Entry": {
		"on_submit": "repairs.status_updater.stock_entry",
		"on_cancel": "repairs.status_updater.stock_entry"
	},
	"Sales Invoice": {
		"on_submit": "repairs.status_updater.sales_invoice",
		"on_cancel": "repairs.status_updater.sales_invoice"
	},
	"Payment Entry": {
		"on_submit": "repairs.status_updater.payment_entry",
		"on_cancel": "repairs.status_updater.payment_entry"
	},
	"Production Order": {
		"on_submit": "repairs.status_updater.production_order",
		"on_cancel": "repairs.status_updater.production_order"
	},
	"DTI Shipment Note": {
		"on_submit": "repairs.status_updater.dti_shipment_note",
		"on_cancel": "repairs.status_updater.dti_shipment_note"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"repairs.tasks.all"
# 	],
# 	"daily": [
# 		"repairs.tasks.daily"
# 	],
# 	"hourly": [
# 		"repairs.tasks.hourly"
# 	],
# 	"weekly": [
# 		"repairs.tasks.weekly"
# 	]
# 	"monthly": [
# 		"repairs.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "repairs.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "repairs.event.get_events"
# }
