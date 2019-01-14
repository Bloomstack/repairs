// Copyright (c) 2018, DigiThinkIT, Inc. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Repair Settings', {
	refresh: function(frm) {
		frm.call({
			method: "repairs.api.get_order_series",
			callback: function (r) {
				if (!r.exc) {
					set_field_options("order_naming_series", r.message);
				}
			}
		});

		frm.call({
			method: "repairs.api.get_invoice_series",
			callback: function (r) {
				if (!r.exc) {
					set_field_options("invoice_naming_series", r.message);
				}
			}
		});
	}
});
