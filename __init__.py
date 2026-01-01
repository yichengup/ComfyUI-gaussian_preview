"""
ComfyUI Gaussian Preview - Standalone Gaussian Splatting Preview Node

Preview 3D Gaussian Splatting PLY files with interactive gsplat.js viewer.
"""

# 注册节点
from .nodes.visualization.preview_gaussian import (
    NODE_CLASS_MAPPINGS as PREVIEW_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as PREVIEW_DISPLAY_MAPPINGS
)
from .nodes.visualization.save_ply import (
    NODE_CLASS_MAPPINGS as SAVE_PLY_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as SAVE_PLY_DISPLAY_MAPPINGS
)

# 合并节点映射
NODE_CLASS_MAPPINGS = {}
NODE_CLASS_MAPPINGS.update(PREVIEW_MAPPINGS)
NODE_CLASS_MAPPINGS.update(SAVE_PLY_MAPPINGS)

NODE_DISPLAY_NAME_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS.update(PREVIEW_DISPLAY_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(SAVE_PLY_DISPLAY_MAPPINGS)

# 设置 web 目录
WEB_DIRECTORY = "./web"

# 导出给 ComfyUI
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
