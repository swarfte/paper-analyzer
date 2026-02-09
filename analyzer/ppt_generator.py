"""
PowerPoint Generator Service for Paper Analyzer

This service generates PowerPoint presentations from analyzed research papers,
following academic presentation standards with proper formatting and structure.
"""

import os
from typing import Dict, Any, Optional, Tuple
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import nsmap
import re


class PowerPointGenerator:
    """
    Generate PowerPoint presentations from paper analysis data.

    Creates professional academic presentations with:
    - Cover slide with paper metadata and student info
    - Introduction/Related Work
    - Motivation
    - Main Idea & Framework
    - Methodology
    - Experiments & Results
    - Conclusion & Future Work
    """

    # Color scheme (professional academic blue theme)
    PRIMARY_COLOR = RGBColor(0, 51, 102)      # Dark blue
    SECONDARY_COLOR = RGBColor(0, 102, 204)   # Medium blue
    ACCENT_COLOR = RGBColor(204, 51, 0)       # Accent red
    TEXT_COLOR = RGBColor(51, 51, 51)         # Dark gray
    LIGHT_GRAY = RGBColor(240, 240, 240)      # Light gray for backgrounds

    def __init__(self, analysis_data: Dict[str, Any], metadata: Dict[str, Any]):
        """
        Initialize the PowerPoint generator.

        Args:
            analysis_data: Dictionary containing paper analysis results
            metadata: Dictionary containing paper metadata (title, authors, venue, etc.)
        """
        self.analysis_data = analysis_data
        self.metadata = metadata
        self.prs = Presentation()
        self.prs.slide_width = Inches(10)
        self.prs.slide_height = Inches(7.5)

    def generate(self) -> Presentation:
        """
        Generate the complete PowerPoint presentation.

        Returns:
            Presentation: The complete PowerPoint presentation object
        """
        # 1. Cover slide
        self._add_cover_slide()

        # 2. Introduction/Related Work
        self._add_introduction_slide()

        # 3. Motivation
        self._add_motivation_slide()

        # 4. Main Idea & Framework
        self._add_main_idea_slide()

        # 5. Methodology (can span multiple slides)
        self._add_methodology_slides()

        # 6. Experiments & Results (can span multiple slides)
        self._add_experiments_slides()

        # 7. Conclusion & Future Work
        self._add_conclusion_slide()

        return self.prs

    def _add_cover_slide(self):
        """Create the cover slide with paper metadata."""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])  # Blank layout

        # Add background color strip at top
        left = Inches(0)
        top = Inches(0)
        width = Inches(10)
        height = Inches(1.5)
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = self.PRIMARY_COLOR
        shape.line.fill.background()

        # Add paper title
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = self.metadata.get('title', 'Paper Title')
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(28)
        title_para.font.bold = True
        title_para.font.color.rgb = RGBColor(255, 255, 255)
        title_para.alignment = PP_ALIGN.CENTER

        # Authors
        authors = self.metadata.get('authors', 'Unknown Authors')
        if len(authors) > 80:
            authors = authors[:77] + '...'
        authors_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.2), Inches(9), Inches(0.4))
        authors_frame = authors_box.text_frame
        authors_frame.text = f"Authors: {authors}"
        authors_para = authors_frame.paragraphs[0]
        authors_para.font.size = Pt(16)
        authors_para.font.color.rgb = self.TEXT_COLOR
        authors_para.alignment = PP_ALIGN.CENTER

        # Venue and Year
        venue = self.metadata.get('venue', 'Unknown Venue')
        year = self.metadata.get('year', 'Unknown Year')
        venue_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.7), Inches(9), Inches(0.3))
        venue_frame = venue_box.text_frame
        venue_frame.text = f"{venue} {year}"
        venue_para = venue_frame.paragraphs[0]
        venue_para.font.size = Pt(14)
        venue_para.font.color.rgb = self.SECONDARY_COLOR
        venue_para.alignment = PP_ALIGN.CENTER

        # Paper URL
        if self.metadata.get('paper_url'):
            url_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.1), Inches(9), Inches(0.3))
            url_frame = url_box.text_frame
            url_frame.text = self.metadata['paper_url']
            url_para = url_frame.paragraphs[0]
            url_para.font.size = Pt(10)
            url_para.font.color.rgb = RGBColor(102, 102, 102)
            url_para.alignment = PP_ALIGN.CENTER

        # Divider line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2), Inches(3.8), Inches(6), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = self.SECONDARY_COLOR
        line.line.fill.background()

        # Student Information
        student_name = self.metadata.get('student_name', 'Your Name')
        student_id = self.metadata.get('student_id', 'Student ID')
        student_box = slide.shapes.add_textbox(Inches(0.5), Inches(4.5), Inches(9), Inches(0.5))
        student_frame = student_box.text_frame
        student_frame.text = f"Presented by: {student_name} ({student_id})"
        student_para = student_frame.paragraphs[0]
        student_para.font.size = Pt(18)
        student_para.font.color.rgb = self.TEXT_COLOR
        student_para.alignment = PP_ALIGN.CENTER

    def _add_title_slide(self, title: str, subtitle: str = ""):
        """
        Create a standard title slide with header and content area.

        Args:
            title: Slide title
            subtitle: Optional subtitle

        Returns:
            Tuple: (slide, content_text_frame)
        """
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])  # Blank layout

        # Add header bar
        header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(1))
        header.fill.solid()
        header.fill.fore_color.rgb = self.PRIMARY_COLOR
        header.line.fill.background()

        # Add title
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(0.6))
        title_frame = title_box.text_frame
        title_frame.text = title
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(32)
        title_para.font.bold = True
        title_para.font.color.rgb = RGBColor(255, 255, 255)

        # Add subtitle if provided
        if subtitle:
            subtitle_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(9), Inches(0.4))
            subtitle_frame = subtitle_box.text_frame
            subtitle_frame.text = subtitle
            subtitle_para = subtitle_frame.paragraphs[0]
            subtitle_para.font.size = Pt(18)
            subtitle_para.font.color.rgb = self.TEXT_COLOR

        # Add content text box
        content_top = Inches(1.7) if subtitle else Inches(1.3)
        content_box = slide.shapes.add_textbox(Inches(0.5), content_top, Inches(9), Inches(5.3))
        content_frame = content_box.text_frame
        content_frame.word_wrap = True

        return slide, content_frame

    def _add_introduction_slide(self):
        """Add Introduction and Related Work slide."""
        slide, content_frame = self._add_title_slide("Introduction & Related Work")

        introduction = self.analysis_data.get('introduction', self.analysis_data.get('abstract', ''))
        if introduction:
            self._add_content_to_frame(content_frame, introduction, max_slides=2)

    def _add_motivation_slide(self):
        """Add Motivation slide."""
        slide, content_frame = self._add_title_slide("Motivation")

        motivation = self.analysis_data.get('motivation', '')
        if motivation:
            self._add_content_to_frame(content_frame, motivation, max_slides=2)

    def _add_main_idea_slide(self):
        """Add Main Idea & Framework slide."""
        slide, content_frame = self._add_title_slide("Main Idea & Framework")

        # Combine contribution and methodology overview
        content = ""
        if self.analysis_data.get('contribution'):
            content += "### Key Contributions\n\n" + self.analysis_data['contribution'] + "\n\n"

        if self.analysis_data.get('how_does_paper_do'):
            # Extract first paragraph for overview
            methodology = self.analysis_data['how_does_paper_do']
            first_para = methodology.split('\n\n')[0] if '\n\n' in methodology else methodology[:300]
            content += "### Framework Overview\n\n" + first_para

        if content:
            self._add_content_to_frame(content_frame, content, max_slides=2)

    def _add_methodology_slides(self):
        """Add Methodology slides (can be multiple)."""
        methodology = self.analysis_data.get('how_does_paper_do', '')
        if not methodology:
            return

        # First slide with title
        slide, content_frame = self._add_title_slide("Methodology")
        self._add_content_to_frame(content_frame, methodology, max_slides=4)

    def _add_experiments_slides(self):
        """Add Experiments & Results slides (can be multiple)."""
        experiments = self.analysis_data.get('what_does_paper_do', '')
        if not experiments:
            return

        # First slide with title
        slide, content_frame = self._add_title_slide("Experiments & Results")
        self._add_content_to_frame(content_frame, experiments, max_slides=4)

    def _add_conclusion_slide(self):
        """Add Conclusion and Future Work slide."""
        slide, content_frame = self._add_title_slide("Conclusion & Future Work")

        content = ""
        if self.analysis_data.get('conclusion'):
            content += "### Conclusion\n\n" + self.analysis_data['conclusion'] + "\n\n"

        if self.analysis_data.get('future_work'):
            content += "### Future Work\n\n" + self.analysis_data['future_work']

        if content:
            self._add_content_to_frame(content_frame, content, max_slides=2)

    def _add_content_to_frame(self, text_frame, content: str, max_slides: int = 2):
        """
        Add markdown-formatted content to a text frame, handling overflow across slides.

        Args:
            text_frame: The text frame to add content to
            content: Markdown-formatted content string
            max_slides: Maximum number of slides to create for overflow
        """
        self._add_formatted_text(text_frame, content)

        # Check if content overflows and create additional slides if needed
        current_slide = 0
        while text_frame.text.endswith('...') and current_slide < max_slides - 1:
            # Create a continuation slide
            slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])

            # Add header
            header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(1))
            header.fill.solid()
            header.fill.fore_color.rgb = self.PRIMARY_COLOR
            header.line.fill.background()

            title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(0.6))
            title_frame = title_box.text_frame
            title_frame.text = "(Continued)"
            title_para = title_frame.paragraphs[0]
            title_para.font.size = Pt(32)
            title_para.font.bold = True
            title_para.font.color.rgb = RGBColor(255, 255, 255)

            # Add content text box
            content_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.3), Inches(9), Inches(5.7))
            text_frame = content_box.text_frame
            text_frame.word_wrap = True

            self._add_formatted_text(text_frame, content)
            current_slide += 1

    def _add_formatted_text(self, text_frame, content: str):
        """
        Parse and add markdown-formatted content to a text frame.

        Args:
            text_frame: PowerPoint text frame
            content: Markdown-formatted string
        """
        lines = content.split('\n')
        current_paragraph = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Empty line - add spacing
            if not stripped:
                if current_paragraph is not None:
                    p = text_frame.add_paragraph()
                    p.text = ""
                    p.space_after = Pt(6)
                    current_paragraph = p
                continue

            # Header (###)
            if stripped.startswith('###'):
                header_text = stripped[3:].strip()
                p = text_frame.add_paragraph()
                p.text = header_text
                p.font.size = Pt(20)
                p.font.bold = True
                p.font.color.rgb = self.PRIMARY_COLOR
                p.space_before = Pt(12)
                p.space_after = Pt(6)
                current_paragraph = p
                continue

            # Bullet point
            if stripped.startswith('- ') or stripped.startswith('* '):
                bullet_text = stripped[2:].strip()
                # Handle inline formatting
                bullet_text = self._parse_inline_formatting(bullet_text)

                p = text_frame.add_paragraph()
                p.text = bullet_text
                p.level = 0
                p.font.size = Pt(16)
                p.font.color.rgb = self.TEXT_COLOR
                p.space_before = Pt(4)
                p.space_after = Pt(4)
                current_paragraph = p
                continue

            # Numbered list
            numbered_match = re.match(r'^(\d+)\.\s+(.*)$', stripped)
            if numbered_match:
                num_text = numbered_match.group(2)
                # Handle inline formatting
                num_text = self._parse_inline_formatting(num_text)

                p = text_frame.add_paragraph()
                p.text = num_text
                p.level = 0
                p.font.size = Pt(16)
                p.font.color.rgb = self.TEXT_COLOR
                p.space_before = Pt(4)
                p.space_after = Pt(4)
                current_paragraph = p
                continue

            # Regular paragraph
            para_text = self._parse_inline_formatting(stripped)

            # If it's a continuation of previous content, append to last paragraph
            if current_paragraph and not stripped[0].isupper():
                current_paragraph.text += " " + para_text
            else:
                p = text_frame.add_paragraph()
                p.text = para_text
                p.font.size = Pt(16)
                p.font.color.rgb = self.TEXT_COLOR
                p.space_before = Pt(6)
                p.space_after = Pt(6)
                p.alignment = PP_ALIGN.JUSTIFY
                current_paragraph = p

    def _parse_inline_formatting(self, text: str) -> str:
        """
        Parse inline markdown formatting (bold, italic, code).

        Args:
            text: Text with markdown formatting

        Returns:
            str: Text with PowerPoint formatting applied (as plain text for now,
                 as python-pptx has limited inline formatting support)
        """
        # For simplicity, we return the text stripped of markdown markers
        # In a production system, you would use run objects for proper formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code
        return text

    def save(self, filepath: str):
        """
        Save the presentation to a file.

        Args:
            filepath: Path where to save the .pptx file
        """
        self.prs.save(filepath)

    def save_to_bytes(self) -> BytesIO:
        """
        Save the presentation to a BytesIO buffer.

        Returns:
            BytesIO: Buffer containing the .pptx file
        """
        buffer = BytesIO()
        self.prs.save(buffer)
        buffer.seek(0)
        return buffer


