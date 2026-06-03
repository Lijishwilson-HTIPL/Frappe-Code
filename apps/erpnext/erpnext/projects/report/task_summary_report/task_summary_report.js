frappe.query_reports["Task Summary Report"] = {
	filters: [
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "assignee",
			label: __("Assignee"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nOpen\nWorking\nPending Review\nOverdue\nCompleted\nCancelled",
		},
		{
			fieldname: "priority",
			label: __("Priority"),
			fieldtype: "Select",
			options: "\nLow\nMedium\nHigh\nUrgent",
		},
		{
			fieldname: "from_date",
			label: __("From Date (Due)"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date (Due)"),
			fieldtype: "Date",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "days_overdue" && data && data.days_overdue > 0) {
			value = `<span style="color:#c53030;font-weight:600;">${data.days_overdue} days</span>`;
		}

		if (column.fieldname === "status" && data) {
			const colors = {
				"Open": "#e2e8f0",
				"Working": "#bee3f8",
				"Pending Review": "#fef3c7",
				"Overdue": "#fed7d7",
				"Completed": "#c6f6d5",
				"Cancelled": "#e2e8f0",
			};
			const textColors = {
				"Open": "#4a5568",
				"Working": "#2b6cb0",
				"Pending Review": "#92400e",
				"Overdue": "#c53030",
				"Completed": "#276749",
				"Cancelled": "#718096",
			};
			const bg = colors[data.status] || "#e2e8f0";
			const fg = textColors[data.status] || "#4a5568";
			value = `<span style="background:${bg};color:${fg};padding:2px 8px;border-radius:10px;font-size:11px;">${data.status}</span>`;
		}

		if (column.fieldname === "priority" && data && data.priority !== "—") {
			const colors = { Urgent: "#e53e3e", High: "#dd6b20", Medium: "#d69e2e", Low: "#38a169" };
			const fg = colors[data.priority];
			if (fg) value = `<span style="color:${fg};font-weight:600;">${data.priority}</span>`;
		}

		if (column.fieldname === "progress" && data) {
			const pct = data.progress || 0;
			const color = pct >= 100 ? "#38a169" : pct >= 50 ? "#d69e2e" : "#4490f1";
			value = `
				<div style="display:flex;align-items:center;gap:6px;">
					<div style="flex:1;height:6px;background:#e2e8f0;border-radius:3px;overflow:hidden;">
						<div style="width:${pct}%;height:100%;background:${color};border-radius:3px;"></div>
					</div>
					<span style="font-size:11px;color:#666;white-space:nowrap;">${pct}%</span>
				</div>`;
		}

		return value;
	},
};
