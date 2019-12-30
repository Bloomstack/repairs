// Copyright (c) 2018, DigiThinkIT, Inc. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Repair Settings', {
	setup: (frm) => {
		frm.set_query("default_3d_scan_item", () => {
			return { filters: { "item_group": "Services" } };
		});
	},

	refresh: (frm) => {
		frappe.call({
			method: "repairs.api.get_doctype_series",
			args: {
				doctype: "Sales Order"
			},
			callback: (r) => {
				if (!r.exc) {
					set_field_options("order_naming_series", r.message);
				}
			}
		});

		frappe.call({
			method: "repairs.api.get_doctype_series",
			args: {
				doctype: "Sales Invoice"
			},
			callback: (r) => {
				if (!r.exc) {
					set_field_options("invoice_naming_series", r.message);
				}
			}
		});

		frappe.call({
			method: "repairs.api.get_doctype_series",
			args: {
				doctype: "Production Order"
			},
			callback: (r) => {
				if (!r.exc) {
					set_field_options("production_naming_series", r.message);
				}
			}
		});
	}
});
