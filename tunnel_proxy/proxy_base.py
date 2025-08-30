import abc
import yaml
import random
import binascii
from loguru import logger
from typing import Generator

class ProxyBase(abc.ABC):
    config_path = "config.yaml"
    
    def __init__(self) -> None:
        self.config = self.__load_config()
        self.groups = {}
        self.default_group = self.config["default_group"]

    def reload_proxy(self):
        logger.info("---> 初始化代理组")
        proxies = self.load_proxy()
        self.groups = self.__init_proxy_group(proxies)
    
    @abc.abstractmethod
    def load_proxy(self) -> dict:
        pass
   
    def __load_config(self) -> dict:
        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f)
        return config

    def __init_proxy_group(self, groups:dict) -> dict[str, Generator[str, None, None]]:
        # 验证各组数据
        assert len(groups) > 0, "代理组为空"
        for group, info in groups.items():
            nodes = info.get("nodes")
            assert nodes and len(nodes) > 0, f"[{group}] 组中没有节点"
        
        # 创建默认组, 合并全部节点
        all_node = [
            node for node in groups.values() for node in node["nodes"]
        ]
        
        random.shuffle(all_node)  # 打乱节点
        
        if "ALL" not in groups:
            groups["ALL"] = {
                "nodes": all_node,
                "description": "全部节点",
            }
            
        # 创建节点组生成器
        groups_generated = {}
        for group, info in groups.items():
            nodes = info.get("nodes")
            groups_generated[group] = self.__choice_proxy(nodes)
            logger.info(f"[{group}] 节点数量:{len(info['nodes'])} [{info['description']}]")
        
        return groups_generated

    @staticmethod
    def parse_http_basic_auth(s: str) -> tuple[str, str, str]:
        """解析http basic auth, 返回(scheme, user, password)

        Args:
            s (str): Proxy-Authorization / Authorization 请求头

        Returns:
            tuple[str, str, str]: (scheme, user, password)
        """
        scheme, authinfo = s.split()
        if scheme.lower() != "basic":
            raise ValueError("Unknown scheme")
        try:
            user, password = (
                binascii.a2b_base64(authinfo.encode())
                .decode("utf8", "replace")
                .split(":")
            )
        except binascii.Error as e:
            raise ValueError(str(e))
        return scheme, user, password

    def __choice_proxy(self, hosts: list[str]) -> Generator[str, None, None]:
        """轮流切换代理"""
        n = 0
        length = len(hosts)
        while True:
            yield hosts[n]
            n = (n + 1) % length
            
    def get_proxy(self, group_name: str) -> str:
        """获取代理"""
        assert group_name in self.groups, f"代理组不存在: {group_name}"
        return next(self.groups[group_name])

    def run_server(self):
        import inspect
        from mitmproxy.tools.main import mitmdump
        
        logger.info(f"=====TUNNEL PROXY=====")
        script_file_path = inspect.getmodule(self.__class__).__file__  # 获取子类的文件路径
        mitmdump(
            [
                "-s",
                script_file_path,
                "-p",
                str(self.config["port"]),
                "-q",
                "--set",
                "block_global=false",
            ]
        )
