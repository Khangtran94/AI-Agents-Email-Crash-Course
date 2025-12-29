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
# print(evidently_docs[:2])  # Print first 2 documents for inspection

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

evidently_sliding_chunks = []
for doc in evidently_docs:
    doc_copy  = doc.copy()
    doc_content = doc_copy.pop('content', '')
    chunks = sliding_window(doc_content, size=2000, step=1000)
    for chunk in chunks:
        chunk.update(doc_copy)
    evidently_sliding_chunks.extend(chunks)
        
from minsearch import Index
index = Index(text_fields = ['chunk','title','description','filename'], keyword_fields = [])
index.fit(evidently_sliding_chunks)

query = 'What should be in a test dataset for AI evaluation?'
results = index.search(query)

print(results)