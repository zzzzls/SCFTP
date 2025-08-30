import random
import orjson
from loguru import logger
from mitmproxy import http, ctx
import yaml


# todo: 拆分mitmproxy 和 addon 功能

class MitmProxy:
    port = "9067"
    config_path = "config.yaml"

    def __init__(self):
        self.config = self._load_config()
        self.proxies = self.config['proxies']
        print(self.proxies)
        
        self.proxy_generator = None
        
    def _load_config(self):
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
        
    def _choice_proxy(self, hosts:list[str]):
        """轮流切换代理"""
        n = 0
        length = len(hosts)
        while True:
            yield hosts[n]
            n = (n+1) % length
    
    def load(self, loader):
        loader.add_option(
            name="group",
            typespec=str,
            default="ALL",
            help="配置代理组(CN:国内组, EN:国外组, ALL:混合组)",
        )
        
    def running(self):
        group = ctx.options.group
        
        # 初始化代理生成器
        assert group != "ALL" and group not in self.proxies, f"代理组不存在: {group}"
        if group == "ALL":
            nodes = [node for group in self.proxies.values() for node in group['nodes']]
            description = "混合组"
        else:
            nodes = self.proxies[group]['nodes']
            description = self.proxies[group]['description']
            
        self.proxy_generator = self._choice_proxy(nodes)
            
        logger.info(f"mitmdump is running at 0.0.0.0:{MitmProxy.port} , tunnel_group: {group} [{description}]...")
    
    async def request(self, flow: http.HTTPFlow):
        original_req = {
            "url": flow.request.url,
            "method": flow.request.method,
            "headers": dict(flow.request.headers),
            "body": flow.request.content.decode(),
        }
        
        proxy = next(self.proxy_generator)
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


addons = [MitmProxy()]


if __name__ == "__main__":
    from mitmproxy.tools.main import mitmdump
    mitmdump(
        [
            "-s",
            __file__,
            "-p",
            MitmProxy.port,
            "-q",
            "--set",
            "block_global=false"
        ]
    )
