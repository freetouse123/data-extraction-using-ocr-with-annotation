"""
PDF Annotation Module
Creates annotated PDFs with hoverable text regions
"""

import fitz
from typing import List, Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class PdfAnnotator:
    """
    Add hoverable annotations to PDF based on OCR results
    """
    
    def __init__(self):
        self.annotation_color = (1, 1, 0.8)  # Light yellow highlight
        self.border_color = (0, 0, 1)  # Blue border
        self.text_color = (0, 0, 0)  # Black text
    
    def create_annotated_pdf(
        self, 
        pdf_bytes: bytes, 
        ocr_results: List[Dict],
        annotation_type: str = "popup",
        show_confidence: bool = True,
        dpi: int = 300
    ) -> bytes:
        """
        Create annotated PDF with hoverable regions
        
        Args:
            pdf_bytes: Original PDF bytes
            ocr_results: List of OCR results per page
            annotation_type: Type of annotation to add
            show_confidence: Whether to show confidence scores in popups
            dpi: DPI used during OCR (for coordinate scaling)
        
        Returns:
            Annotated PDF as bytes
        """
        logger.info("Creating annotated PDF")
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        scale_factor = 72 / dpi  # Convert from OCR coordinates to PDF coordinates
        
        for result in ocr_results:
            page_num = result['page_num']
            annotations = result['annotations']
            
            if page_num >= len(doc):
                logger.warning(f"Page {page_num} not found in document")
                continue
            
            page = doc[page_num]
            page_rect = page.rect
            
            for annotation in annotations:
                try:
                    self._add_annotation(
                        page=page,
                        annotation=annotation,
                        scale_factor=scale_factor,
                        page_rect=page_rect,
                        annotation_type=annotation_type,
                        show_confidence=show_confidence
                    )
                except Exception as e:
                    logger.warning(f"Failed to add annotation: {e}")
                    continue
        
        # Save to bytes
        annotated_bytes = doc.tobytes()
        doc.close()
        
        logger.info("Annotated PDF created successfully")
        return annotated_bytes
    
    def _add_annotation(
        self,
        page: fitz.Page,
        annotation: Dict,
        scale_factor: float,
        page_rect: fitz.Rect,
        annotation_type: str,
        show_confidence: bool
    ):
        """Add annotation to a specific text region"""
        
        bbox = annotation['bbox_pixels']
        text = annotation['text']
        confidence = annotation.get('confidence', 1.0)
        
        # Scale coordinates from OCR space to PDF space
        x0 = bbox['x'] * scale_factor
        y0 = bbox['y'] * scale_factor
        x1 = (bbox['x'] + bbox['width']) * scale_factor
        y1 = (bbox['y'] + bbox['height']) * scale_factor
        
        # Ensure coordinates are within page bounds
        x0 = max(0, min(x0, page_rect.width))
        y0 = max(0, min(y0, page_rect.height))
        x1 = max(0, min(x1, page_rect.width))
        y1 = max(0, min(y1, page_rect.height))
        
        rect = fitz.Rect(x0, y0, x1, y1)
        
        if rect.is_empty or rect.is_infinite:
            return
        
        if annotation_type in ["popup", "all"]:
            self._add_popup_annotation(page, rect, text, confidence, show_confidence)
        
        if annotation_type in ["highlight", "all"]:
            self._add_highlight_annotation(page, rect)
        
        if annotation_type in ["invisible_text", "all"]:
            self._add_invisible_text(page, rect, text)
        
        if annotation_type in ["underline"]:
            self._add_underline_annotation(page, rect, text, confidence, show_confidence)
        
        # Add word-level annotations if available
        if annotation_type == "words" and 'words' in annotation:
            for word in annotation['words']:
                word_bbox = word['bbox_pixels']
                word_rect = fitz.Rect(
                    word_bbox['x'] * scale_factor,
                    word_bbox['y'] * scale_factor,
                    (word_bbox['x'] + word_bbox['width']) * scale_factor,
                    (word_bbox['y'] + word_bbox['height']) * scale_factor
                )
                if not word_rect.is_empty:
                    self._add_popup_annotation(
                        page, word_rect, word['text'], 
                        word.get('confidence', 1.0), show_confidence
                    )
    
    def _add_popup_annotation(
        self, 
        page: fitz.Page, 
        rect: fitz.Rect, 
        text: str, 
        confidence: float,
        show_confidence: bool
    ):
        """Add a popup annotation (tooltip on hover)"""
        
        # Create popup content
        if show_confidence:
            popup_text = f"Text: {text}\nConfidence: {confidence:.2%}"
        else:
            popup_text = text
        
        try:
            # Method 1: Add a square/rect annotation with popup
            # This creates a hoverable region that shows content on click/hover
            annot = page.add_rect_annot(rect)
            annot.set_info(title="OCR Text", content=popup_text)
            annot.set_colors(stroke=(0, 0, 1))  # Blue border
            annot.set_border(width=0.5)
            annot.set_opacity(0.1)  # Nearly invisible but hoverable
            annot.update()
            
        except Exception as e:
            logger.debug(f"Rect annotation failed, trying alternative: {e}")
            try:
                # Method 2: Add text annotation (note icon)
                annot = page.add_text_annot(
                    point=rect.tl,
                    text=popup_text,
                    icon="Comment"
                )
                annot.update()
            except Exception as e2:
                logger.warning(f"Text annotation also failed: {e2}")
    
    def _add_highlight_annotation(self, page: fitz.Page, rect: fitz.Rect):
        """Add highlight annotation"""
        try:
            # Create quad points for highlight
            quad = rect.quad
            annot = page.add_highlight_annot(quad)
            annot.set_colors(stroke=(1, 1, 0))  # Yellow
            annot.set_opacity(0.3)
            annot.update()
        except Exception as e:
            logger.warning(f"Highlight annotation failed: {e}")
    
    def _add_underline_annotation(
        self, 
        page: fitz.Page, 
        rect: fitz.Rect,
        text: str,
        confidence: float,
        show_confidence: bool
    ):
        """Add underline annotation with popup"""
        try:
            quad = rect.quad
            annot = page.add_underline_annot(quad)
            annot.set_colors(stroke=(0, 0, 1))  # Blue underline
            
            if show_confidence:
                popup_text = f"Text: {text}\nConfidence: {confidence:.2%}"
            else:
                popup_text = text
            annot.set_info(title="OCR Text", content=popup_text)
            annot.update()
        except Exception as e:
            logger.warning(f"Underline annotation failed: {e}")
    
    def _add_invisible_text(self, page: fitz.Page, rect: fitz.Rect, text: str):
        """Add invisible but searchable/selectable text layer"""
        try:
            # Calculate font size based on rect height
            font_size = max(6, min(rect.height * 0.8, 12))
            
            # Add invisible text (for searchability)
            # render_mode=3 makes text invisible
            page.insert_text(
                point=(rect.x0, rect.y1 - 2),  # Bottom-left with small offset
                text=text,
                fontsize=font_size,
                fontname="helv",
                color=(1, 1, 1),  # White (invisible on white background)
                render_mode=3  # Invisible text mode
            )
        except Exception as e:
            logger.warning(f"Invisible text insertion failed: {e}")
    
    def create_interactive_pdf(
        self,
        pdf_bytes: bytes,
        ocr_results: List[Dict],
        dpi: int = 300
    ) -> bytes:
        """
        Create a fully interactive PDF with:
        - Hoverable text regions
        - Tooltips showing OCR text
        - Searchable text layer
        """
        logger.info("Creating interactive annotated PDF")
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        scale_factor = 72 / dpi
        
        for result in ocr_results:
            page_num = result['page_num']
            annotations = result['annotations']
            
            if page_num >= len(doc):
                continue
            
            page = doc[page_num]
            
            for annotation in annotations:
                bbox = annotation['bbox_pixels']
                text = annotation['text']
                confidence = annotation.get('confidence', 1.0)
                
                # Scale coordinates
                rect = fitz.Rect(
                    bbox['x'] * scale_factor,
                    bbox['y'] * scale_factor,
                    (bbox['x'] + bbox['width']) * scale_factor,
                    (bbox['y'] + bbox['height']) * scale_factor
                )
                
                if rect.is_empty or rect.is_infinite:
                    continue
                
                # Ensure rect is within page bounds
                page_rect = page.rect
                rect = rect & page_rect  # Intersection with page
                
                if rect.is_empty:
                    continue
                
                try:
                    # Add hoverable rectangle annotation with popup
                    popup_text = f"OCR Text: {text}\nConfidence: {confidence:.2%}"
                    
                    # Create a polygon/polyline annotation for the text region
                    annot = page.add_rect_annot(rect)
                    annot.set_info(
                        title="OCR Detection",
                        content=popup_text,
                        subject="Detected Text"
                    )
                    annot.set_colors(stroke=(0, 0.5, 1))  # Light blue border
                    annot.set_border(width=0.5, dashes=[2, 2])  # Dashed border
                    annot.set_opacity(0.15)
                    annot.update()
                    
                    # Add invisible text for searchability
                    self._add_invisible_text(page, rect, text)
                    
                except Exception as e:
                    logger.warning(f"Failed to add interactive annotation: {e}")
                    continue
        
        annotated_bytes = doc.tobytes()
        doc.close()
        
        logger.info("Interactive PDF created successfully")
        return annotated_bytes
    
    def create_searchable_pdf(
        self,
        pdf_bytes: bytes,
        ocr_results: List[Dict],
        dpi: int = 300,
        add_highlights: bool = False
    ) -> bytes:
        """
        Create a searchable PDF with invisible text layer.
        Optionally add subtle highlights over detected text.
        """
        logger.info("Creating searchable PDF")
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        scale_factor = 72 / dpi
        
        for result in ocr_results:
            page_num = result['page_num']
            annotations = result['annotations']
            
            if page_num >= len(doc):
                continue
            
            page = doc[page_num]
            
            for annotation in annotations:
                bbox = annotation['bbox_pixels']
                text = annotation['text']
                
                rect = fitz.Rect(
                    bbox['x'] * scale_factor,
                    bbox['y'] * scale_factor,
                    (bbox['x'] + bbox['width']) * scale_factor,
                    (bbox['y'] + bbox['height']) * scale_factor
                )
                
                if rect.is_empty or rect.is_infinite:
                    continue
                
                # Add invisible text
                self._add_invisible_text(page, rect, text)
                
                # Optionally add subtle highlight
                if add_highlights:
                    try:
                        annot = page.add_highlight_annot(rect.quad)
                        annot.set_opacity(0.1)
                        annot.update()
                    except:
                        pass
        
        annotated_bytes = doc.tobytes()
        doc.close()
        
        logger.info("Searchable PDF created successfully")
        return annotated_bytes


