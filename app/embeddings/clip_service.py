"""
CLIP Embedding Service
======================
Singleton service for converting images and text into vector embeddings using HuggingFace CLIP.
"""

from typing import List
import logging
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torch.nn.functional as F

from app.config import settings

logger = logging.getLogger(__name__)

class CLIPService:
    """Wraps HuggingFace CLIP model for image and text embedding."""
    
    def __init__(self):
        # Determine device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading CLIP model '{settings.CLIP_MODEL}' on device: {self.device}")
        
        # Load model and processor
        self.model = CLIPModel.from_pretrained(settings.CLIP_MODEL).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(settings.CLIP_MODEL)
        
    def embed_image(self, image_path: str) -> List[float]:
        """
        Open and encode an image into a normalized 512-dimensional vector.
        
        Args:
            image_path (str): The path to the image file.
            
        Returns:
            List[float]: A flat, L2-normalized list of floats representing the embedding.
        """
        try:
            # Open image and force to RGB (handles PNG transparency and grayscale)
            image = Image.open(image_path).convert("RGB")
        except FileNotFoundError:
            raise ValueError(f"Image not found: {image_path}")
        except Exception as e:
            raise ValueError(f"Error opening image {image_path}: {e}")
            
        # Process image
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        
        # Extract features
        with torch.no_grad():
            outputs = self.model.get_image_features(**inputs)
            # The projected features are stored in pooler_output if return_dict=True
            image_features = outputs.pooler_output if hasattr(outputs, 'pooler_output') else outputs
            
        # L2 Normalize so cosine similarity works correctly
        image_features = F.normalize(image_features, p=2, dim=-1)
        
        return image_features.cpu().numpy()[0].tolist()

    def embed_text_for_image_search(self, text: str) -> List[float]:
        """
        Encode text into a normalized 512-dimensional vector in the same space as the images.
        
        Args:
            text (str): The text query.
            
        Returns:
            List[float]: A flat, L2-normalized list of floats representing the embedding.
        """
        inputs = self.processor(text=[text], return_tensors="pt", truncation=True, max_length=77).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.get_text_features(**inputs)
            text_features = outputs.pooler_output if hasattr(outputs, 'pooler_output') else outputs
            
        # L2 Normalize
        text_features = F.normalize(text_features, p=2, dim=-1)
        
        return text_features.cpu().numpy()[0].tolist()
