"""列出所有卖家，按GMV倒序"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.web.data import load_all_seller_ids, load_all_seller_history
from src.web.seller_analysis import safe_float

all_ids = load_all_seller_ids()
all_hist = load_all_seller_history()
results = []

for sid in all_ids:
    hist = all_hist.get(sid, [])
    if not hist:
        continue
    latest = hist[-1]
    site = "B2C"
    seller_name = ""
    seller_dir = os.path.join("data", "sku_analysis", sid)
    if os.path.exists(seller_dir):
        files = sorted([f for f in os.listdir(seller_dir) if f.endswith(".json")], reverse=True)
        if files:
            with open(os.path.join(seller_dir, files[0]), "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data.get("records", [])
                if records:
                    p = str(records[0].get("Platform", "")).lower()
                    if "ca" in p:
                        site = "CA"
                    elif "business" in p:
                        site = "B2B"
                    seller_name = records[0].get("SellerName", "")

    results.append({
        "sid": sid,
        "name": seller_name,
        "site": site,
        "gmv": safe_float(latest.get("GMV", 0)),
        "grade": latest.get("等级", "?"),
        "health": safe_float(latest.get("健康度评分", 0)),
        "rma": safe_float(latest.get("RMA%", 0)),
        "sku": safe_float(latest.get("SKU数", 0)),
    })

results.sort(key=lambda x: x["gmv"], reverse=True)
total = sum(r["gmv"] for r in results)

# 统计
by_site = {}
by_grade = {}
for r in results:
    by_site[r["site"]] = by_site.get(r["site"], 0) + 1
    by_grade[r["grade"]] = by_grade.get(r["grade"], 0) + 1

print(f"总计: {len(results)}个卖家, 总GMV: ${total:,.0f}")
print(f"站点: {', '.join(f'{k}={v}' for k, v in sorted(by_site.items()))}")
print(f"等级: {', '.join(f'{k}={v}' for k, v in sorted(by_grade.items()))}")
print()
print(f"{'#':>3}  {'SellerID':<8} {'SellerName':<42} {'站点':<4} {'GMV':>12}  {'等级':<4} {'健康度':>6} {'RMA%':>7} {'SKU':>4}")
print("-" * 105)

for i, r in enumerate(results, 1):
    name = r["name"][:40] if len(r["name"]) > 40 else r["name"]
    gmv_str = f"${r['gmv']:,.0f}"
    rma_str = f"{r['rma']:.2f}%"
    print(f"{i:>3}  {r['sid']:<8} {name:<42} {r['site']:<4} {gmv_str:>12}  {r['grade']:<4} {r['health']:>6.1f} {rma_str:>7} {r['sku']:>4.0f}")
