import yaml
import orjson
from loguru import logger
from mitmproxy import http, ctx

from proxy_base import ProxyBase


class TunnelProxyAddon(ProxyBase):
    """
    tunnel proxy addon
    """
    
    group_file = "proxy_groups.yaml"

    def __init__(self):
        super().__init__()

    def load_proxy(self) -> dict[str, list[str]]:
        with open(self.group_file, "r") as f:
            groups = yaml.safe_load(f)
        return groups
    
    def load(self, loader):
        loader.add_option(
            name="group",
            typespec=str,
            default=self.default_group,
            help="配置代理组",
        )

    def running(self):
        super().reload_proxy()
        
        group = ctx.options.group

        # 初始化代理生成器
        assert group in self.groups, f"代理组不存在: {group}"

        logger.info(
            f"---> mitmdump is running at 0.0.0.0:{self.config['port']}, default group: [{group}]..."
        )

    async def http_connect(self, flow: http.HTTPFlow):
        """根据Proxy-Authorization的用户名选择代理组"""
        proxy_auth = flow.request.headers.get("Proxy-Authorization", "")
        if proxy_auth:
            scheme, username, password = self.parse_http_basic_auth(proxy_auth)
            # todo: 验证密码
            self.group_name = username
        else:
            self.group_name = "ALL"

    async def request(self, flow: http.HTTPFlow):
        original_req = {
            "url": flow.request.url,
            "method": flow.request.method,
            "headers": dict(flow.request.headers),
            "body": flow.request.content.decode() if flow.request.content else None,
        }

        proxy = self.get_proxy(self.group_name)
        # todo: 若代理组不存在, 则取消请求, 返回自定义 response
        
        logger.info(f"[Request] {proxy} -> {original_req['url']}")

        flow.request.url = proxy
        flow.request.method = "POST"
        flow.request.headers = http.Headers(
            host=flow.request.host,
            content_type="application/json",
        )
        flow.request.content = orjson.dumps(original_req)

    async def response(self, flow: http.HTTPFlow):
        logger.info(f"[Response] {flow.response}")

    async def error(self, flow: http.HTTPFlow):
        logger.error(f"[Error] {flow.request.url}")


tpa = TunnelProxyAddon()
addons = [tpa]


if __name__ == "__main__":
    tpa.run_server()
