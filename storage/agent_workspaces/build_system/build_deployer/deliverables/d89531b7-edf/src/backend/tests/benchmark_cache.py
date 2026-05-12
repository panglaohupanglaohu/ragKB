# src/backend/tests/benchmark_cache.py
import time
import requests
import statistics

BASE_URL = "http://localhost:8001"

def benchmark_scenario(scenario_name, requests_list):
    """运行基准测试并收集指标"""
    results = []
    for req in requests_list:
        start = time.time()
        try:
            resp = requests.post(
                f"{BASE_URL}/api/v1/chat",
                json=req,
                timeout=30
            )
            latency = time.time() - start
            results.append({
                "success": resp.status_code == 200,
                "latency": latency,
                "cached": resp.headers.get("X-Cache-Hit", "false") == "true"
            })
        except Exception as e:
            results.append({
                "success": False,
                "latency": time.time() - start,
                "error": str(e)
            })
    
    # 计算统计
    latencies = [r["latency"] for r in results if r["success"]]
    return {
        "scenario": scenario_name,
        "total_requests": len(results),
        "success_count": sum(1 for r in results if r["success"]),
        "success_rate": sum(1 for r in results if r["success"]) / len(results) * 100,
        "avg_latency": statistics.mean(latencies) if latencies else 0,
        "p50_latency": statistics.median(latencies) if latencies else 0,
        "p95_latency": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
        "cache_hit_count": sum(1 for r in results if r.get("cached")),
        "cache_hit_rate": sum(1 for r in results if r.get("cached")) / len(results) * 100,
        "estimated_cost_saved": sum(1 for r in results if r.get("cached")) * 0.002  # $0.002 per cached call
    }

# 运行基准测试
if __name__ == "__main__":
    # 场景1: 首次调用
    scenario1 = [{"messages": [{"role": "user", "content": "Hello"}], "model": "deepseek-chat"}]
    
    # 场景2: 重复调用
    scenario2 = scenario1 * 10
    
    # 场景3: 不同参数
    scenario3 = [
        {"messages": [{"role": "user", "content": "Hello"}], "model": "deepseek-chat", "temperature": 0.1},
        {"messages": [{"role": "user", "content": "Hello"}], "model": "deepseek-chat", "temperature": 0.9},
    ]
    
    # 场景4: 混合
    scenario4 = [
        {"messages": [{"role": "user", "content": "What is AI?"}], "model": "deepseek-chat"},
        {"messages": [{"role": "user", "content": "What is AI?"}], "model": "deepseek-chat"},
        {"messages": [{"role": "user", "content": "Explain Python"}], "model": "deepseek-chat"},
        {"messages": [{"role": "user", "content": "Explain Python"}], "model": "deepseek-chat"},
    ]
    
    results = []
    for name, reqs in [("首次调用", scenario1), ("重复调用", scenario2), 
                        ("不同参数", scenario3), ("混合负载", scenario4)]:
        result = benchmark_scenario(name, reqs)
        results.append(result)
        print(f"\n=== {name} ===")
        print(f"成功率: {result['success_rate']:.1f}%")
        print(f"平均时延: {result['avg_latency']*1000:.1f}ms")
        print(f"缓存命中率: {result['cache_hit_rate']:.1f}%")
        print(f"预估节省: ${result['estimated_cost_saved']:.4f}")
    
    # 输出对比表格
    print("\n\n## 对比数据总结")
    print("| 场景 | 成功率 | 平均时延 | 缓存命中率 | 预估节省 |")
    print("|------|--------|----------|------------|----------|")
    for r in results:
        print(f"| {r['scenario']} | {r['success_rate']:.1f}% | {r['avg_latency']*1000:.1f}ms | {r['cache_hit_rate']:.1f}% | ${r['estimated_cost_saved']:.4f} |")