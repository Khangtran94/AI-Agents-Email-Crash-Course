import io
import zipfile
import requests
import frontmatter

def read_repo_data(repo_owner, repo_name):
    """
    Download and parse all markdown files from a GitHub repository.
    
    Args:
        repo_owner: GitHub username or organization
        repo_name: Repository name
    
    Returns:
        List of dictionaries containing file content and metadata
    """
    prefix = 'https://codeload.github.com' 
    url = f'{prefix}/{repo_owner}/{repo_name}/zip/refs/heads/main'
    resp = requests.get(url)
    
    if resp.status_code != 200:
        raise Exception(f"Failed to download repository: {resp.status_code}")

    repository_data = []
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    
    for file_info in zf.infolist():
        filename = file_info.filename
        filename_lower = filename.lower()

        if not (filename_lower.endswith('.md') 
            or filename_lower.endswith('.mdx')):
            continue
    
        try:
            with zf.open(file_info) as f_in:
                content = f_in.read().decode('utf-8', errors='ignore')
                post = frontmatter.loads(content)
                data = post.to_dict()
                data['filename'] = filename
                repository_data.append(data)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    zf.close()
    return repository_data

evidently_docs = read_repo_data('evidentlyai', 'docs')
# print(f"Evidently documents: {len(evidently_docs)}")

### Split by sliding window
def sliding_window(seq, size, step):
    if size  <= 0 or step <= 0:
        raise ValueError("Size and step must be positive integers.")
    n = len(seq)
    result = []
    for i in range(0, n, step):
        chunk = seq[i:i + size]
        result.append({'start': i, 'end': i + len(chunk), 'chunk': chunk})
        if i + size >= n:
            break
    return result

evidently_chunks = []
for doc in evidently_docs:
    doc_copy  = doc.copy()
    doc_content = doc_copy.pop('content', '')
    chunks = sliding_window(doc_content, size=2000, step=1000)
    for chunk in chunks:
        chunk.update(doc_copy)
    evidently_chunks.extend(chunks)
        
### Split by paragraphs and sections
import re
text = evidently_docs[45]['content']
paragraphs = re.split(r'\n\s*\n', text.strip())

### Split by headers
def split_markdown_by_level(text, level=2):
    """
    Split markdown text by a specific header level.
    
    :param text: Markdown text as a string
    :param level: Header level to split on
    :return: List of sections as strings
    """
    # This regex matches markdown headers
    # For level 2, it matches lines starting with "## "
    header_pattern = r'^(#{' + str(level) + r'} )(.+)$'
    pattern = re.compile(header_pattern, re.MULTILINE)

    # Split and keep the headers
    parts = pattern.split(text)
    
    sections = []
    for i in range(1, len(parts), 3):
        # We step by 3 because regex.split() with
        # capturing groups returns:
        # [before_match, group1, group2, after_match, ...]
        # here group1 is "## ", group2 is the header text
        header = parts[i] + parts[i+1]  # "## " + "Title"
        header = header.strip()

        # Get the content after this header
        content = ""
        if i+2 < len(parts):
            content = parts[i+2].strip()

        if content:
            section = f'{header}\n\n{content}'
        else:
            section = header
        sections.append(section)
    
    return sections

evidently_chunks = []
for doc in evidently_docs:
    doc_copy  = doc.copy()
    doc_content = doc_copy.pop('content', '')
    sections = split_markdown_by_level(doc_content, level=2)
    for section in sections:
        section_doc = doc_copy.copy()
        section_doc['section'] = section
        evidently_chunks.append(section_doc)
        
### use openai to further split large sections
# from openai import OpenAI
# openai_client = OpenAI()
# def llm(prompt, model = 'gpt-4o-mini'):
#     messages = [{"role": "user", "content": prompt}]
#     response = openai_client.responses.create(model = 'gpt-4o-mini', input = messages)
#     return response.output_text

# prompt_template = """
# Split the provided document into logical sections
# that make sense for a Q&A system.

# Each section should be self-contained and cover
# a specific topic or concept.

# <DOCUMENT>
# {document}
# </DOCUMENT>

# Use this format:

# ## Section Name

# Section content with all relevant details

# ---

# ## Another Section Name

# Another section content

# ---
# """.strip()

# ### Fuction to split using LLM
# def intelligent_chunking(text):
#     prompt = prompt_template.format(document=text)
#     response = llm(prompt)
#     sections = response.split('---')
#     sections = [section.strip() for section in sections if section.strip()]
#     return sections


# from tqdm.auto import tqdm
# evidently_chunks = []
# for doc in tqdm(evidently_docs):
#     doc_copy  = doc.copy()
#     doc_content = doc_copy.pop('content', '')
#     sections = intelligent_chunking(doc_content)
#     for section in sections:
#         section_doc = doc_copy.copy()
#         section_doc['section'] = section
#         evidently_chunks.append(section_doc)
        