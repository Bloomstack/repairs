import frappe
from awesome_cart.compat.customer import get_current_customer
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
from frappe.contacts.doctype.contact.contact import get_default_contact
from frappe.model.mapper import get_mapped_doc


def set_missing_values(doc, method):
	if not doc.customer:
		customer = get_current_customer()
		doc.customer = customer.name
	else:
		customer = frappe.get_doc("Customer", doc.customer)

	doc.customer_name = customer.customer_name
	doc.contact_email = customer.email_id
	doc.contact_person = get_default_contact("Customer", customer.name)

	if not doc.contact_mobile:
		doc.contact_mobile = customer.mobile_no

	if frappe.db.exists("Serial No", doc.unlinked_serial_no):
		doc.serial_no = doc.unlinked_serial_no

	if doc.serial_no:
		serial_no = frappe.get_doc("Serial No", doc.serial_no)

		doc.update({
			"item_code": serial_no.item_code,
			"item_name": serial_no.item_name,
			"description": serial_no.description,
			"warranty_amc_status": serial_no.maintenance_status,
			"warranty_expiry_date": serial_no.warranty_expiry_date,
			"amc_expiry_date": serial_no.amc_expiry_date
		})


def validate_serial_no_warranty(doc, method):
	# Remove warranty period for old manufactured items that are not in the system
	if frappe.db.get_value("Stock Entry", doc.purchase_document_no, "purpose") != "Manufacture":
		doc.warranty_period = None


def receive_stock_item(doc, method):
	if not doc.item_received:
		return

	if not doc.item_code:
		return

	create_stock_entry(doc)


def create_stock_entry(doc):
	to_warehouse = frappe.db.get_single_value("Repair Settings", "default_incoming_warehouse")
	serial_no = doc.serial_no or doc.unlinked_serial_no

	stock_entry = make_stock_entry(item_code=doc.item_code, qty=1,
									to_warehouse=to_warehouse, serial_no=serial_no,
									do_not_save=True)

	stock_entry.warranty_claim = doc.name
	stock_entry.items[0].allow_zero_valuation_rate = True
	stock_entry.insert()
	stock_entry.submit()

	if not doc.serial_no:
		doc.db_set("serial_no", serial_no)

	doc.db_set("item_received", True)
	warranty_not_applicable = True if frappe.db.get_value("Serial No", serial_no, "maintenance_status") != "Under Warranty" else False
	doc.db_set("is_paid", warranty_not_applicable)

	return stock_entry.name


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
