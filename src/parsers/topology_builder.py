"""网络拓扑构建器"""
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict


class TopologyBuilder:
    """网络拓扑关系构建器"""

    def __init__(self):
        self.nodes = []      # 节点列表
        self.edges = []      # 边列表 (from, to, properties)
        self.adjacency = defaultdict(list)  # 邻接表

    def add_node(self, node_id: str, node_type: str, properties: Dict = None):
        """添加节点"""
        node = {
            'id': node_id,
            'type': node_type,
            'properties': properties or {}
        }
        # 避免重复
        if not any(n['id'] == node_id for n in self.nodes):
            self.nodes.append(node)

    def add_edge(self, from_node: str, to_node: str, edge_type: str = '连接', properties: Dict = None):
        """添加边（连接关系）"""
        edge = {
            'from': from_node,
            'to': to_node,
            'type': edge_type,
            'properties': properties or {}
        }
        self.edges.append(edge)
        self.adjacency[from_node].append(to_node)

    def get_upstream(self, node_id: str) -> List[str]:
        """获取上游设备"""
        upstream = []
        for edge in self.edges:
            if edge['to'] == node_id:
                upstream.append(edge['from'])
        return upstream

    def get_downstream(self, node_id: str) -> List[str]:
        """获取下游设备"""
        return self.adjacency.get(node_id, [])

    def trace_route(self, from_node: str, to_node: str) -> List[str]:
        """追踪路由路径 (BFS)"""
        if from_node == to_node:
            return [from_node]

        visited = {from_node}
        queue = [(from_node, [from_node])]

        while queue:
            current, path = queue.pop(0)
            for next_node in self.adjacency.get(current, []):
                if next_node == to_node:
                    return path + [next_node]
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))

        return []  # 未找到路径

    def to_json(self) -> Dict[str, Any]:
        """导出为JSON格式"""
        return {
            'nodes': self.nodes,
            'edges': self.edges,
            'adjacency': dict(self.adjacency)
        }

    def to_csv_edges(self) -> List[Dict[str, Any]]:
        """导出边为CSV格式"""
        rows = []
        for edge in self.edges:
            rows.append({
                '起点': edge['from'],
                '终点': edge['to'],
                '连接类型': edge['type'],
                '属性': str(edge['properties'])
            })
        return rows