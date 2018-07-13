import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc, map_child_doc


def match_existing_serial_no(doc, method):
	if not doc.unlinked_serial_no:
		return

	if doc.unlinked_serial_no in [serial_no.get("name") for serial_no in frappe.get_all("Serial No")]:
		doc.serial_no = doc.unlinked_serial_no


@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	def _set_fields(source_doc, target_doc, source_parent):
		target_doc.order_type = "Maintenance"

	existing_quotation = frappe.get_all("Quotation",
										filters={"warranty_claim": source_name,
												"docstatus": 1})

	if not existing_quotation:
		return get_mapped_doc("Warranty Claim", source_name, {
			"Warranty Claim": {
				"doctype": "Quotation",
				"field_map": {
					"warranty_claim": "name"
				},
				"postprocess": _set_fields
			},
		}, target_doc)


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):
	def _set_fields(source_doc, target_doc, source_parent):
		target_doc.purpose = "Material Receipt"
		target_doc.to_warehouse = frappe.db.get_single_value("Repair Settings", "default_incoming_warehouse")

	def _set_child_fields(source_doc, target_doc, source_parent):
		target_doc.qty = 1
		target_doc.uom = frappe.db.get_value("Item", source_doc.item_code, "stock_uom")
		target_doc.serial_no = source_doc.serial_no or source_doc.unlinked_serial_no

	existing_stock_entry = frappe.get_all("Stock Entry",
										filters={"warranty_claim": source_name,
												"docstatus": 1})

	if not existing_stock_entry:
		target_doc = get_mapped_doc("Warranty Claim", source_name, {
			"Warranty Claim": {
				"doctype": "Stock Entry",
				"field_map": {
					"warranty_claim": "name"
				},
				"postprocess": _set_fields
			}
		}, target_doc)

		source_doc = frappe.get_doc("Warranty Claim", source_name)
		if source_doc.get("item_code"):
			table_map = {
				"doctype": "Stock Entry Detail",
				"postprocess": _set_child_fields
			}
			map_child_doc(source_doc, target_doc, table_map, source_doc)

		return target_doc

	frappe.throw(_("Stock Receipt ({0}) has already been made.".format(existing_stock_entry[0].name)))


@frappe.whitelist()
def make_invoice(source_name, target_doc=None):
	existing_sales_invoice = frappe.get_all("Sales Invoice",
										filters={"warranty_claim": source_name,
												"docstatus": 1})

	if not existing_sales_invoice:
		return get_mapped_doc("Warranty Claim", source_name, {
			"Warranty Claim": {
				"doctype": "Sales Invoice",
				"field_map": {
					"warranty_claim": "name"
				}
			},
		}, target_doc)
