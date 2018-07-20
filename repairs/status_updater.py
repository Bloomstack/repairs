import frappe


def stock_entry(doc, method):
	if method == "on_submit":
		if doc.warranty_claim:
			if get_status(doc.warranty_claim) == "To Receive":
				set_status(doc.warranty_claim, "To Test")


def sales_invoice(doc, method):
	if method == "on_submit":
		if doc.warranty_claim:
			if get_status(doc.warranty_claim) == "To Bill":
				set_status(doc.warranty_claim, "Unpaid")


def payment_entry(doc, method):
	if method == "on_submit":
		if doc.warranty_claim:
			if get_status(doc.warranty_claim) == "Unpaid":
				set_status(doc.warranty_claim, "To Repair")


def production_order(doc, method):
	if method == "on_submit":
		if doc.warranty_claim:
			if get_status(doc.warranty_claim) in ["To Repair", "To Bill", "Unpaid"]:
				set_status(doc.warranty_claim, "Repairing")


def delivery_note(doc, method):
	pass


def dti_shipment_note(doc, method):
	pass


def get_status(dn):
	return frappe.db.get_value("Warranty Claim", dn, "status")


def set_status(dn, status):
	if frappe.db.exists("Warranty Claim", dn):
		doc = frappe.get_doc("Warranty Claim", dn)
		doc.status = status
		doc.save()
		frappe.db.commit()
