import os
import json
from typing import Dict, Any
import PyPDF2
from io import BytesIO

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
LLM_MODEL = os.getenv('LLM_MODEL', 'anthropic/claude-3.5-sonnet:beta')
OPENROUTER_APP_NAME = os.getenv('OPENROUTER_APP_NAME', 'Paper Analyzer')
OPENROUTER_REFERER = os.getenv('OPENROUTER_REFERER', 'http://localhost:8000')


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text content from a PDF file.

    Args:
        pdf_file: Django UploadedFile object

    Returns:
        str: Extracted text from the PDF
    """
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = []

        # Extract text from all pages
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            if text.strip():
                text_content.append(f"--- Page {page_num + 1} ---\n{text}")

        return '\n\n'.join(text_content)
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def create_analysis_prompt(paper_text: str) -> str:
    """
    Create a comprehensive prompt for LLM to analyze a research paper.
    Focused purely on paper analysis for understanding and research purposes.

    Args:
        paper_text: Full text content of the research paper

    Returns:
        str: Formatted prompt for the LLM
    """
    prompt = f"""You are an expert research analyst specializing in academic paper analysis. Your task is to thoroughly analyze the following research paper and provide a comprehensive breakdown for research understanding.

Please analyze the paper and extract the following information:

## PAPER CONTENT:
{paper_text[:25000]}


## ANALYSIS REQUIREMENTS:

Please provide a detailed analysis with the following sections. Be specific, thorough, and extract exact information from the paper.

### PAPER METADATA
First, extract:
- Paper title (exact)
- All authors (list them all)
- Publication venue (conference/journal name, e.g., "ICCV 2023", "CVPR 2022", "IEEE Transactions on Pattern Analysis and Machine Intelligence")
- Publication year
- Paper URL (arXiv URL, official PDF link, or DOI link if mentioned)

### 1. ABSTRACT
Summarize the abstract in 2-3 sentences. What is the core focus of this paper?

### 2. INTRODUCTION
Provide a comprehensive introduction including:
- What is the research domain/field?
- What is the background context for this work?
- What is the related work? Summarize key prior approaches and their limitations
- How does this paper relate to or build upon existing research?
- What is the research gap or problem this paper addresses?

### 3. MOTIVATION
What problem or gap in existing research motivated this work?
- What are the key issues or limitations in current approaches?
- Why is this research necessary or timely?
- What real-world problem does it address?

### 4. CONTRIBUTION
What are the main contributions of this paper?
- Novel algorithms, methods, or frameworks proposed
- New datasets or benchmarks introduced
- Theoretical contributions or proofs
- Practical improvements over existing methods
- Be specific and list each contribution clearly

### 5. METHODOLOGY
Explain the technical approach in detail:
- What is the main idea or framework proposed?
- Describe the key technical components or architecture
- What algorithms or techniques are used?
- How does the method work (step-by-step)?
- Include any mathematical formulations or key equations
- What makes this approach innovative or unique?

### 6. EXPERIMENTS & RESULTS
Describe the experimental evaluation:
- What datasets were used?
- What baselines or comparison methods were evaluated against?
- What metrics were used for evaluation?
- What are the key quantitative results?
- Summarize the main experimental findings
- Any significant performance improvements or discoveries?
- Include specific numbers/percentages when available

### 7. LIMITATIONS & CHALLENGES
Discuss the limitations acknowledged by the authors:
- What are the stated limitations of the proposed method?
- What assumptions does the method make?
- What scenarios or conditions might affect performance?
- Any computational or resource constraints?
- What challenges remain unsolved?

### 8. FUTURE WORK
What future work do the authors suggest?
- What extensions or improvements are proposed?
- What open questions remain?
- What directions for future research are identified?

### 9. CONCLUSION
Summarize the main conclusion:
- What are the key takeaways?
- How does this work advance the field?
- What is the broader impact?


## RESPONSE FORMAT:
Please provide your analysis in the following JSON format. **IMPORTANT: Use Markdown formatting within each JSON field:**

