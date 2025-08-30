# SCFTP
基于云函数的隧道代理 (Tunnel proxy based on Serverless Cloud Function)


### 工作流程
1. **初始化阶段**: 加载配置文件，初始化代理组，创建节点轮询生成器
2. **请求拦截**: 拦截用户 HTTP 请求，解析代理认证信息
3. **代理选择**: 根据代理用户名 `http://{user}:{pwd}@{host}:{port}` 随机选择对应的组中的代理节点
4. **请求转发**: 将原始请求封装为 JSON 格式，由云函数发起请求
5. **响应处理**: 接收云函数响应，返回给用户

### 代理组机制

- **ALL**: 默认组，包含所有可用节点
- **group1**: 国内代理组
- **group2**: 海外代理组
- 可继续添加组
- 


## QuickStart

### 环境要求

- Python 3.11+
- 支持的操作系统: Linux, macOS, Windows

### 安装依赖

```bash
# 使用 uv 包管理器（推荐）
uv sync
```

### 快速启动

1. **启动隧道代理服务**

```bash
cd tunnel_proxy
python tunnel_proxy.py
```

2. **测试连接**

```python
import requests

# 使用默认代理组
response = requests.get(
    "https://httpbin.org/ip", 
    proxy="http://127.0.0.1:9042", 
    verify=False
)
print(response.json())

# 使用指定代理组
# 通过代理账户名指定代理组
response = requests.get(
    "https://httpbin.org/ip", 
    proxy="http://group1:password@127.0.0.1:9042", 
    verify=False
)
print(response.json())
```

## Usage

### 配置说明

#### 主配置文件 (`config.yaml`)

```yaml
port: 9042  # 代理服务监听端口
default_group: ALL  # 默认代理组
```


### 注意事项

1. **取消 SSL 证书验证**: 必须设置 `verify=False` 或配置 mitmproxy 证书到系统信任证书中
2. **代理认证**: 用户名对应代理组名，密码可为任意值
3. **端口配置**: 默认监听 9042 端口，可在 `config.yaml` 中修改
