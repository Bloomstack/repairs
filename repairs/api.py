import frappe
from frappe.model.mapper import map_child_doc

from .utils import create_stock_entry, make_mapped_doc


@frappe.whitelist()
def make_stock_entry_from_warranty_claim(doc):
	doc = frappe.get_doc("Warranty Claim", doc)
	stock_entry_name = create_stock_entry(doc)

	return stock_entry_name


@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.order_type = "Maintenance"

	field_map = {"notes": "instructions"}

	target_doc = make_mapped_doc("Quotation", source_name, target_doc,
								target_cdt="Quotation Item", field_map=field_map,
								postprocess=set_missing_values, check_for_existing=False)
	source_doc = frappe.get_doc("Warranty Claim", source_name)

	items = []
	for idx, service in enumerate(source_doc.services):
		quotation_item_row = target_doc.items[idx]

		if quotation_item_row.item_code:
			if service.ear_side in ["Left", "Right"]:
				qty = 1
			elif service.ear_side == "Both":
				qty = 2
			else:
				qty = 0

			quotation_item_row.qty = qty
			items.append(quotation_item_row)

	target_doc.set("items", items)

	return target_doc


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
		"use_multi_level_bom": 0,
		"skip_transfer": 1
	})

	return target_doc


@frappe.whitelist()
def make_stock_entry_for_repair(production_order_id, repair_item, serial_no):
	production_order = frappe.get_doc("Production Order", production_order_id)
	stock_uom = frappe.db.get_value("Item", repair_item, "stock_uom")

	stock_entry = frappe.new_doc("Stock Entry")

	stock_entry.update({
		"purpose": "Material Transfer",
		"production_order": production_order_id,
		"warranty_claim": production_order.warranty_claim,
		"from_warehouse": frappe.db.get_single_value("Repair Settings", "default_incoming_warehouse"),
		"to_warehouse": production_order.fg_warehouse,
		"items": [{
			"item_code": repair_item,
			"qty": 1,
			"uom": stock_uom,
			"stock_uom": stock_uom,
			"serial_no": serial_no
		}]
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
