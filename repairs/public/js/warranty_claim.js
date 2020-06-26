frappe.ui.form.on("Warranty Claim", {
	setup: (frm) => {
		frm.set_query('shipping_address', erpnext.queries.address_query);

		// triggers add fetch, sets value in model and runs triggers
		// ref to `trigger_link_fields` in form.js
		if (!frm.doc.address_display || !frm.doc.service_address) {
			$.each(frm.fields_dict, function (fieldname, field) {
				if (field.df.fieldtype == "Link" && frm.doc[fieldname]) {
					field.set_value(frm.doc[fieldname]);
				}
			});
		}
	},

	refresh: (frm) => {
		frm.add_fetch('item_code', 'item_group', 'item_group');

		if (!frm.doc.is_under_warranty) {
			frm.add_fetch('item_code', 'standard_rate', 'rate');
		};

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

		if (!frm.is_new() && frm.doc.status != "Completed") {
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

								frappe.db.get_value('Repair Settings', { name: 'Repair Settings' }, 'default_incoming_warehouse', (r) => {
									if (r.default_incoming_warehouse) {
										frappe.msgprint(__("The {0} was received in the {1} warehouse", [frm.doc.item_code, r.default_incoming_warehouse]));
									}
								});
							}
						}
					});
				}, __("Make"));
			};

			// Start testing the item
			if (frm.doc.status == "To Test") {
				let requires_scan = {
					left_ear: false,
					right_ear: false
				};

				for (let issue of frm.doc.issues) {
					frappe.db.get_value("Repair Issue Option", issue.issue_type, "is_3d_scan", (r) => {
						if (r && r.is_3d_scan) {
							requires_scan.left_ear = issue.left_ear;
							requires_scan.right_ear = issue.right_ear;
						}
					});
				}

				let test_btn = frm.add_custom_button(__("Test Item"), () => {
					fields = [
						{ fieldname: "sb_driver", fieldtype: "Section Break" },
						{ label: __("LEFT DRIVER"), fieldname: "cb_left_driver", fieldtype: "Column Break" },
						{ label: __("Low"), fieldname: "left_low_driver", fieldtype: "Check" },
						{ label: __("Mid"), fieldname: "left_mid_driver", fieldtype: "Check" },
						{ label: __("High"), fieldname: "left_high_driver", fieldtype: "Check" },
						{ label: __("RIGHT DRIVER"), fieldname: "cb_right_driver", fieldtype: "Column Break" },
						{ label: __("Low"), fieldname: "right_low_driver", fieldtype: "Check" },
						{ label: __("Mid"), fieldname: "right_mid_driver", fieldtype: "Check" },
						{ label: __("High"), fieldname: "right_high_driver", fieldtype: "Check" },

						{ fieldname: "sb_shell", fieldtype: "Section Break" },
						{ label: __("LEFT SHELL"), fieldname: "cb_left_shell", fieldtype: "Column Break" },
						{ label: __("Cracked"), fieldname: "left_cracked_shell", fieldtype: "Check" },
						{ label: __("Broken"), fieldname: "left_broken_shell", fieldtype: "Check" },
						{ label: __("Refit"), fieldname: "left_refit_shell", fieldtype: "Check" },
						{ label: __("Deep Clean"), fieldname: "left_clean_shell", fieldtype: "Check" },
						{ label: __("3D Scan"), fieldname: "left_scan_shell", fieldtype: "Check", "default": requires_scan.left_ear },
						{ label: __("RIGHT SHELL"), fieldname: "cb_right_shell", fieldtype: "Column Break" },
						{ label: __("Cracked"), fieldname: "right_cracked_shell", fieldtype: "Check" },
						{ label: __("Broken"), fieldname: "right_broken_shell", fieldtype: "Check" },
						{ label: __("Refit"), fieldname: "right_refit_shell", fieldtype: "Check" },
						{ label: __("Deep Clean"), fieldname: "right_clean_shell", fieldtype: "Check" },
						{ label: __("3D Scan"), fieldname: "right_scan_shell", fieldtype: "Check", "default": requires_scan.right_ear },

						{ fieldname: "sb_faceplate", fieldtype: "Section Break" },
						{ label: __("LEFT FACEPLATE"), fieldname: "cb_left_faceplate", fieldtype: "Column Break" },
						{ label: __("Cracked"), fieldname: "left_cracked_faceplate", fieldtype: "Check" },
						{ label: __("Broken"), fieldname: "left_broken_faceplate", fieldtype: "Check" },
						{ label: __("RIGHT FACEPLATE"), fieldname: "cb_right_faceplate", fieldtype: "Column Break" },
						{ label: __("Cracked"), fieldname: "right_cracked_faceplate", fieldtype: "Check" },
						{ label: __("Broken"), fieldname: "right_broken_faceplate", fieldtype: "Check" },

						{ fieldname: "sb_artwork", fieldtype: "Section Break" },
						{ label: __("LEFT ARTWORK"), fieldname: "cb_left_artwork", fieldtype: "Column Break" },
						{ label: __("Replacement"), fieldname: "left_artwork", fieldtype: "Check" },
						{ label: __("RIGHT ARTWORK"), fieldname: "cb_right_artwork", fieldtype: "Column Break" },
						{ label: __("Replacement"), fieldname: "right_artwork", fieldtype: "Check" },

						{ fieldname: "sb_socket", fieldtype: "Section Break" },
						{ label: __("LEFT SOCKET"), fieldname: "cb_left_socket", fieldtype: "Column Break" },
						{ label: __("Broken"), fieldname: "left_broken_socket", fieldtype: "Check" },
						{ label: __("Worn Out"), fieldname: "left_worn_out_socket", fieldtype: "Check" },
						{ label: __("Spinning / Loose"), fieldname: "left_loose_socket", fieldtype: "Check" },
						{ label: __("RIGHT SOCKET"), fieldname: "cb_right_socket", fieldtype: "Column Break" },
						{ label: __("Broken"), fieldname: "right_broken_socket", fieldtype: "Check" },
						{ label: __("Worn Out"), fieldname: "right_worn_out_socket", fieldtype: "Check" },
						{ label: __("Spinning / Loose"), fieldname: "right_loose_socket", fieldtype: "Check" },

						{ fieldname: "sb_others", fieldtype: "Section Break" },
						{ label: __("Cable Status"), fieldname: "cable_status", fieldtype: "Select", options: [null, "Good", "Bad"].join("\n") },
						{ label: __("Additional Results"), fieldname: "testing_details", fieldtype: "Small Text" }
					]

					frappe.prompt(fields, (data) => {
						let waitOnPromises = [];

						for (let result in data) {
							if (data[result]) {
								if (["cable_status", "testing_details"].includes(result)) {
									frm.set_value(result, data[result]);
								} else {
									waitOnPromises.push(get_suggested_service_for_result(frm, result));
								}
							}
						};

						Promise.all(waitOnPromises).then(() => {
							frm.set_value("status", "To Repair");
							frm.set_value("tested_by", frappe.session.user);
							frm.set_value("testing_date", frappe.datetime.now_datetime());
							frm.save();
						});
					}, __("Testing Results"), __("Record"));
				});
				test_btn.addClass('btn-primary');
			};

			// Start the sales cycle for the customer
			if (frm.doc.billing_status == "To Bill") {
				frm.add_custom_button(__("Quotation"), () => {
					if (!frm.doc.services.length && frm.doc.status != "To Receive") {
						frappe.confirm(__("Do you want to create a Quotation without services?"), () => {
							frm.trigger("make_quotation");
						});
					} else {
						frm.trigger("make_quotation");
					};
				}, __("Make"));

				frm.add_custom_button(__("Sales Order"), () => {
					if (!frm.doc.services.length && frm.doc.status != "To Receive") {
						frappe.confirm(__("Do you want to create a Sales Order without services?"), () => {
							frm.trigger("make_sales_order");
						});
					} else {
						frm.trigger("make_sales_order");
					};
				}, __("Make"));
			};

			// Start repairing the item
			if (frm.doc.status == "To Repair") {
				let repair_btn = frm.add_custom_button(__("Start Repair"), () => {
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

	shipping_address: function (frm) {
		erpnext.utils.get_address_display(frm, "shipping_address", "service_address");
	},

	make_quotation: function (frm) {
		frappe.model.open_mapped_doc({
			method: "repairs.api.make_quotation",
			frm: frm,
			run_link_triggers: true
		});
	},

	make_sales_order: function (frm) {
		frappe.model.open_mapped_doc({
			method: "repairs.api.make_sales_order",
			frm: frm,
			run_link_triggers: true
		});
	},
});

async function get_suggested_service_for_result(frm, result) {
	let [ear_side, service_desc, service_type] = result.split("_");

	// get suggested service item for the issue
	let item_code = "";
	if (service_desc == "scan") {
		let r = await frappe.db.get_value("Repair Settings", { "name": "Repair Settings" }, "default_3d_scan_item");
		item_code = r.message ? r.message.default_3d_scan_item : "";
	} else {
		let driver_type = service_type == "driver" ? service_desc : "";
		let r = await frappe.db.get_value("Item Service Default", {
			"parent": frm.doc.item_code,
			"service_type": service_type,
			"driver_type": driver_type
		}, "default_service_item");

		item_code = r.message ? r.message.default_service_item : "";
	}

	// get issue details
	let issue = [service_desc, service_type].join(" ");
	issue = issue[0].toUpperCase() + issue.slice(1);  // Capitalize
	ear_side = ear_side[0].toUpperCase() + ear_side.slice(1);  // Capitalize

	// add a row in the Testing Details table
	frm.add_child("services", {
		"issue": issue,
		"ear_side": ear_side,
		"item_code": item_code
	});
}
