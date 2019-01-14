import frappe


def stock_entry(doc, method):
	warranty_claims = [item.warranty_claim for item in doc.items if item.warranty_claim]
	warranty_claims = list(set(warranty_claims))

	for warranty_claim in warranty_claims:
		if method == "on_submit":
			if get_item_status(warranty_claim) == "To Receive":
				set_item_status(warranty_claim, "To Test")
		elif method == "on_cancel":
			if get_item_status(warranty_claim) == "To Test":
				set_item_status(warranty_claim, "To Receive")
			elif get_item_status(warranty_claim) == "To Deliver":
				set_item_status(warranty_claim, "Repairing")


def sales_invoice(doc, method):
	warranty_claims = [item.warranty_claim for item in doc.items if item.warranty_claim]
	warranty_claims = list(set(warranty_claims))

	for warranty_claim in warranty_claims:
		if method == "on_submit":
			if get_billing_status(warranty_claim) == "To Bill":
				set_billing_status(warranty_claim, "Unpaid")
		elif method == "on_cancel":
			if get_billing_status(warranty_claim) == "Unpaid":
				set_billing_status(warranty_claim, "To Bill")


def payment_entry(doc, method):
	def set_warranty_billing_status(warranty_claim, method):
		if method == "on_submit":
			if get_billing_status(warranty_claim) == "Unpaid":
				set_billing_status(warranty_claim, "Paid")
		elif method == "on_cancel":
			if get_billing_status(warranty_claim) == "Paid":
				set_billing_status(warranty_claim, "Unpaid")

	if doc.warranty_claim:
		set_warranty_billing_status(doc.warranty_claim, method)
	else:
		for ref in doc.references:
			ref_doc = frappe.get_doc(ref.reference_doctype, ref.reference_name)

			unique_claims = []
			for item in ref_doc.get("items", []):
				if item.warranty_claim and item.warranty_claim not in unique_claims:
					unique_claims.append(item.warranty_claim)

			for claim in unique_claims:
				set_warranty_billing_status(claim, method)


def production_order(doc, method):
	if doc.warranty_claim:
		if method == "on_submit":
			if get_item_status(doc.warranty_claim) == "To Repair":
				set_item_status(doc.warranty_claim, "Repairing")
		elif method == "on_cancel":
			if get_item_status(doc.warranty_claim) == "Repairing":
				set_item_status(doc.warranty_claim, "To Repair")


def dti_shipment_note(doc, method):
	delivery_note = frappe.get_doc("Delivery Note", doc.delivery_note)

	warranty_claims = [item.warranty_claim for item in delivery_note.items if item.warranty_claim]
	warranty_claims = list(set(warranty_claims))

	for warranty_claim in warranty_claims:
		if method == "on_submit":
			if get_item_status(warranty_claim) == "To Deliver":
				set_item_status(warranty_claim, "Completed")
		elif method == "on_cancel":
			if get_item_status(warranty_claim) == "Completed":
				set_item_status(warranty_claim, "To Deliver")


def get_item_status(dn):
	return frappe.db.get_value("Warranty Claim", dn, "status")


def get_billing_status(dn):
	return frappe.db.get_value("Warranty Claim", dn, "billing_status")


def set_item_status(dn, status):
	if frappe.db.exists("Warranty Claim", dn):
		doc = frappe.get_doc("Warranty Claim", dn)
		doc.status = status
		doc.save()
		frappe.db.commit()


def set_billing_status(dn, status):
	if frappe.db.exists("Warranty Claim", dn):
		doc = frappe.get_doc("Warranty Claim", dn)
		doc.billing_status = status
		doc.save()
		frappe.db.commit()
