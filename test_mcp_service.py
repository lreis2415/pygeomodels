#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP服务本地测试脚本
演示如何使用local_config.ini中的test_bearer_token进行测试
"""

import requests
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pygeomodels.config import parse_config


def test_with_test_token():
    """使用配置的测试token进行MCP服务测试"""

    # MCP服务端点
    MCP_URL = "http://127.0.0.1:8050/mcp"

    print("🔧 测试MCP服务...")
    print("=" * 50)

    # 1. 检查配置
    print("\n1️⃣ 检查测试token配置...")
    try:
        cfg = parse_config()
        test_token = cfg.test_bearer_token
        if test_token and test_token != "your_test_token_here":
            print(f"✅ 找到测试token: {test_token[:20]}...{test_token[-10:]}")
        else:
            print("❌ 未配置有效的测试token")
            print("请在 local_config.ini 中设置 test_bearer_token")
            return False
    except Exception as e:
        print(f"❌ 配置读取失败: {e}")
        return False

    # 2. 测试服务状态
    print("\n2️⃣ 测试服务状态...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {test_token}"
    }

    try:
        response = requests.get(f"{MCP_URL}/ready", headers=headers)
        if response.status_code == 200:
            print(f"✅ 服务状态: {response.json()}")
        else:
            print(f"❌ 服务状态异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        print("请确保MCP服务正在运行: python pygeomodels_service.py")
        return False

    # 3. 测试工具列表
    print("\n3️⃣ 测试MCP工具列表...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        response = requests.post(MCP_URL, headers=headers, json=payload)
        if response.status_code == 200:
            tools = response.json().get("result", {}).get("tools", [])
            print(f"✅ 可用工具数量: {len(tools)}")
            for tool in tools:
                print(f"   - {tool['name']}")
        else:
            print(f"❌ 获取工具列表失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    # 4. 测试具体工具调用
    print("\n4️⃣ 测试类别查询工具...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "list_categories",
                "arguments": {}
            }
        }
        response = requests.post(MCP_URL, headers=headers, json=payload)
        if response.status_code == 200:
            categories = response.json().get("result", [])
            print(f"✅ 模型类别: {categories}")
        else:
            print(f"❌ 工具调用失败: {response.status_code}")
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    # 5. 测试模型列表
    print("\n5️⃣ 测试模型列表工具...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "list_models",
                "arguments": {}
            }
        }
        response = requests.post(MCP_URL, headers=headers, json=payload)
        if response.status_code == 200:
            models = response.json().get("result", [])
            print(f"✅ 模型数量: {len(models)}")
            if models:
                print(f"   示例模型: {models[0].get('model_name', 'unknown')}")
        else:
            print(f"❌ 获取模型列表失败: {response.status_code}")
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    print("\n" + "=" * 50)
    print("🎉 测试完成！")
    return True


if __name__ == "__main__":
    print("""
    🚀 MCP服务本地测试工具

    使用前请确保：
    1. ✅ MCP服务正在运行: python pygeomodels_service.py
    2. ✅ local_config.ini 中配置了 test_bearer_token
    3. ✅ 相关的后端服务可以访问

    """)

    success = test_with_test_token()
    sys.exit(0 if success else 1)