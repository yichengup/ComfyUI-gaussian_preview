"""
Save PLY node for ComfyUI-gaussian_preview.

Saves GAUSSIANS_3D objects to PLY files.
"""

import os
import time
from pathlib import Path

try:
    import folder_paths
    OUTPUT_DIR = folder_paths.get_output_directory()
except (ImportError, AttributeError):
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")


class SavePLYNode:
    """
    Save Gaussians3D object to PLY file.
    
    Takes a GAUSSIANS_3D object and saves it as a PLY file.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "ply_path": ("STRING", {
                    "forceInput": True,
                    "tooltip": "Path to existing PLY file (if provided, returns this path directly)"
                }),
                "gaussians": ("GAUSSIANS_3D", {
                    "forceInput": True,
                    "tooltip": "Gaussians3D object to save (alternative to ply_path input)"
                }),
                "extrinsics": ("EXTRINSICS", {
                    "tooltip": "Camera extrinsics (optional, used to extract metadata when saving from gaussians)"
                }),
                "intrinsics": ("INTRINSICS", {
                    "tooltip": "Camera intrinsics (optional, used to extract focal length and image size when saving from gaussians)"
                }),
                "output_prefix": ("STRING", {
                    "default": "gaussians",
                    "tooltip": "Prefix for output PLY filename (only used when saving from gaussians object)"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("ply_path",)
    FUNCTION = "save_ply"
    CATEGORY = "gaussian_preview"
    OUTPUT_NODE = True
    DESCRIPTION = "Save PLY file from either file path or Gaussians3D object. If ply_path is provided, returns it directly. If gaussians is provided, converts and saves to new file."

    def save_ply(
        self,
        ply_path=None,
        gaussians=None,
        extrinsics=None,
        intrinsics=None,
        output_prefix: str = "gaussians",
    ):
        """
        Save PLY file from path or Gaussians3D object.

        Args:
            ply_path: Path to existing PLY file (if provided, returns this path directly)
            gaussians: Gaussians3D object from SHARP Predict node (if provided, converts and saves)
            extrinsics: Camera extrinsics (optional, for metadata)
            intrinsics: Camera intrinsics (optional, used to extract focal length and image size)
            output_prefix: Prefix for output filename (only used when saving from gaussians)

        Returns:
            str: Path to PLY file
        """
        # If ply_path is provided, return it directly (no conversion needed)
        if ply_path:
            if os.path.exists(ply_path):
                print(f"[SavePLY] Using existing PLY file: {ply_path}")
                return (ply_path,)
            else:
                print(f"[SavePLY] Warning: PLY file not found: {ply_path}")
                print(f"[SavePLY] Falling back to gaussians conversion if available")
        
        # If gaussians is provided, convert and save
        if gaussians is not None:
            try:
                # Import save_ply function from SHARP
                import sys
                current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                sharp_path = os.path.join(current_dir, "ComfyUI-Sharp")
                
                if not os.path.exists(sharp_path):
                    # Try alternative path
                    sharp_path = os.path.join(os.path.dirname(current_dir), "ComfyUI-Sharp")
                
                if os.path.exists(sharp_path):
                    if sharp_path not in sys.path:
                        sys.path.insert(0, sharp_path)
                
                from sharp.utils.gaussians import save_ply
                
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
                
                # Ensure output directory exists
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                
                # Generate output filename
                timestamp = int(time.time() * 1000)
                output_filename = f"{output_prefix}_{timestamp}.ply"
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                
                # Save PLY file
                print(f"[SavePLY] Converting and saving Gaussians3D to: {output_path}")
                print(f"[SavePLY] Using metadata: f_px={f_px}, size={image_width}x{image_height}")
                _, metadata = save_ply(
                    gaussians,
                    f_px,
                    (image_height, image_width),
                    Path(output_path)
                )
                
                file_size = os.path.getsize(output_path)
                file_size_mb = file_size / (1024 * 1024)
                
                print(f"[SavePLY] Saved: {output_path}")
                print(f"[SavePLY] File size: {file_size_mb:.2f} MB")
                print(f"[SavePLY] Number of gaussians: {metadata['num_gaussians']:,}")
                
                return (output_path,)
                
            except ImportError as e:
                error_msg = f"Failed to import save_ply from SHARP: {e}"
                print(f"[SavePLY] Error: {error_msg}")
                print(f"[SavePLY] Make sure ComfyUI-Sharp is installed and accessible")
                return ("",)
            except Exception as e:
                error_msg = f"Error saving PLY file: {e}"
                print(f"[SavePLY] Error: {error_msg}")
                import traceback
                traceback.print_exc()
                return ("",)
        
        # If neither ply_path nor gaussians provided, return empty
        print("[SavePLY] Error: Neither ply_path nor gaussians provided")
        return ("",)


NODE_CLASS_MAPPINGS = {
    "SavePLY": SavePLYNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SavePLY": "Save PLY",
}

