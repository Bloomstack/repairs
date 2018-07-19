import frappe


def stock_entry(doc, method):
	if method == "on_submit":
		if doc.warranty_claim and frappe.db.get_value("Warranty Claim", doc.warranty_claim, "status") == "To Receive":
			update_status(doc.warranty_claim, "To Test")


def sales_invoice(doc, method):
	if method == "on_submit":
		if doc.warranty_claim and frappe.db.get_value("Warranty Claim", doc.warranty_claim, "status") == "To Bill":
			update_status(doc.warranty_claim, "Unpaid")


def payment_entry(doc, method):
	if method == "on_submit":
		if doc.warranty_claim and frappe.db.get_value("Warranty Claim", doc.warranty_claim, "status") == "Unpaid":
			update_status(doc.warranty_claim, "To Repair")


def production_order(doc, method):
	pass


def delivery_note(doc, method):
	pass


def dti_shipment_note(doc, method):
	pass


def update_status(dn, status):
	if frappe.db.exists("Warranty Claim", dn):
		doc = frappe.get_doc("Warranty Claim", dn)
		doc.status = status
		doc.save()
		frappe.db.commit()
