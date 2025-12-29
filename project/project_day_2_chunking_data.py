import io
import zipfile
import requests
import frontmatter

def read_repo_data(repo_owner, repo_name, branch = 'main'):
    """
    Download and parse all markdown files from a GitHub repository.
    
    Args:
        repo_owner: GitHub username or organization
        repo_name: Repository name
    
    Returns:
        List of dictionaries containing file content and metadata
    """
    prefix = 'https://codeload.github.com' 
    url = f'{prefix}/{repo_owner}/{repo_name}/zip/refs/heads/{branch}'
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

### Select project to work on
project_docs = read_repo_data('Khangtran94', 'kaggle-solutions','gh-pages')
print('Length of project docs:',len(project_docs))

#### Split by sliding window
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

project_sliding_chunks = []
from tqdm.auto import tqdm 
for doc in tqdm(project_docs):
    doc_copy  = doc.copy()
    doc_content = doc_copy.pop('content', '')
    chunks = sliding_window(doc_content, size=2000, step=1000)
    for chunk in chunks:
        chunk.update(doc_copy)
    project_sliding_chunks.extend(chunks)

print('-'*100)
print('SLIDING CHUNK')
print(project_sliding_chunks)


### Split by paragraphs and sections
import re
def split_markdown_by_level(text, level=2):
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

project_section_chunks = []
for doc in tqdm(project_docs):
    doc_copy  = doc.copy()
    doc_content = doc_copy.pop('content', '')
    sections = split_markdown_by_level(doc_content, level=2)
    for section in sections:
        chunk = {'chunk': section}
        chunk.update(doc_copy)
        project_section_chunks.append(chunk)
    
print('-'*100)
print('SECTION chunk')
print(project_section_chunks)