frappe.ui.form.on("Warranty Claim", {
	refresh: (frm) => {
		frm.add_fetch('item_code', 'item_group', 'item_group');
		frm.add_fetch('item_code', 'standard_rate', 'fee');

		frm.fields_dict.item_code.get_query = (doc, cdt, cdn) => {
			return {
				filters: {
					"item_group": ["in", ["Custom", "Full Retail", "Universal"]],
					"is_sales_item": 1
				}
			};
		};

		frm.fields_dict.cable.get_query = (doc, cdt, cdn) => {
			return {
				filters: {
					"item_group": "Cables",
					"is_sales_item": 1
				}
			};
		};

		frm.fields_dict.case.get_query = (doc, cdt, cdn) => {
			return { filters: { "item_group": "Cases" } };
		};

		frm.fields_dict.services.grid.get_field("item_code").get_query = (doc, cdt, cdn) => {
			return { filters: { "item_group": "Services" } };
		};

		if (!frm.doc.__islocal && frm.doc.status != "Completed") {
			// Receive the item from the customer
			if (!frm.doc.item_received) {
				frm.add_custom_button(__("Stock Receipt"), () => {
					frappe.call({
						method: "repairs.api.make_stock_entry_from_warranty_claim",
						args: {
							doc: frm.doc.name
						},
						callback: (r) => {
							if (!r.exc) {
								frm.set_value("received_date", frappe.datetime.now_datetime());
								frm.reload_doc();
							}
						}
					});
				}, __("Make"));
			};

			// Start testing the item
			if (frm.doc.status == "To Test") {
				var repair_btn = frm.add_custom_button(__("Test Item"), () => {
					frappe.prompt({
						label: __("Enter Results"),
						fieldname: "testing_details",
						fieldtype: "Text",
						reqd: 1
					}, (data) => {
						frm.set_value("status", "To Repair");
						frm.set_value("billing_status", frm.doc.is_under_warranty ? "Under Warranty" : "To Bill");
						frm.set_value("tested_by", frappe.session.user);
						frm.set_value("testing_date", frappe.datetime.now_datetime());
						frm.set_value("testing_details", data.testing_details);
						frm.save();
					}, __("Testing Results"), __("Record"));
				});
				repair_btn.addClass('btn-primary');
			};

			// Start the sales cycle for the customer
			if (frm.doc.billing_status == "To Bill") {
				frm.add_custom_button(__("Quotation"), () => {
					if (!frm.doc.services.length) {
						frappe.confirm(__("Do you want to create a Quotation without services?"), () => {
							frm.trigger("make_quotation");
						});
					} else {
						frm.trigger("make_quotation");
					};
				}, __("Make"));
			};

			// Start repairing the item
			if (frm.doc.status == "To Repair") {
				var repair_btn = frm.add_custom_button(__("Start Repair"), () => {
					frappe.model.open_mapped_doc({
						method: "repairs.api.start_repair",
						frm: frm,
						run_link_triggers: true
					});
				});
				repair_btn.addClass('btn-primary');
			};

			// Once repair is completed, make the delivery back to the customer
			if (!in_list(["To Receive", "Completed"], frm.doc.status) && frm.doc.billing_status != "To Bill") {
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

	item_received: function (frm) {
		if (frm.doc.item_received) {
			frm.set_value("status", "To Test");
		} else {
			frm.set_value("status", "To Receive");
		}
	},

	make_quotation: function (frm) {
		frappe.model.open_mapped_doc({
			method: "repairs.api.make_quotation",
			frm: frm,
			run_link_triggers: true
		});
	},
});
