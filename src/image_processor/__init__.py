"""
Image Processor - AI-powered image processing with metadata embedding and file renaming.

This package provides two main tools:
- image-processor-meta: Embeds AI-generated descriptions as XMP metadata
- image-processor-name: Renames images using AI-generated descriptive filenames

Both tools use Ollama's LLaVA model for computer vision analysis.
"""

__version__ = "2.1.0"
__author__ = "Shane Holloman"
__email__ = "contact@shaneholloman.com"

# Re-export main functionality from subtools
try:
    from image_processor_meta import main as meta_main
except ImportError:
    meta_main = None

try:
    from image_processor_name import main as name_main
except ImportError:
    name_main = None

__all__ = ["meta_main", "name_main", "__version__"]