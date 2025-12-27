"""
ComfyUI Gaussian Preview - Standalone Gaussian Splatting Preview Node

Preview 3D Gaussian Splatting PLY files with interactive gsplat.js viewer.
"""

# 注册节点
from .nodes.visualization.preview_gaussian import (
    NODE_CLASS_MAPPINGS, 
    NODE_DISPLAY_NAME_MAPPINGS
)

# 设置 web 目录
WEB_DIRECTORY = "./web"

# 导出给 ComfyUI
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']