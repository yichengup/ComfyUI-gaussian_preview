# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 ComfyUI-GeometryPack Contributors

"""
Preview Gaussian Splatting PLY files with gsplat.js viewer.

Displays 3D Gaussian Splats in an interactive WebGL viewer.
"""

import os
import glob
from pathlib import Path

try:
    import folder_paths
    COMFYUI_OUTPUT_FOLDER = folder_paths.get_output_directory()
except (ImportError, AttributeError):
    COMFYUI_OUTPUT_FOLDER = None


class YCGaussianPreviewNode:
    """
    Preview Gaussian Splatting PLY files.

    Displays 3D Gaussian Splats in an interactive gsplat.js viewer
    with orbit controls and real-time rendering.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ply_path": ("STRING", {
                    "forceInput": True,
                    "tooltip": "Path to a Gaussian Splatting PLY file"
                }),
            },
            "optional": {
                "extrinsics": ("EXTRINSICS", {
                    "tooltip": "4x4 camera extrinsics matrix for initial view"
                }),
                "intrinsics": ("INTRINSICS", {
                    "tooltip": "3x3 camera intrinsics matrix for FOV"
                }),
                "preview_width": ("INT", {
                    "default": 512,
                    "min": 256,
                    "max": 4096,
                    "step": 64,
                    "tooltip": "Preview window width in pixels (affects recording resolution)"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    OUTPUT_NODE = True
    FUNCTION = "preview_gaussian"
    CATEGORY = "gaussian_preview"
    
    # Make video output optional - if no video is found, return empty string
    # The connected node should handle empty string gracefully
    OUTPUT_IS_LIST = (False,)
    
    @classmethod
    def IS_CHANGED(cls, ply_path, **kwargs):
        """
        Force re-execution when a new video is recorded.
        Returns the modification time of the latest video file, or a hash of the PLY path.
        """
        # Check for latest video file modification time
        if COMFYUI_OUTPUT_FOLDER:
            try:
                pattern = os.path.join(COMFYUI_OUTPUT_FOLDER, "gaussian-recording-*.mp4")
                video_files = glob.glob(pattern)
                if video_files:
                    # Sort by modification time, get the latest
                    video_files.sort(key=os.path.getmtime, reverse=True)
                    latest_video = video_files[0]
                    if os.path.isfile(latest_video):
                        # Return modification time - when a new video is recorded, this will change
                        return os.path.getmtime(latest_video)
            except Exception:
                pass
        
        # Fallback: return hash of PLY path to ensure node executes at least once
        return hash(ply_path) if ply_path else None

    def preview_gaussian(self, ply_path: str, extrinsics=None, intrinsics=None, preview_width=512):
        """
        Prepare PLY file for gsplat.js preview.

        Args:
            ply_path: Path to the Gaussian Splatting PLY file
            extrinsics: Optional 4x4 camera extrinsics matrix
            intrinsics: Optional 3x3 camera intrinsics matrix
            preview_width: Preview window width in pixels (default: 512)

        Returns:
            dict: UI data for frontend widget
        """
        if not ply_path:
            print("[YCGaussianPreview] No PLY path provided")
            return {"ui": {"error": ["No PLY path provided"]}}

        if not os.path.exists(ply_path):
            print(f"[YCGaussianPreview] PLY file not found: {ply_path}")
            return {"ui": {"error": [f"File not found: {ply_path}"]}}

        # Get just the filename for the frontend
        filename = os.path.basename(ply_path)

        # Check if file is in ComfyUI output directory
        if COMFYUI_OUTPUT_FOLDER and ply_path.startswith(COMFYUI_OUTPUT_FOLDER):
            # File is already in output folder, just use the filename
            relative_path = os.path.relpath(ply_path, COMFYUI_OUTPUT_FOLDER)
        else:
            # File is elsewhere - for now just use basename
            # The viewer will construct the full URL
            relative_path = filename

        # Get file size
        file_size = os.path.getsize(ply_path)
        file_size_mb = file_size / (1024 * 1024)

        print(f"[YCGaussianPreview] Loading PLY: {filename} ({file_size_mb:.2f} MB)")

        # Return metadata for frontend widget
        ui_data = {
            "ply_file": [relative_path],
            "filename": [filename],
            "file_size_mb": [round(file_size_mb, 2)],
        }

        # Add camera parameters if provided
        if extrinsics is not None:
            ui_data["extrinsics"] = [extrinsics]
        if intrinsics is not None:
            ui_data["intrinsics"] = [intrinsics]
        
        # Add preview width parameter
        ui_data["preview_width"] = [preview_width]

        # Find the latest recorded video in output directory
        video_path = self._find_latest_recorded_video()
        
        # If no video found, return empty string but log a warning
        # The connected node should validate the path before using it
        if not video_path:
            print("[YCGaussianPreview] Warning: No recorded video found. Please record a video first.")
            print("[YCGaussianPreview] The video_path output will be empty. Connect this output only after recording.")
        
        return {"ui": ui_data, "result": (video_path,)}
    
    def _find_latest_recorded_video(self):
        """
        Find the latest recorded video file in the output directory.
        
        Returns:
            str: Path to the latest recorded video file, or empty string if not found
        """
        if not COMFYUI_OUTPUT_FOLDER:
            print("[YCGaussianPreview] Output folder not available")
            return ""
        
        try:
            # Search for gaussian-recording-*.mp4 files in output directory
            pattern = os.path.join(COMFYUI_OUTPUT_FOLDER, "gaussian-recording-*.mp4")
            video_files = glob.glob(pattern)
            
            if not video_files:
                print("[YCGaussianPreview] No recorded video files found in output directory")
                print(f"[YCGaussianPreview] Searched pattern: {pattern}")
                print("[YCGaussianPreview] Please record a video first using the 'Start Record' button in the preview window")
                return ""
            
            # Sort by modification time, get the latest
            video_files.sort(key=os.path.getmtime, reverse=True)
            latest_video = video_files[0]
            
            # Verify the file exists and is readable
            if not os.path.isfile(latest_video):
                print(f"[YCGaussianPreview] Video file not found: {latest_video}")
                return ""
            
            # Return absolute path
            abs_path = os.path.abspath(latest_video)
            print(f"[YCGaussianPreview] Found latest recorded video: {os.path.basename(latest_video)}")
            print(f"[YCGaussianPreview] Video path: {abs_path}")
            return abs_path
            
        except Exception as e:
            print(f"[YCGaussianPreview] Error finding recorded video: {e}")
            import traceback
            traceback.print_exc()
            return ""


NODE_CLASS_MAPPINGS = {
    "YCGaussianPreview": YCGaussianPreviewNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "YCGaussianPreview": "Preview Gaussian",
}
