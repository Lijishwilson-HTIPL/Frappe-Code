import frappe

def run():
    for dt in ["Email Template","Notification","Newsletter","Web Form"]:
        try:
            meta = frappe.get_meta(dt)
        except Exception as e:
            print("skip", dt, e); continue
        fields = [f.fieldname for f in meta.fields if f.fieldtype in ("Text Editor","Long Text","Code","HTML Editor","Text","Small Text")]
        for fn in fields:
            try:
                rows = frappe.db.sql(f"SELECT name FROM `tab{dt}` WHERE `{fn}` LIKE %s LIMIT 5", ("%follow up personally%",), as_dict=True)
                if rows: print("HIT", dt, fn, rows)
            except Exception: pass
    # search all custom code fields
    for dt in ["Server Script","Scheduled Job Type","Hook"]:
        try:
            rows = frappe.db.sql(f"SHOW TABLES LIKE 'tab{dt}'")
            print(dt, "exists:", bool(rows))
        except: pass
    # inspect OAuth/integration/API keys set
    print("---api users---")
    for u in frappe.get_all("User", fields=["name","api_key"], filters={"api_key":["!=",""]}):
        print(u)
