# deploy_verify.py
import requests
import json

def verify_deployment():
    base_url = "http://localhost:8000"
    
    # 1. 基础健康检查
    r = requests.get(f"{base_url}/health")
    assert r.status_code == 200
    print("✅ 基础健康检查通过")
    
    # 2. 配置 watch 端点
    r = requests.get(f"{base_url}/health/config-watch")
    assert r.status_code == 200
    data = r.json()
    assert "connected" in data
    assert "metrics" in data
    print("✅ 配置 watch 端点正常")
    
    # 3. Prometheus 指标
    r = requests.get(f"{base_url}/metrics")
    assert r.status_code == 200
    assert "config_watch_" in r.text
    print("✅ Prometheus 指标暴露正常")
    
    # 4. 指标值合理性
    metrics = data["metrics"]
    assert metrics["connections_total"] >= 0
    assert metrics["disconnections_total"] >= 0
    assert metrics["load_failures"] >= 0
    print("✅ 指标值合理")
    
    print("\n🎉 部署验证全部通过!")

if __name__ == "__main__":
    verify_deployment()