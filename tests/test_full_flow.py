#!/usr/bin/env python3
"""End-to-end test: extraction → approve → publish → dedup."""
import json
import time
import urllib.request
import urllib.error

BASE = "http://localhost:8080/api/v1/agent-config"

def api(method, path, data=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        try:
            return json.loads(body_text), e.code
        except Exception:
            return {"raw": body_text}, e.code
    except Exception as e:
        return {"error": str(e)}, 0

def main():
    print("=" * 60)
    print("FULL EXTRACTION FLOW TEST")
    print("=" * 60)

    # Step 0: Health check
    print("\n[0] Health check...")
    r, code = api("GET", "/health")
    assert code == 200, f"Backend not healthy: {r}"
    print(f"  ✅ Backend healthy (LLM: {r.get('llm', {}).get('model', '?')})")

    # Step 1: Check current queue
    print("\n[1] Current queue state...")
    r, code = api("GET", "/teams/build_system/skill-extract/queue")
    assert code == 200
    print(f"  Queue has {len(r)} items")
    for item in r:
        print(f"    {item['item_id'][:8]} {item.get('draft_name', '?'):35s} status={item['status']}")

    # Step 2: Start new extraction
    print("\n[2] Starting extraction with new text...")
    test_text = (
        "## Python Type Hints Best Practices\n\n"
        "When using type hints in Python projects:\n"
        "1. Always annotate function signatures with return types\n"
        "2. Use Optional[T] instead of T | None for Python 3.9 compatibility\n"
        "3. Use TypeVar for generic functions to preserve type information\n"
        "4. Prefer Protocol over ABC for structural subtyping\n"
        "5. Use TypedDict for dictionary-like objects with known keys\n"
        "6. Add py.typed marker file for PEP 561 compliance\n"
        "7. Run mypy or pyright in CI to catch type errors early\n"
        "8. Use Final for constants that should never be reassigned\n"
        "9. Annotate class variables with ClassVar\n"
        "10. Use Literal types for fixed string/int values"
    )
    r, code = api("POST", "/teams/build_system/skill-extract/start", {
        "source_text": test_text,
        "source_title": "Python类型注解最佳实践",
        "source_type": "document",
    })
    print(f"  HTTP {code}: item_id={r.get('item_id', '?')[:8]}, status={r.get('status', '?')}")
    item_id = r.get("item_id", "")

    if r.get("status") == "pending" or r.get("status") == "llm_prefilling":
        # Wait for LLM to finish
        print("  ⏳ Waiting for LLM prefill...")
        for i in range(60):
            time.sleep(2)
            r2, _ = api("GET", f"/teams/build_system/skill-extract/{item_id}")
            if r2 and r2.get("status") in ("ready_for_review", "error"):
                print(f"  ✅ LLM finished: status={r2['status']}, name={r2.get('draft_name', '?')}")
                break
            print(f"    ...still {r2.get('status', '?')} ({i*2}s)")
        else:
            print("  ❌ LLM prefill timed out after 120s")
            return

    # Step 3: Check queue after extraction
    print("\n[3] Queue after extraction...")
    r, code = api("GET", "/teams/build_system/skill-extract/queue")
    new_items = [i for i in r if i["status"] == "ready_for_review"]
    print(f"  Total: {len(r)}, ready_for_review: {len(new_items)}")
    for item in new_items:
        print(f"    {item['item_id'][:8]} {item.get('draft_name', '?'):35s} scope={item.get('draft_scope', '?')} conf={item.get('llm_confidence', 0):.0%}")

    if not new_items:
        print("  ⚠️ No items ready for review. Check if dedup kicked in or LLM failed.")
        # Show all items
        for item in r:
            print(f"    {item['item_id'][:8]} {item.get('draft_name', '?'):35s} status={item['status']}")
        return

    # Step 4: Approve the first ready item
    target = new_items[0]
    target_id = target["item_id"]
    print(f"\n[4] Approving: {target.get('draft_name', '?')} ({target_id[:8]})...")
    r, code = api("POST", f"/teams/build_system/skill-extract/{target_id}/approve", {
        "reviewer": "test_bot",
    })
    print(f"  HTTP {code}: status={r.get('status', '?')}")

    # Step 5: Check team skills
    print("\n[5] Team skills after approve...")
    r, code = api("GET", "/teams/build_system/skills")
    print(f"  Team has {len(r)} skills")
    for s in r:
        print(f"    {s.get('name', '?'):35s} slug={s.get('slug', '?')}")

    # Step 6: Try publish
    if target.get("draft_slug"):
        print(f"\n[6] Publishing: {target['draft_slug']}...")
        r, code = api("POST", "/skill-library/publish", {
            "team_id": "build_system",
            "skill_id": target["draft_slug"],
        })
        print(f"  HTTP {code}: {r}")
    else:
        print("\n[6] Skipping publish (no slug)")

    # Step 7: Dedup test - try same text again
    print("\n[7] Dedup test: submitting same text again...")
    r, code = api("POST", "/teams/build_system/skill-extract/start", {
        "source_text": test_text,
        "source_title": "Python类型注解最佳实践 (duplicate)",
        "source_type": "document",
    })
    print(f"  HTTP {code}: item_id={r.get('item_id', '?')[:8]}, status={r.get('status', '?')}")
    if r.get("status") != "pending":
        print(f"  ✅ Dedup worked! Returned existing item: {r.get('draft_name', '?')}")
    else:
        print(f"  ❌ Dedup failed! Created new item instead of returning existing")

    # Step 8: Reject a skill
    if len(new_items) > 1:
        reject_id = new_items[1]["item_id"]
        print(f"\n[8] Rejecting: {new_items[1].get('draft_name', '?')}...")
        r, code = api("POST", f"/teams/build_system/skill-extract/{reject_id}/reject", {
            "reviewer": "test_bot",
            "reason": "too generic for team",
        })
        print(f"  HTTP {code}: status={r.get('status', '?')}")
    else:
        print("\n[8] Skipping reject (only 1 item)")

    # Step 9: Final state
    print("\n[9] Final state...")
    r, code = api("GET", "/teams/build_system/skill-extract/queue")
    print(f"  Queue: {len(r)} items")
    for item in r[:8]:
        print(f"    {item['item_id'][:8]} {item.get('draft_name', '?'):35s} status={item['status']:20s} scope={item.get('draft_scope', '?')}")

    r, code = api("GET", "/teams/build_system/skills")
    print(f"  Team skills: {len(r)}")
    for s in r:
        print(f"    ✅ {s.get('name', '?')}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
