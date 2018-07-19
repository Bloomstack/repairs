frappe.ui.form.on("Warranty Claim", {
	refresh: (frm) => {
		if (!frm.doc.__islocal) {
			if (!frm.doc.item_received) {
				frm.add_custom_button(__("Stock Receipt"), () => {
					frappe.call({
						method: "repairs.api.make_stock_entry_from_warranty_claim",
						args: {
							doc: frm.doc.name
						},
						callback: (r) => {
							if (r.message) {
								// frappe.msgprint(__("Stock Entry ({0}) created.", [r.message]));
								frm.save();
							}
						}
					});
				}, __("Make"));
			};

			if (frm.doc.status == "To Test") {
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
						primary_action: () => {
							var data = d.get_values();

							frm.set_value("status", frm.doc.is_paid ? "To Bill" : "To Repair");
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
			};

			if (frm.doc.status == "To Bill") {
				frm.add_custom_button(__("Quotation"), () => {
					frappe.model.open_mapped_doc({
						method: "repairs.api.make_quotation",
						frm: frm
					});
				}, __("Make"));
			};

			if (frm.doc.status == "To Repair") {
				frm.add_custom_button(__("Repair Item"), () => {
					frappe.model.open_mapped_doc({
						method: "repairs.api.make_production_order",
						frm: frm,
						run_link_triggers: true
					});
				});
			};

			if (frm.doc.status == "To Deliver") {
				frm.add_custom_button(__("Delivery"), () => {
					frappe.model.open_mapped_doc({
						method: "repairs.api.make_delivery_note",
						frm: frm,
						run_link_triggers: true
					});
				}, __("Make"));
			};
		}
	},
});
