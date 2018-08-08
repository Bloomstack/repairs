import frappe
from awesome_cart.compat.customer import get_current_customer
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
from frappe.contacts.doctype.contact.contact import get_default_contact
from frappe.core.doctype.role.role import get_emails_from_role
from frappe.desk.form import assign_to
from frappe.model.mapper import get_mapped_doc


def set_missing_values(warranty_claim, method):
	if not warranty_claim.customer:
		customer = get_current_customer()
		warranty_claim.customer = customer.name
	else:
		customer = frappe.get_doc("Customer", warranty_claim.customer)

	warranty_claim.update({
		"customer_name": customer.customer_name,
		"contact_email": customer.email_id,
		"contact_person": get_default_contact("Customer", customer.name)
	})

	if not warranty_claim.contact_mobile:
		warranty_claim.contact_mobile = customer.mobile_no

	if not warranty_claim.serial_no and frappe.db.exists("Serial No", warranty_claim.unlinked_serial_no):
		warranty_claim.serial_no = warranty_claim.unlinked_serial_no

	if warranty_claim.serial_no:
		serial_no = frappe.get_doc("Serial No", warranty_claim.serial_no)

		warranty_claim.update({
			"item_code": serial_no.item_code,
			"item_name": serial_no.item_name,
			"item_group": serial_no.item_group,
			"description": serial_no.description,
			"warranty_amc_status": serial_no.maintenance_status,
			"warranty_expiry_date": serial_no.warranty_expiry_date,
			"amc_expiry_date": serial_no.amc_expiry_date,
			"is_under_warranty": serial_no.maintenance_status in ["Under Warranty", "Under AMC"]
		})


def validate_serial_no_warranty(serial_no, method):
	# Remove warranty period for old manufactured items that are not in the system
	if serial_no.purchase_document_no:
		if frappe.db.get_value("Stock Entry", serial_no.purchase_document_no, "purpose") != "Manufacture":
			serial_no.warranty_period = None


def set_iem_owner(warranty_claim, method):
	serial_no = warranty_claim.serial_no or warranty_claim.unlinked_serial_no

	if serial_no:
		impression_id = frappe.db.get_value("Serial No", serial_no, "impression_id")

		if not impression_id:
			# Split the serial number to retrieve the IID (serial number format: JH{IEM model shorthand}-{IID}-{count})
			impression_id = serial_no.split("-")[1]

			if frappe.db.exists("Serial No", serial_no):
				iem_owner = frappe.db.get_value("IEM Owner", {"impression_id": impression_id}, "name")

				frappe.db.set_value("Serial No", serial_no, "impression_id", impression_id)
				frappe.db.set_value("Serial No", serial_no, "iem_owner", iem_owner)

		warranty_claim.iem_owner = frappe.db.get_value("IEM Owner", {"impression_id": impression_id}, "name")


def assign_warranty_claim(warranty_claim, method):
	if not frappe.get_all("ToDo", filters={"reference_type": "Warranty Claim", "reference_name": warranty_claim.name}):
		repair_settings = frappe.get_doc("Repair Settings")
		user_emails = []

		for notification in repair_settings.notification_settings:
			if notification.status == warranty_claim.status:
				if notification.user:
					user_emails.append(notification.user)

				if notification.role:
					user_emails.extend(get_emails_from_role(notification.role))

				if notification.cc:
					notification.cc = notification.cc.replace(",", "\n")
					user_emails.extend(notification.cc.split("\n"))

		user_emails = list(set(user_emails))
		admin_email = frappe.db.get_value("User", "Administrator", "email")

		if admin_email in user_emails:
			user_emails.remove(admin_email)

		for user in user_emails:
			assign_to.add({
				'assign_to': user,
				'doctype': "Warranty Claim",
				'name': warranty_claim.name,
				'description': "Service Request {0} just moved to the '{1}' status".format(warranty_claim.name, warranty_claim.status),
				'priority': 'Medium',
				'notify': 1
			})


def receive_stock_item(warranty_claim, method):
	if warranty_claim.item_received and warranty_claim.item_code:
		create_stock_entry(warranty_claim)


def create_stock_entry(warranty_claim):
	to_warehouse = frappe.db.get_single_value("Repair Settings", "default_incoming_warehouse")
	serial_no = warranty_claim.serial_no or warranty_claim.unlinked_serial_no

	stock_entry = make_stock_entry(item_code=warranty_claim.item_code, qty=1,
									to_warehouse=to_warehouse, serial_no=serial_no,
									do_not_save=True)

	stock_entry.warranty_claim = warranty_claim.name

	# Include the cable and case in the stock receipt, if entered
	if warranty_claim.cable:
		stock_entry.append("items", {
			"item_code": warranty_claim.cable,
			"t_warehouse": to_warehouse,
			"qty": 1
		})

	if warranty_claim.case:
		stock_entry.append("items", {
			"item_code": warranty_claim.case,
			"t_warehouse": to_warehouse,
			"qty": 1
		})

	for item in stock_entry.items:
		item.allow_zero_valuation_rate = True

	stock_entry.insert()
	stock_entry.submit()

	if not warranty_claim.serial_no:
		warranty_claim.db_set("serial_no", serial_no)

	if not warranty_claim.item_received:
		warranty_claim.db_set("item_received", True)

	warranty_claim.reload()

	return stock_entry.name


def make_mapped_doc(target_dt, source_dn, target_doc, target_cdt=None, filters=None,
					field_map=None, postprocess=None, check_for_existing=True):
	if not field_map:
		field_map = {}

	if not filters:
		filters = {"warranty_claim": source_dn, "docstatus": 1}

	table_map = {
		"Warranty Claim": {
			"doctype": target_dt,
			"field_map": field_map
		}
	}

	if target_cdt:
		table_map.update({
			"Repair Claim Services": {
				"doctype": target_cdt
			}
		})

	# Multiple stock entries can be made against Warranty Claim
	if check_for_existing:
		if frappe.get_all(target_dt, filters=filters):
			return

	return get_mapped_doc("Warranty Claim", source_dn, table_map, target_doc, postprocess=postprocess)
