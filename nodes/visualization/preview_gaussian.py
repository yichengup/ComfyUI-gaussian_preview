# revision author yichengup

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

# Fallback output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output") if COMFYUI_OUTPUT_FOLDER is None else None


class YCGaussianPreviewNode:
    """
    Preview Gaussian Splatting PLY files.

    Displays 3D Gaussian Splats in an interactive gsplat.js viewer
    with orbit controls and real-time rendering.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "ply_path": ("STRING", {
                    "forceInput": True,
                    "tooltip": "Path to a Gaussian Splatting PLY file (alternative to gaussians input)"
                }),
                "gaussians": ("GAUSSIANS_3D", {
                    "forceInput": True,
                    "tooltip": "Gaussians3D object from SHARP Predict (alternative to ply_path input)"
                }),
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

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("video_path", "save_ply_path",)
    OUTPUT_NODE = True
    FUNCTION = "preview_gaussian"
    CATEGORY = "gaussian_preview"
    
    # Make video output optional - if no video is found, return empty string
    # The connected node should handle empty string gracefully
    OUTPUT_IS_LIST = (False, False)
    
    @classmethod
    def IS_CHANGED(cls, ply_path=None, gaussians=None, **kwargs):
        """
        Force re-execution when a new video is recorded.
        Returns the modification time of the latest video file, or a hash of the PLY path/gaussians.
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
        
        # Fallback: return hash of PLY path or gaussians to ensure node executes at least once
        if ply_path:
            return hash(ply_path)
        elif gaussians is not None:
            # Hash the gaussians object (use id for now, could be improved)
            return id(gaussians)
        return None

    def preview_gaussian(self, ply_path=None, gaussians=None, extrinsics=None, intrinsics=None, preview_width=512):
        """
        Prepare PLY file for gsplat.js preview.

        Args:
            ply_path: Path to the Gaussian Splatting PLY file (optional if gaussians provided)
            gaussians: Gaussians3D object from SHARP Predict (optional if ply_path provided)
            extrinsics: Optional 4x4 camera extrinsics matrix
            intrinsics: Optional 3x3 camera intrinsics matrix
            preview_width: Preview window width in pixels (default: 512)

        Returns:
            dict: UI data for frontend widget
        """
        # Handle gaussians input - convert to PLY file first
        saved_ply_path = None
        if gaussians is not None:
            print("[YCGaussianPreview] Received Gaussians3D object, converting to PLY file...")
            ply_path = self._save_gaussians_to_ply(gaussians, extrinsics, intrinsics)
            if not ply_path:
                return {"ui": {"error": ["Failed to convert Gaussians3D to PLY file"]}}
            saved_ply_path = ply_path  # Store the saved path for output
        
        # Validate ply_path
        if not ply_path:
            print("[YCGaussianPreview] No PLY path or gaussians provided")
            return {"ui": {"error": ["No PLY path or gaussians provided"]}}

        if not os.path.exists(ply_path):
            print(f"[YCGaussianPreview] PLY file not found: {ply_path}")
            return {"ui": {"error": [f"File not found: {ply_path}"]}}
        
        # If ply_path was provided directly (not from gaussians conversion), use it as save_ply_path
        if saved_ply_path is None:
            saved_ply_path = ply_path

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
        
        # Return video_path and save_ply_path
        return {"ui": ui_data, "result": (video_path, saved_ply_path,)}
    
    def _save_gaussians_to_ply(self, gaussians, extrinsics=None, intrinsics=None):
        """
        Convert Gaussians3D object to PLY file.
        
        Args:
            gaussians: Gaussians3D object
            extrinsics: Optional camera extrinsics
            intrinsics: Optional camera intrinsics
            
        Returns:
            str: Path to saved PLY file, or None on error
        """
        try:
            # Import save_ply function from SHARP
            import sys
            import time
            from pathlib import Path
            
            # Try to find ComfyUI-Sharp plugin
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            sharp_path = os.path.join(current_dir, "ComfyUI-Sharp")
            
            if not os.path.exists(sharp_path):
                # Try alternative path
                sharp_path = os.path.join(os.path.dirname(current_dir), "ComfyUI-Sharp")
            
            if os.path.exists(sharp_path):
                if sharp_path not in sys.path:
                    sys.path.insert(0, sharp_path)
            
            from sharp.utils.gaussians import save_ply
            
            # Ensure output directory exists
            os.makedirs(COMFYUI_OUTPUT_FOLDER or OUTPUT_DIR, exist_ok=True)
            
            # Generate temporary filename
            timestamp = int(time.time() * 1000)
            output_filename = f"gaussian_preview_{timestamp}.ply"
            output_path = os.path.join(COMFYUI_OUTPUT_FOLDER or OUTPUT_DIR, output_filename)
            
            # Extract focal length and image size from intrinsics if available
            f_px = 512.0
            image_width = 1024
            image_height = 1024
            
            if intrinsics is not None:
                if isinstance(intrinsics, (list, tuple)) and len(intrinsics) >= 3:
                    if isinstance(intrinsics[0], (list, tuple)):
                        # 3x3 matrix format
                        f_px = float(intrinsics[0][0]) if intrinsics[0][0] else 512.0
                        image_width = int(intrinsics[0][2] * 2) if intrinsics[0][2] else 1024
                        image_height = int(intrinsics[1][2] * 2) if intrinsics[1][2] else 1024
                    else:
                        # Flat array format
                        f_px = float(intrinsics[0]) if len(intrinsics) > 0 else 512.0
            
            # Save PLY file
            print(f"[YCGaussianPreview] Saving temporary PLY file: {output_path}")
            _, metadata = save_ply(
                gaussians,
                f_px,
                (image_height, image_width),
                Path(output_path)
            )
            
            print(f"[YCGaussianPreview] Saved temporary PLY: {output_path} ({metadata['num_gaussians']:,} gaussians)")
            return output_path
            
        except ImportError as e:
            print(f"[YCGaussianPreview] Error: Failed to import save_ply from SHARP: {e}")
            print(f"[YCGaussianPreview] Make sure ComfyUI-Sharp is installed")
            return None
        except Exception as e:
            print(f"[YCGaussianPreview] Error converting Gaussians3D to PLY: {e}")
            import traceback
            traceback.print_exc()
            return None
    
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
