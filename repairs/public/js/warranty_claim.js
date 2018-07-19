frappe.ui.form.on("Warranty Claim", {
	refresh: (frm) => {
		if (!frm.doc.__islocal) {
			if (frm.doc.status == "Open") {  // "To Test"
				frm.add_custom_button(__("Test Item"), () => {
					var d = new frappe.ui.Dialog({
						title: __('Testing Results'),
						fields: [
							{
								"fieldname": "testing_details",
								"fieldtype": "Text",
								"reqd": 1
							}
						],
						primary_action: function () {
							var data = d.get_values();

							frm.set_value("tested_by", frappe.session.user);
							frm.set_value("testing_date", frappe.datetime.now_datetime());
							frm.set_value("testing_details", data.testing_details);
							frm.save();

							d.hide();
						},
						primary_action_label: __('Record')
					});
					d.show();
				});
			}

			if (frm.doc.status == "To Repair") {
				frm.add_custom_button(__("Repair Item"), () => {
					frappe.model.open_mapped_doc({
						method: "repairs.api.make_production_order",
						frm: frm,
						run_link_triggers: true
					});
				});
			};

			if (!frm.doc.serial_no || !frm.doc.item_received) {
				frm.add_custom_button(__("Stock Receipt"), () => {
					frappe.call({
						method: "repairs.api.make_stock_entry_from_warranty_claim",
						args: {
							doc: frm.doc.name
						},
						callback: (r) => {
							if (r.message) {
								// frappe.msgprint(__("Stock Entry ({0}) created.", [r.message]));
								frm.refresh();
							}
						}
					});
				}, __("Make"));
			};

			var methodMappings = {
				"Quotation": "make_quotation",
				"Delivery": "make_delivery_note"
			};

			Object.entries(methodMappings).forEach((mapping) => {
				var label = mapping[0];
				var method = mapping[1];

				frm.add_custom_button(__(`${label}`), () => {
					frappe.model.open_mapped_doc({
						method: `repairs.api.${method}`,
						frm: frm,
						run_link_triggers: true
					});
				}, __("Make"));
			});
		}
	},
});
