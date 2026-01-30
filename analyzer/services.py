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

    Args:
        paper_text: Full text content of the research paper

    Returns:
        str: Formatted prompt for the LLM
    """
    prompt = f"""You are an expert research analyst specializing in academic paper analysis. Your task is to thoroughly analyze the following research paper and provide a comprehensive breakdown.

Please analyze the paper and extract the following information:

## PAPER CONTENT:
{paper_text[:25000]}


## ANALYSIS REQUIREMENTS:

Please provide a detailed analysis with the following sections. Be specific, thorough, and extract exact information from the paper:

### 1. ABSTRACT 📝
Summarize the abstract in 2-3 sentences. What is the core focus of this paper?

### 2. MOTIVATION 💡
What problem or gap in existing research motivated this work?
- What are the key issues or limitations in current approaches?
- Why is this research necessary or timely?
- What real-world problem does it address?

### 3. CONTRIBUTION 🎯
What are the main contributions of this paper?
- Novel algorithms, methods, or frameworks proposed
- New datasets or benchmarks introduced
- Theoretical contributions or proofs
- Practical improvements over existing methods
- Be specific and list each contribution clearly

### 4. WHAT DOES THE PAPER DO (Experiments & Results) 🔬
Describe the experimental evaluation:
- What datasets were used?
- What baselines or comparison methods were evaluated against?
- What metrics were used for evaluation?
- What are the key quantitative results?
- Summarize the main experimental findings
- Any significant performance improvements or discoveries?

### 5. HOW DOES THE PAPER DO IT (Methodology) ⚙️
Explain the technical approach:
- What is the main idea or framework proposed?
- Describe the key technical components or architecture
- What algorithms or techniques are used?
- How does the method work (step-by-step)?
- Include any mathematical formulations or key equations
- What makes this approach innovative or unique?

### 6. LIMITATIONS & CHALLENGES ⚠️
Discuss the limitations acknowledged by the authors:
- What are the stated limitations of the proposed method?
- What assumptions does the method make?
- What scenarios or conditions might affect performance?
- Any computational or resource constraints?
- What challenges remain unsolved?

### 7. FUTURE WORK 🚀
What future work do the authors suggest?
- What extensions or improvements are proposed?
- What open questions remain?
- What directions for future research are identified?

### 8. CONCLUSION 📌
Summarize the main conclusion:
- What are the key takeaways?
- How does this work advance the field?
- What is the broader impact?


## RESPONSE FORMAT:
Please provide your analysis in the following JSON format:

{{
    "abstract": "Brief summary of the abstract...",
    "motivation": "Detailed explanation of motivation...",
    "contribution": "List of key contributions...",
    "what_does_paper_do": "Experiments, results, and findings...",
    "how_does_paper_do": "Technical methodology and framework...",
    "limitations_challenges": "Limitations and challenges...",
    "future_work": "Suggested future work...",
    "conclusion": "Main conclusions and impact..."
}}

Ensure your analysis is:
- Accurate and based only on the paper content
- Specific and detailed, not vague
- Well-structured and easy to understand
- Professional and scholarly in tone
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
                    "content": "You are an expert research analyst specializing in academic paper analysis. You always respond with valid JSON."
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
                        "content": "You are an expert research analyst specializing in academic paper analysis. IMPORTANT: You must respond ONLY with valid JSON, no additional text or explanation."
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
