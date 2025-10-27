"""Stylesheet loader utility"""

import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_stylesheet(stylesheet_name: str) -> str:
    """
    Load stylesheet from resources/styles directory
    
    Args:
        stylesheet_name: Name of the stylesheet file (e.g., 'table_style.qss')
    
    Returns:
        Stylesheet content as string, empty string if file not found
    """
    try:
        # Get path to stylesheet
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_path = Path(getattr(sys, '_MEIPASS')) / "resources"
        else:
            base_path = Path(__file__).resolve().parent.parent.parent / "resources"

        style_path = base_path / "styles" / stylesheet_name
        
        if not style_path.exists():
            logger.warning(f"Stylesheet not found: {style_path}")
            return ""
        
        # Read and return stylesheet
        with open(style_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info(f"Loaded stylesheet: {stylesheet_name}")
            return content
            
    except Exception as e:
        logger.error(f"Error loading stylesheet {stylesheet_name}: {e}")
        return ""


def load_combined_stylesheets(*stylesheet_names: str) -> str:
    """
    Load and combine multiple stylesheets
    
    Args:
        *stylesheet_names: Variable number of stylesheet names
    
    Returns:
        Combined stylesheet content
    """
    combined = []
    
    for name in stylesheet_names:
        content = load_stylesheet(name)
        if content:
            combined.append(f"/* {name} */")
            combined.append(content)
            combined.append("")
    
    return "\n".join(combined)
