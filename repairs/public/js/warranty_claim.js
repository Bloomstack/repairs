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

		if (!frm.doc.__islocal) {
			// Reopen and close the document
			if (frm.doc.status != "Closed") {
				frm.add_custom_button(__("Close"), () => {
					frm.set_value("previous_status", frm.doc.status);
					frm.set_value("status", "Closed");
					frm.save();
				});
			} else {
				frm.add_custom_button(__("Reopen"), () => {
					frm.set_value("status", frm.doc.previous_status);
					frm.save();
				});
			}

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
					frappe.model.open_mapped_doc({
						method: "repairs.api.make_quotation",
						frm: frm,
						run_link_triggers: true
					});
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

			// Finish repairing the item (with or without items)
			if (frm.doc.status == "Repairing") {
				var repair_btn = frm.add_custom_button(__("Finish Repair"), () => {
					var d = new frappe.ui.Dialog({
						title: __("Repair Results"),
						fields: [
							{
								label: __("With Items"),
								fieldname: "with_items",
								fieldtype: "Check",
								reqd: 0
							},
							{
								label: __("Enter Results"),
								fieldname: "resolution_details",
								fieldtype: "Text",
								reqd: 1
							}
						],
						primary_action: () => {
							var data = d.get_values();

							if (data.with_items) {
								frappe.model.open_mapped_doc({
									method: "repairs.api.finish_repair",
									frm: frm
								});
							}

							frappe.call({
								method: "repairs.api.complete_production_order",
								args: { doc: frm.doc.name },
								callback: (r) => {
									if (!r.exc) {
										frm.set_value("status", "To Deliver");
										frm.set_value("resolved_by", frappe.session.user);
										frm.set_value("resolution_date", frappe.datetime.now_datetime());
										frm.set_value("resolution_details", data.resolution_details);
										frm.save();

										d.hide();
									}
								}
							})
						},
						primary_action_label: __("Finish")
					});
					d.show();
				});
				repair_btn.addClass('btn-primary');
			};

			// Finally, make the delivery back to the customer
			if (!in_list(["To Receive", "Closed", "Completed"], frm.doc.status)) {
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
