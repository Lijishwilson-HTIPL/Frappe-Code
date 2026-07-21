import frappe
def check():
    logs = frappe.get_all("Error Log", fields=["method", "error"], order_by="creation desc", limit=1)
    if logs:
        for log in logs:
            print("ERROR LOG:")
            print(log.error)
    else:
        print("No error logs found.")