- Use bullet points with `-` for lists
- Use numbered lists with `1.` `2.` `3.` for sequential items
- Use `**bold**` for key terms and emphasis
- Use `###` for subsections within longer responses
- Use proper spacing and line breaks for readability

{{
    "title": "Exact paper title",
    "authors": "Author1, Author2, Author3",
    "venue": "Conference/Journal Name",
    "year": "Publication Year",
    "paper_url": "https://arxiv.org/abs/...",
    "abstract": "Brief summary of the abstract...",
    "introduction": "Background and related work. Use subsections: ### Background\\n### Related Work\\n### Research Gap...",
    "motivation": "- Key issue 1\\n- Key issue 2\\n- Problem addressed...",
    "contribution": "- Contribution 1\\n- Contribution 2\\n- Contribution 3...",
    "how_does_paper_do": "Technical methodology with subsections: ### Main Idea\\n### Framework\\n### Algorithm\\n### Implementation details...",
    "what_does_paper_do": "1. Dataset used\\n2. Evaluation metrics\\n3. Results: ...\\n4. Key findings...",
    "limitations_challenges": "- Limitation 1\\n- Limitation 2\\n- Assumption/Constraint...",
    "future_work": "1. Future direction 1\\n2. Future direction 2...",
    "conclusion": "Main conclusions, impact, and significance..."
}}

Ensure your analysis is:
- Accurate and based only on the paper content
- Specific and detailed, not vague
- Well-structured with Markdown formatting
- Use proper list formatting (bullet points or numbered lists)
- Professional and scholarly in tone
- Comprehensive enough for deep understanding of the research
"""

    return prompt


def create_ppt_generation_prompt(paper_text: str, student_name: str = "Your Name", student_id: str = "Student ID") -> str:
    """
    Create a specialized prompt for LLM to analyze a research paper for PPT generation.
    This prompt is optimized for generating presentation-ready content with specific
    focus on what should appear on slides.

    Args:
        paper_text: Full text content of the research paper
        student_name: Name of the student presenting
        student_id: Student ID

    Returns:
        str: Formatted prompt for the LLM
    """
    prompt = f"""You are an expert academic presentation designer. Your task is to analyze the following research paper and extract content specifically for generating a professional PowerPoint presentation suitable for academic presentation requirements (≤16 slides).

## PAPER CONTENT:
{paper_text[:25000]}

## PRESENTATION REQUIREMENTS:

This analysis will be used to generate an academic presentation with the following structure:
1. Cover Slide (title, authors, venue, student info)
2. Introduction & Related Work (1-2 slides)
3. Motivation (1 slide)
4. Main Idea & Framework (1-2 slides)
5. Methodology (2-4 slides)
6. Experiments & Results (2-4 slides)
7. Conclusion & Future Work (1-2 slides)

## ANALYSIS REQUIREMENTS:

Please extract and organize content specifically for presentation slides. Focus on VISUAL-READY content that can be easily converted to bullet points and diagrams.

### PAPER METADATA (for cover slide)
Extract:
- Paper title (exact, as it should appear on the cover)
- All authors (formatted for display)
- Publication venue (e.g., "CVPR 2024", "NeurIPS 2023")
- Publication year
- Paper URL if available

### 1. INTRODUCTION & RELATED WORK (for 1-2 slides)
Extract presentation-ready content:
- **Background**: 2-3 bullet points on the research domain
- **Related Work**: 3-4 key prior approaches with brief descriptions
- **Research Gap**: What's missing and why this paper matters
- Format for visual presentation (bullet points, concise)

### 2. MOTIVATION (for 1 slide)
Extract compelling motivation:
- **Problem Statement**: What is the core problem? (1-2 sentences)
- **Current Limitations**: 3-4 bullet points on issues with existing approaches
- **Why Now**: Why is this research timely? (1 sentence)
- Make it impactful and presentation-friendly

### 3. MAIN IDEA & CONTRIBUTIONS (for 1-2 slides)
Extract the key contributions:
- **Main Idea**: One clear sentence summarizing the core innovation
- **Key Contributions**: 3-5 bullet points on specific contributions
- **Framework Overview**: High-level description suitable for a diagram
- Focus on what makes this work novel