def generate_powerpoint(analysis_data: Dict[str, Any], metadata: Dict[str, Any]) -> BytesIO:
    """
    Convenience function to generate a PowerPoint presentation.

    Args:
        analysis_data: Dictionary containing paper analysis results
        metadata: Dictionary containing paper metadata (title, authors, venue, year, url,
                       student_name, student_id)

    Returns:
        BytesIO: Buffer containing the .pptx file
    """
    generator = PowerPointGenerator(analysis_data, metadata)
    return generator.save_to_bytes()


def extract_metadata_from_paper(paper_text: str, filename: str = "") -> Dict[str, str]:
    """
    Extract paper metadata from the paper text.

    Args:
        paper_text: Full text of the research paper
        filename: Original filename (used as fallback for title)

    Returns:
        dict: Extracted metadata (title, authors, venue, year, url)
    """
    import re

    metadata = {
        'title': filename.replace('.pdf', '') if filename else 'Unknown Title',
        'authors': 'Unknown Authors',
        'venue': 'Unknown Venue',
        'year': 'Unknown Year',
        'paper_url': '',
    }

    # Try to extract title (usually first significant text, often all caps or title case)
    lines = paper_text.split('\n')
    for i, line in enumerate(lines[:20]):  # Check first 20 lines
        stripped = line.strip()
        # Skip page numbers, headers, etc.
        if stripped and len(stripped) > 10 and len(stripped) < 200:
            # Likely a title
            if not re.match(r'^\d+$', stripped) and not stripped.startswith('http'):
                # Check if it looks like a title (contains letters, maybe some numbers)
                if any(c.isalpha() for c in stripped):
                    # First significant line is likely the title
                    if not metadata['title'] or metadata['title'] == filename.replace('.pdf', ''):
                        metadata['title'] = stripped
                    break

    # Try to extract authors (usually after title)
    in_authors = False
    author_lines = []
    for i, line in enumerate(lines[5:30]):  # Check lines 5-30
        stripped = line.strip()
        # Look for author patterns (names, universities, emails)
        if in_authors:
            if not stripped or stripped.startswith('Abstract') or len(author_lines) > 5:
                break
            if any(marker in stripped.lower() for marker in ['university', 'institute', 'college', 'lab', '@']):
                author_lines.append(stripped)
            # Check if it looks like a name (has common name patterns)
            elif any(c.isalpha() for c in stripped) and len(stripped) < 100:
                author_lines.append(stripped)
        # Start collecting after title-like text
        elif metadata['title'] in line and 'author' in lines[i+5:i+10]:
            in_authors = True

    if author_lines:
        # Join author lines and clean up
        authors_text = ' '.join(author_lines)
        # Remove common non-author text
        authors_text = re.sub(r'\bUniversity\b.*', '', authors_text, flags=re.IGNORECASE)
        authors_text = re.sub(r'\bInstitute\b.*', '', authors_text, flags=re.IGNORECASE)
        metadata['authors'] = authors_text.strip()[:200]  # Limit length

    # Try to extract venue and year from text
    text_lower = paper_text.lower()

    # Look for conference/journal names
    venues = [
        'CVPR', 'ICCV', 'ECCV', 'NeurIPS', 'ICML', 'ICLR', 'AAAI',
        'IJCAI', 'ACL', 'EMNLP', 'NAACL', 'SIGGRAPH', 'SIGMOD',
        'VLDB', 'ICDE', 'WWW', 'KDD', 'RecSys', 'CIKM',
        'IEEE Transactions on', 'ACM Transactions on',
        'Journal of', 'Proceedings of'
    ]

    for venue in venues:
        if venue.lower() in text_lower:
            # Extract the full venue mention
            pattern = re.compile(re.escape(venue) + r'[^.\n]*', re.IGNORECASE)
            matches = pattern.findall(paper_text)
            if matches:
                metadata['venue'] = matches[0].strip()[:100]
                break

    # Extract year (4 digits, likely 2015-2025)
    year_match = re.search(r'\b(201[5-9]|202[0-5])\b', paper_text[:5000])
    if year_match:
        metadata['year'] = year_match.group(1)

    # Try to extract arXiv URL or other URLs
    url_match = re.search(r'(https?://arxiv\.org/abs/\d+\.\d+)', paper_text[:3000])
    if url_match:
        metadata['paper_url'] = url_match.group(1)
    else:
        # Look for any other paper URL
        url_match = re.search(r'(https?://[^\s]+(?:\.pdf|/paper/))', paper_text[:3000])
        if url_match:
            metadata['paper_url'] = url_match.group(1)

    return metadata
