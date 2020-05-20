import frappe
from frappe.model.mapper import map_child_doc
from frappe.utils import flt

from .utils import create_stock_entry, make_mapped_doc


@frappe.whitelist()
def get_customer_claim_count(customer):
	status_check = ["NOT IN", ["Completed", "Offline", "Declined", "Cancelled"]]

	warranty_claims = frappe.get_all("Warranty Claim",
		filters={"customer": customer, "status": status_check})

	return {"count": len(warranty_claims)}


@frappe.whitelist()
def make_stock_entry_from_warranty_claim(doc):
	doc = frappe.get_doc("Warranty Claim", doc)
	stock_entry_name = create_stock_entry(doc)

	return stock_entry_name


@frappe.whitelist()
def get_doctype_series(doctype):
	return frappe.get_meta(doctype).get_field("naming_series").options or ""


@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.party_name = source.customer
		target.order_type = "Maintenance"
		target.set_onload("shipping_address_name", source.shipping_address)

		# Set item weights
		items = list(filter(None, [source.item_code, source.cable, source.case]))
		item_weights = frappe.get_all("Item", filters={"item_code": ["IN", items]}, fields=["sum(net_weight) AS total_weight"])
		target.total_net_weight = flt(target.total_net_weight) + item_weights[0].total_weight

	def set_item_details(source, target, source_parent):
		target.serial_no = source_parent.unlinked_serial_no or source_parent.serial_no
		target.uom = frappe.db.get_value("Item", source.item_code, "stock_uom")
		target.ear_side = source.ear_side

		# Set IEM Owner details
		if source_parent.iem_owner:
			target.iem_owner = source_parent.iem_owner
			target.designer_owner_first_name = frappe.db.get_value("IEM Owner", source_parent.iem_owner, "first_name")
			target.designer_owner_last_name = frappe.db.get_value("IEM Owner", source_parent.iem_owner, "last_name")
			target.designer_owner_email = source_parent.contact_email

		# Set item quantity based on number of ear sides
		if not source.ear_side or source.ear_side in ["Left", "Right"]:
			target.qty = 1
		elif source.ear_side == "Both":
			target.qty = 2

	return make_mapped_doc("Quotation", source_name, target_doc,
		target_cdt="Quotation Item", postprocess=set_missing_values,
		child_postprocess=set_item_details, check_for_existing=False)


@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.naming_series = frappe.db.get_single_value("Repair Settings", "order_naming_series")
		target.order_type = "Maintenance"
		target.set_onload("shipping_address_name", source.shipping_address)

		# Set item weights
		items = list(filter(None, [source.item_code, source.cable, source.case]))
		item_weights = frappe.get_all("Item", filters={"item_code": ["IN", items]}, fields=["sum(net_weight) AS total_weight"])
		target.total_net_weight = flt(target.total_net_weight) + item_weights[0].total_weight

	def set_item_details(source, target, source_parent):
		target.serial_no = source_parent.unlinked_serial_no or source_parent.serial_no
		target.uom = frappe.db.get_value("Item", source.item_code, "stock_uom")
		target.ear_side = source.ear_side

		# Set IEM Owner details
		if source_parent.iem_owner:
			target.iem_owner = source_parent.iem_owner
			target.designer_owner_first_name = frappe.db.get_value("IEM Owner", source_parent.iem_owner, "first_name")
			target.designer_owner_last_name = frappe.db.get_value("IEM Owner", source_parent.iem_owner, "last_name")
			target.designer_owner_email = source_parent.contact_email

		# Set item quantity based on number of ear sides
		if not source.ear_side or source.ear_side in ["Left", "Right"]:
			target.qty = 1
		elif source.ear_side == "Both":
			target.qty = 2

	return make_mapped_doc("Sales Order", source_name, target_doc,
		target_cdt="Sales Order Item", postprocess=set_missing_values,
		child_postprocess=set_item_details, check_for_existing=False)


@frappe.whitelist()
def start_repair(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.qty = 1
		target.serial_number = source.serial_no

	field_map = {
		"item_code": "production_item"
	}

	target_doc = make_mapped_doc("Production Order", source_name, target_doc, field_map=field_map, postprocess=set_missing_values)
	target_doc.update({
		"naming_series": frappe.db.get_single_value("Repair Settings", "production_naming_series") or target_doc.naming_series,
		"skip_transfer": 1
	})

	return target_doc


@frappe.whitelist()
def make_stock_entry_for_repair(production_order_id, repair_item, serial_no):
	production_order = frappe.get_doc("Production Order", production_order_id)
	stock_uom = frappe.db.get_value("Item", repair_item, "stock_uom")

	incoming_warehouse = frappe.db.get_single_value("Repair Settings", "default_incoming_warehouse")
	consumption_warehouse = frappe.db.get_single_value("Repair Settings", "default_consumption_warehouse")

	stock_entry = frappe.new_doc("Stock Entry")

	stock_entry.update({
		"purpose": "Material Transfer for Manufacture",
		"production_order": production_order_id,
		"from_bom": 1,
		"fg_completed_qty": 1,
		"from_warehouse": incoming_warehouse,
		"to_warehouse": consumption_warehouse
	})
	stock_entry.get_items()

	for item in stock_entry.items:
		item.t_warehouse = consumption_warehouse

	stock_entry.append("items", {
		"item_code": repair_item,
		"qty": 1,
		"uom": stock_uom,
		"stock_uom": stock_uom,
		"s_warehouse": incoming_warehouse,
		"t_warehouse": production_order.fg_warehouse,
		"warranty_claim": production_order.warranty_claim,
		"serial_no": serial_no
	})

	return stock_entry.as_dict()


@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
	def _set_child_fields(source_doc, target_doc, source_parent):
		target_doc.update({
			"qty": 1,
			"description": frappe.db.get_value("Item", source_doc.item_code, "description"),
			"uom": frappe.db.get_value("Item", source_doc.item_code, "stock_uom"),
			"serial_no": source_doc.serial_no or source_doc.unlinked_serial_no,
			"warehouse": frappe.db.get_value("Production Order", {"warranty_claim": source_doc.name}, "fg_warehouse")
		})

	target_doc = make_mapped_doc("Delivery Note", source_name, target_doc)
	source_doc = frappe.get_doc("Warranty Claim", source_name)

	# Include the cable and case in the stock receipt, if entered
	if source_doc.cable:
		target_doc.append("items", {
			"item_code": source_doc.cable,
			"qty": 1
		})

	if source_doc.case:
		target_doc.append("items", {
			"item_code": source_doc.case,
			"qty": 1
		})

	if source_doc.get("item_code"):
		table_map = {
			"doctype": "Delivery Note Item",
			"postprocess": _set_child_fields
		}
		map_child_doc(source_doc, target_doc, table_map, source_doc)

	return target_doc