class PdfAnnotatorSimple:
    """
    Simplified PDF Annotator - More compatible with different PyMuPDF versions
    """
    
    def __init__(self):
        pass
    
    def create_annotated_pdf(
        self,
        pdf_bytes: bytes,
        ocr_results: List[Dict],
        dpi: int = 300,
        annotation_style: str = "box"  # "box", "highlight", "underline"
    ) -> bytes:
        """
        Create annotated PDF with simple, compatible annotations
        """
        logger.info("Creating annotated PDF (simple mode)")
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        scale_factor = 72 / dpi
        
        for result in ocr_results:
            page_num = result['page_num']
            annotations = result['annotations']
            
            if page_num >= len(doc):
                continue
            
            page = doc[page_num]
            page_rect = page.rect
            
            for annotation in annotations:
                bbox = annotation['bbox_pixels']
                text = annotation['text']
                confidence = annotation.get('confidence', 1.0)
                
                # Calculate scaled rectangle
                x0 = bbox['x'] * scale_factor
                y0 = bbox['y'] * scale_factor
                x1 = (bbox['x'] + bbox['width']) * scale_factor
                y1 = (bbox['y'] + bbox['height']) * scale_factor
                
                # Clamp to page bounds
                x0 = max(0, min(x0, page_rect.width - 1))
                y0 = max(0, min(y0, page_rect.height - 1))
                x1 = max(x0 + 1, min(x1, page_rect.width))
                y1 = max(y0 + 1, min(y1, page_rect.height))
                
                rect = fitz.Rect(x0, y0, x1, y1)
                
                if rect.is_empty:
                    continue
                
                popup_content = f"Text: {text}\nConfidence: {confidence:.1%}"
                
                try:
                    if annotation_style == "box":
                        # Simple rectangle annotation
                        annot = page.add_rect_annot(rect)
                        annot.set_info(content=popup_content)
                        annot.set_colors(stroke=(0, 0, 1))
                        annot.set_opacity(0.2)
                        annot.update()
                        
                    elif annotation_style == "highlight":
                        # Highlight annotation
                        annot = page.add_highlight_annot(rect.quad)
                        annot.set_info(content=popup_content)
                        annot.set_opacity(0.25)
                        annot.update()
                        
                    elif annotation_style == "underline":
                        # Underline annotation  
                        annot = page.add_underline_annot(rect.quad)
                        annot.set_info(content=popup_content)
                        annot.update()
                        
                except Exception as e:
                    logger.debug(f"Annotation failed for '{text[:20]}...': {e}")
                    continue
        
        output_bytes = doc.tobytes()
        doc.close()
        
        logger.info("Annotated PDF created successfully")
        return output_bytes