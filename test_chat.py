"""
测试通义千问 API 调用
使用方法: python test_api.py
"""

import os
import sys

# 检查环境变量
print("=" * 50)
print("1. 检查环境变量 DASHSCOPE_API_KEY")
print("=" * 50)

api_key = os.environ.get("DASHSCOPE_API_KEY")
if not api_key:
    print("❌ 未设置 DASHSCOPE_API_KEY 环境变量")
    print("\n请在终端设置:")
    print("  Windows: set DASHSCOPE_API_KEY=你的密钥")
    print("  或在代码中设置: os.environ['DASHSCOPE_API_KEY'] = '你的密钥'")
    sys.exit(1)
else:
    print(f"✅ API_KEY 已设置 (长度: {len(api_key)})")
    print(f"   前10位: {api_key[:10]}...")

# 测试 API 调用
print("\n" + "=" * 50)
print("2. 测试通义千问 API 调用")
print("=" * 50)

try:
    from dashscope import Generation
    
    # 构造消息
    messages = [
        {"role": "system", "content": "你是一个智能助手，请用简洁的中文回答问题。"},
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
    
    print("正在调用 qwen-max API...")
    
    response = Generation.call(
        model="qwen-max",
        messages=messages,
        result_format="message"
    )
    
    if response.status_code == 200:
        print("✅ API 调用成功!")
        print("\n回答内容:")
        print("-" * 30)
        print(response.output.choices[0].message.content)
        print("-" * 30)
    else:
        print(f"❌ API 调用失败")
        print(f"   状态码: {response.status_code}")
        print(f"   错误信息: {response.message}")

except ImportError as e:
    print(f"❌ 未安装 dashscope 库")
    print(f"   错误: {e}")
    print(f"\n请运行: pip install dashscope")
    
except Exception as e:
    print(f"❌ 调用失败: {e}")
    
print("\n" + "=" * 50)
print("测试完成")
print("=" * 50)