import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ctx.load_cert_chain(
    r"C:\tbootit\data\auth\certificates\owner.crt",
    r"C:\tbootit\data\auth\certificates\owner.key"
)

# 1. Sale detail
req1 = urllib.request.Request("https://144.31.15.88/sales/1")
res1 = urllib.request.urlopen(req1, context=ctx)
content1 = res1.read().decode("utf-8", errors="replace")
print("=== /sales/1 ===")
print("Status:", res1.status)
print("Has 'Изменить продажу':", "Изменить продажу" in content1 or "openCorrectionModal" in content1)
print("Has 'История изменений':", "История изменений" in content1 or "История правок" in content1 or "revision" in content1.lower())

# 2. Repair detail
for rep_url in ["https://144.31.15.88/repairs/1", "https://144.31.15.88/repairs/repairs/1"]:
    try:
        req2 = urllib.request.Request(rep_url)
        res2 = urllib.request.urlopen(req2, context=ctx)
        content2 = res2.read().decode("utf-8", errors="replace")
        print(f"=== {rep_url} ===")
        print("Status:", res2.status)
        print("Has 'Выдать клиенту' / issue flow:", "Выдать" in content2 or "openIssueModal" in content2 or "issue" in content2.lower())
        print("Has receipt / warranty link:", "receipt" in content2 or "Квитанция" in content2 or "гарантия" in content2.lower())
        print("Has linked sale:", "Связанная продажа" in content2 or "sale_id" in content2 or "/sales/3" in content2)
    except Exception as e:
        print(f"{rep_url} -> {e}")

# 5. Check repair detail modal and issue controls
req_rep = urllib.request.Request("https://144.31.15.88/repairs/1")
res_rep = urllib.request.urlopen(req_rep, context=ctx)
html_rep = res_rep.read().decode("utf-8", errors="replace")

req_rec = urllib.request.Request("https://144.31.15.88/repairs/repairs/1/receipt")
res_rec = urllib.request.urlopen(req_rec, context=ctx)
html_rec = res_rec.read().decode("utf-8", errors="replace")
print("=== Repair Receipt Endpoint Check ===")
print("Status:", res_rec.status)
print("Receipt Content Length:", len(html_rec))
print("Has receipt text:", "Квитанция" in html_rec or "гаранти" in html_rec.lower() or "техноребут" in html_rec.lower())




