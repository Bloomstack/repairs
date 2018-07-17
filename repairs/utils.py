import frappe
from awesome_cart.compat.customer import get_current_customer
from frappe.contacts.doctype.contact.contact import get_default_contact
from frappe.model.mapper import get_mapped_doc


def set_missing_values(doc, method):
	customer = get_current_customer()

	doc.customer = customer.name
	doc.customer_name = customer.customer_name
	doc.contact_email = customer.email_id
	doc.contact_person = get_default_contact("Customer", customer.name)

	if not doc.contact_mobile:
		doc.contact_mobile = customer.mobile_no

	if frappe.db.exists("Serial No", doc.unlinked_serial_no):
		doc.serial_no = doc.unlinked_serial_no

	if doc.serial_no and not doc.item_code:
		doc.item_code, doc.item_name = frappe.db.get_value("Serial No", doc.serial_no, ["item_code", "item_name"])


def validate_serial_no_warranty(doc, method):
	# Remove warranty period for old manufactured items that are not in the system
	if frappe.db.get_value("Stock Entry", doc.purchase_document_no, "purpose") != "Manufacture":
		doc.warranty_period = None


def make_mapped_doc(target_dt, source_name, target_doc, filters=None, field_map=None, postprocess=None):
	if not field_map:
		field_map = {}

	if not filters:
		filters = {"warranty_claim": source_name, "docstatus": 1}

	existing_doc = frappe.get_all(target_dt, filters=filters)

	if not existing_doc:
		return get_mapped_doc("Warranty Claim", source_name, {
			"Warranty Claim": {
				"doctype": target_dt,
				"field_map": field_map
			},
		}, target_doc, postprocess)
