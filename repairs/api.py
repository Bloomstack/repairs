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

	target_doc = make_mapped_doc("Quotation", source_name, target_doc, target_cdt="Quotation Item", postprocess=set_missing_values)

	for item in target_doc.items:
		item.qty = 1

	target_doc.save()

	return target_doc


@frappe.whitelist()
def start_repair(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.qty = 1

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
def finish_repair(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.purpose = "Material Issue"

	return make_mapped_doc("Stock Entry", source_name, target_doc, postprocess=set_missing_values, check_for_existing=False)


@frappe.whitelist()
def complete_production_order(doc):
	frappe.db.set_value("Production Order", {"warranty_claim": doc}, "status", "Completed")
	frappe.db.commit()


@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
	def _set_child_fields(source_doc, target_doc, source_parent):
		target_doc.update({
			"qty": 1,
			"uom": frappe.db.get_value("Item", source_doc.item_code, "stock_uom"),
			"serial_no": source_doc.serial_no or source_doc.unlinked_serial_no,
			"warehouse": frappe.db.get_single_value("Repair Settings", "default_incoming_warehouse"),
			"item_ignore_pricing_rule": 1,
			"allow_zero_valuation_rate": 1,
			"rate": 0,
			"additional_discount_percentage": 100
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
