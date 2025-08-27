import random
import orjson
from loguru import logger
from mitmproxy import http, ctx

ali_proxy_hosts = {
    "group1": [
        "",  # 添加阿里云链接
    ],
    "group2": [
    ]
}

class MitmProxy:
    port = "9067"

    def __init__(self):
        self.pgen_cn = self._choice_proxy(ali_proxy_hosts['group1'])
        self.pgen_en = self._choice_proxy(ali_proxy_hosts['group2'])
        
        # 混合组
        mix_group = [host for group in ali_proxy_hosts.values() for host in group]
        random.shuffle(mix_group)
        self.pgen_all = self._choice_proxy(mix_group)
        
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
        print(f"mitmdump is running at 0.0.0.0:{MitmProxy.port} , tunnel_group: {ctx.options.group} ...")
    
    async def request(self, flow: http.HTTPFlow):
        original_req = {
            "url": flow.request.url,
            "method": flow.request.method,
            "headers": dict(flow.request.headers),
            "body": flow.request.content.decode(),
        }
        
        body = orjson.dumps(original_req)
        
        match ctx.options.group.upper():
            case "EN":
                proxy = next(self.pgen_cn)
            case "CN":
                proxy = next(self.pgen_en)
            case "ALL":
                proxy = next(self.pgen_all)
            case _:
                proxy = next(self.pgen_all)
        
        logger.info(f"[Request] {proxy} -> {original_req['url']}")
        flow.request.url = proxy
        flow.request.method = "POST"
        flow.request.headers = http.Headers(
            host=flow.request.host,
            content_type="application/json", 
        )
        flow.request.content = body
    
    async def response(self, flow: http.HTTPFlow):
        logger.info(f"[Response] {flow.response}")

    async def error(self, flow: http.HTTPFlow):
        logger.error(f"err, {flow.request.url}")


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
            "group=ALL"
        ]
    )
