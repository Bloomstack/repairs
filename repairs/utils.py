import frappe
from awesome_cart.compat.customer import get_current_customer
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
from frappe import _
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
		"contact_person": get_default_contact("Customer", customer.name)
	})

	if not warranty_claim.contact_email:
		warranty_claim.contact_email = customer.email_id

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


def validate_missing_serial_no(warranty_claim, method):
	if warranty_claim.item_group == "Custom":
		if not (warranty_claim.serial_no or warranty_claim.unlinked_serial_no):
			frappe.throw(_("Custom products must have a serial number"))


def validate_serial_no_warranty(serial_no, method):
	# Remove warranty period for old manufactured items that are not in the system
	if serial_no.purchase_document_no:
		if frappe.db.get_value("Stock Entry", serial_no.purchase_document_no, "purpose") != "Manufacture":
			serial_no.warranty_period = None


def set_iem_owner(warranty_claim, method):
	if warranty_claim.item_group and warranty_claim.item_group != "Custom":
		warranty_claim.iem_owner = None
		return

	serial_no = warranty_claim.serial_no or warranty_claim.unlinked_serial_no

	if serial_no:
		impression_id = frappe.db.get_value("Serial No", serial_no, "impression_id")

		if not impression_id:
			# Split the serial number to retrieve the IID (serial number format: JH{IEM model shorthand}-{IID}-{count})
			impression_id = serial_no.split("-")
			impression_id = impression_id[1] if len(impression_id) > 1 else impression_id[0]

			try:
				impression_id = int(impression_id)
			except ValueError:
				return

			if impression_id:
				if frappe.db.exists("Serial No", serial_no):
					frappe.db.set_value("Serial No", serial_no, "impression_id", impression_id)

					iem_owner = frappe.get_all("IEM Owner", or_filters={"impression_id": impression_id, "old_impression_id": impression_id})
					if iem_owner:
						frappe.db.set_value("Serial No", serial_no, "iem_owner", iem_owner[0].name)

		if impression_id:
			iem_owner = frappe.get_all("IEM Owner", or_filters={"impression_id": impression_id, "old_impression_id": impression_id})
			if iem_owner:
				warranty_claim.iem_owner = iem_owner[0].name
			else:
				warranty_claim.iem_owner = None
		else:
			warranty_claim.iem_owner = None


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


def set_shipping_date(dti_shipment_note, method):
	warranty_claim = frappe.db.get_value("Delivery Note", dti_shipment_note.delivery_note, "warranty_claim")

	if warranty_claim:
		warranty_claim = frappe.get_doc("Warranty Claim", warranty_claim)

		if method == "on_submit":
			warranty_claim.shipping_date = frappe.utils.now_datetime()
		elif method == "on_cancel":
			warranty_claim.shipping_date = None

		warranty_claim.save()


def complete_production_order(stock_entry, method):
	if method == "on_submit":
		if stock_entry.purpose == "Material Transfer for Manufacture":
			warranty_claim = frappe.db.get_value("Production Order", stock_entry.production_order, "warranty_claim")

			if warranty_claim:
				update_fields = {
					"produced_qty": 1,
					"status": "Completed"
				}

				frappe.db.set_value("Production Order", {"warranty_claim": warranty_claim}, update_fields, val=None)
				frappe.db.commit()

				warranty_claim = frappe.get_doc("Warranty Claim", warranty_claim)
				if warranty_claim.status == "Repairing":
					warranty_claim.status = "To Deliver"
					warranty_claim.resolution_date = frappe.utils.now_datetime()
					warranty_claim.save()


def create_stock_entry(warranty_claim):
	to_warehouse = frappe.db.get_single_value("Repair Settings", "default_incoming_warehouse")
	serial_no = warranty_claim.serial_no or warranty_claim.unlinked_serial_no

	stock_entry = make_stock_entry(item_code=warranty_claim.item_code, qty=1,
									to_warehouse=to_warehouse, serial_no=serial_no,
									do_not_save=True)

	for item in stock_entry.items:
		item.warranty_claim = warranty_claim.name

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


def flush_raw_materials_for_repair(stock_entry, method):
	if method == "on_submit":
		new_se = frappe.new_doc("Stock Entry")
		consumption_warehouse = frappe.db.get_single_value("Repair Settings", "default_consumption_warehouse")

		new_se.update({
			"purpose": "Material Issue",
			"production_order": stock_entry.production_order,
			"from_bom": 1,
			"fg_completed_qty": 1,
			"from_warehouse": frappe.db.get_single_value("Repair Settings", "default_consumption_warehouse"),
			"reference_stock_entry": stock_entry.name
		})

		consumption_items = [item.as_dict() for item in stock_entry.items if item.t_warehouse == consumption_warehouse]

		if consumption_items:
			for c_item in consumption_items:
				c_item.s_warehouse = consumption_warehouse
				c_item.t_warehouse = None

			new_se.set("items", consumption_items)
			new_se.save()
			new_se.submit()
	elif method == "on_cancel":
		if stock_entry.purpose == "Material Transfer for Manufacture":
			existing_se = frappe.db.get_value("Stock Entry", filters={"reference_stock_entry": stock_entry.name})

			if existing_se:
				existing_se = frappe.get_doc("Stock Entry", existing_se)
				existing_se.cancel()
				existing_se.delete()


def make_mapped_doc(target_dt, source_dn, target_doc, target_cdt=None, filters=None,
					field_map=None, postprocess=None, child_postprocess=None, check_for_existing=True):
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
			"Warranty Claim Services": {
				"doctype": target_cdt,
				"field_map": field_map,
				"postprocess": child_postprocess
			}
		})

	# Multiple sales orders and stock entries can be made against Warranty Claim
	if check_for_existing:
		if frappe.get_all(target_dt, filters=filters):
			frappe.throw(_("A {0} document already exists for this request.".format(target_dt)))

	return get_mapped_doc("Warranty Claim", source_dn, table_map, target_doc, postprocess=postprocess)
