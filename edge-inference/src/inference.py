"""
YOLOv5-nano Inference Engine for Edge Deployment
Optimized for <100ms inference time and <10MB model size
"""
import torch
import time
from pathlib import Path
from typing import Dict, List, Any
import os


class InferenceError(Exception):
    """Base exception for inference errors"""
    pass


class ImageLoadError(InferenceError):
    """Raised when image cannot be loaded or is corrupted"""
    pass


class ModelInferenceError(InferenceError):
    """Raised when model inference fails"""
    pass


class InferenceEngine:
    """Lightweight inference engine using YOLOv5-nano"""

    def __init__(self, model_name: str = "yolov5n"):
        """
        Initialize inference engine

        Args:
            model_name: YOLOv5 model variant (default: yolov5n for nano)
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model(model_name)
        self.model_name = model_name

    def _load_model(self, model_name: str):
        """
        Load YOLOv5 model from torch hub

        Args:
            model_name: Model variant to load

        Returns:
            Loaded PyTorch model
        """
        model = torch.hub.load(
            'ultralytics/yolov5',
            model_name,
            pretrained=True,
            verbose=False
        )
        model.to(self.device)
        model.conf = 0.25  # Confidence threshold
        model.iou = 0.45   # IoU threshold
        model.max_det = 100  # Maximum detections
        return model

    def detect(self, image_path: str) -> Dict[str, Any]:
        """
        Run object detection on image

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with detections and metadata

        Raises:
            ImageLoadError: If image cannot be loaded or is corrupted
            ModelInferenceError: If inference fails
        """
        # Validate image file exists
        if not os.path.exists(image_path):
            raise ImageLoadError(f"Image file not found: {image_path}")

        start_time = time.time()

        try:
            # Run inference
            results = self.model(image_path)

            # Check if results are valid
            if results is None or not hasattr(results, 'pandas'):
                raise ModelInferenceError("Model returned invalid results")

            # Extract detections
            detections = results.pandas().xyxy[0].to_dict('records')

        except ImageLoadError:
            # Re-raise our custom exceptions
            raise
        except ModelInferenceError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Catch PIL/OpenCV image loading errors, corrupted files, etc.
            if "cannot identify image file" in str(e).lower() or "truncated" in str(e).lower():
                raise ImageLoadError(f"Failed to load image (possibly corrupted): {str(e)}")
            # Catch any other inference errors
            raise ModelInferenceError(f"Inference failed: {str(e)}")

        inference_time = (time.time() - start_time) * 1000  # Convert to ms

        # Format output
        try:
            formatted_detections = [
                {
                    "bbox": {
                        "xmin": float(det["xmin"]),
                        "ymin": float(det["ymin"]),
                        "xmax": float(det["xmax"]),
                        "ymax": float(det["ymax"])
                    },
                    "class": det["name"],
                    "confidence": float(det["confidence"]),
                    "class_id": int(det["class"])
                }
                for det in detections
            ]
        except (KeyError, ValueError) as e:
            raise ModelInferenceError(f"Failed to parse detection results: {str(e)}")

        return {
            "detections": formatted_detections,
            "count": len(formatted_detections),
            "inference_time_ms": round(inference_time, 2),
            "model": self.model_name
        }