### 4. METHODOLOGY (for 2-4 slides)
Extract technical approach in presentable format:
- **Overview**: 2-3 sentence high-level description
- **Key Components**: Break down into 4-6 main components with brief descriptions
- **Algorithm/Process**: Step-by-step flow (suitable for flowchart)
- **Technical Details**: Key equations or technical insights (2-3 items)
- Organize with clear subsections for multiple slides

### 5. EXPERIMENTS & RESULTS (for 2-4 slides)
Extract results in presentation format:
- **Datasets**: What data was used? (1-2 bullet points)
- **Baselines**: Comparison methods (list 3-5)
- **Metrics**: Evaluation metrics used (list)
- **Key Results**: Quantitative results in bullet format
  - State specific numbers, percentages, improvements
  - Format: "Method X achieved Y% improvement on Z dataset"
- **Main Findings**: 3-4 key takeaways from experiments
- Include specific numbers for charts/visuals

### 6. CONCLUSION & FUTURE WORK (for 1-2 slides)
Extract concluding insights:
- **Key Takeaways**: 3-4 bullet points on main contributions
- **Impact**: How does this advance the field? (1-2 sentences)
- **Future Work**: 3-4 suggested directions or open problems

## RESPONSE FORMAT:
Provide your analysis in JSON format optimized for slide generation:

{{
    "title": "Exact Paper Title",
    "authors": "Author1, Author2, Author3",
    "venue": "Conference/Journal Name Year",
    "year": "Publication Year",
    "paper_url": "https://...",
    "introduction": "- Research domain: 1-2 sentences\\n- Related work:\\n  - Prior approach 1: brief description\\n  - Prior approach 2: brief description\\n- Research gap: What's missing",
    "motivation": "- Core problem: Clear statement\\n- Limitation 1\\n- Limitation 2\\n- Limitation 3\\n- Why this matters",
    "contribution": "### Main Idea\\nOne clear sentence\\n\\n### Key Contributions\\n- Contribution 1\\n- Contribution 2\\n- Contribution 3\\n- Contribution 4\\n\\n### Framework Overview\\nHigh-level description suitable for diagram",
    "how_does_paper_do": "### Overview\\n2-3 sentence description\\n\\n### Key Components\\n1. Component 1: description\\n2. Component 2: description\\n3. Component 3: description\\n\\n### Algorithm\\nStep 1\\nStep 2\\nStep 3\\n\\n### Technical Details\\n- Key equation/insight 1\\n- Key equation/insight 2",
    "what_does_paper_do": "### Datasets\\n- Dataset 1: description\\n- Dataset 2: description\\n\\n### Baselines\\n- Method 1\\n- Method 2\\n- Method 3\\n\\n### Metrics\\n- Metric 1\\n- Metric 2\\n\\n### Key Results\\n- Our method achieved X% on dataset Y (Z% improvement over baseline)\\n- On dataset A, achieved B%\\n- Comparison: Method A: 85%, Method B: 88%, **Ours: 92%**\\n\\n### Main Findings\\n- Finding 1\\n- Finding 2\\n- Finding 3",
    "conclusion": "### Key Takeaways\\n- Takeaway 1\\n- Takeaway 2\\n- Takeaway 3\\n\\n### Impact\\n1-2 sentences on field advancement\\n\\n### Future Work\\n- Direction 1\\n- Direction 2\\n- Direction 3",
    "future_work": "1. Extension 1\\n2. Extension 2\\n3. Open problem 1",
    "abstract": "Brief 2-3 sentence summary for speaker notes"
}}

## CRITICAL REQUIREMENTS:
- **Slide-Ready**: All content must be presentation-ready (bullet points, concise)
- **Specific Numbers**: Include exact percentages, scores, improvements for charts
- **Visual Structure**: Use subsections (###) to indicate slide breaks
- **Bullet Format**: Use `-` for bullets, numbered lists for sequences
- **Concise**: Each point should be 1-2 sentences max
- **Complete**: Must contain all sections for a full presentation

Generate presentation content that is:
- Immediately usable for slide creation
- Visually structured and easy to present
- Quantitative and specific (no vague statements)
- Organized for clear slide-by-slide conversion
"""

    return prompt


def call_llm_api(prompt: str) -> Dict[str, Any]:
    """
    Call the OpenRouter LLM API to analyze the paper.

    Args:
        prompt: The formatted prompt to send to the LLM

    Returns:
        dict: Parsed JSON response from the LLM

    Raises:
        Exception: If API call fails or returns invalid response
    """
    try:
        return _call_openrouter(prompt)
    except Exception as e:
        raise Exception(f"Error calling OpenRouter API: {str(e)}")


def _call_openrouter(prompt: str) -> Dict[str, Any]:
    """
    Call OpenRouter API for paper analysis.
    OpenRouter provides access to multiple LLMs through a unified API.
    """
    try:
        from openai import OpenAI

        # Your app name and URL for OpenRouter ranking
        # See https://openrouter.ai/docs/quick-start
        headers = {
            'HTTP-Referer': OPENROUTER_REFERER,
            'X-Title': OPENROUTER_APP_NAME,
        }

        client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=OPENROUTER_API_KEY,
            default_headers=headers
        )

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert research analyst specializing in academic paper analysis. You always respond with valid JSON. Format all text content using Markdown with proper bullet points, numbered lists, and bold text for emphasis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            extra_body={
                'response_format': {"type": "json_object"}
            }
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        # Some models on OpenRouter don't support response_format
        # Try again without it
        try:
            from openai import OpenAI

            headers = {
                'HTTP-Referer': OPENROUTER_REFERER,
                'X-Title': OPENROUTER_APP_NAME,
            }

            client = OpenAI(
                base_url=OPENROUTER_BASE_URL,
                api_key=OPENROUTER_API_KEY,
                default_headers=headers
            )

            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert research analyst specializing in academic paper analysis. IMPORTANT: You must respond ONLY with valid JSON, no additional text or explanation. Format all text content using Markdown with proper bullet points, numbered lists, and bold text for emphasis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )

            content = response.choices[0].message.content

            # Try to extract JSON from the response if it contains extra text
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                content = json_match.group(0)

            return json.loads(content)

        except Exception as e2:
            raise Exception(f"OpenRouter API error: {str(e2)}")


def analyze_paper(pdf_file) -> Dict[str, str]:
    """
    Main function to analyze a research paper PDF.
    Uses the standard analysis prompt for research understanding.

    Args:
        pdf_file: Django UploadedFile object

    Returns:
        dict: Analysis results with all sections
    """
    # Step 1: Extract text from PDF
    paper_text = extract_text_from_pdf(pdf_file)

    if not paper_text or len(paper_text.strip()) < 100:
        raise Exception("Unable to extract sufficient text from the PDF. Please ensure it's a valid text-based PDF.")

    # Step 2: Create analysis prompt
    prompt = create_analysis_prompt(paper_text)

    # Step 3: Call LLM API
    analysis_result = call_llm_api(prompt)

    return analysis_result


def analyze_paper_for_ppt(pdf_file, student_name: str = "Your Name", student_id: str = "Student ID") -> Dict[str, str]:
    """
    Analyze a research paper PDF specifically for PPT generation.
    Uses the PPT-optimized prompt that focuses on presentation-ready content.

    Args:
        pdf_file: Django UploadedFile object
        student_name: Name of the student presenting
        student_id: Student ID

    Returns:
        dict: Analysis results optimized for presentation generation
    """
    # Step 1: Extract text from PDF
    paper_text = extract_text_from_pdf(pdf_file)

    if not paper_text or len(paper_text.strip()) < 100:
        raise Exception("Unable to extract sufficient text from the PDF. Please ensure it's a valid text-based PDF.")

    # Step 2: Create PPT-specific analysis prompt
    prompt = create_ppt_generation_prompt(paper_text, student_name, student_id)

    # Step 3: Call LLM API
    analysis_result = call_llm_api(prompt)

    return analysis_result
