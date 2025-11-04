import fitz
import requests
import json
import os
import glob

def read_pdf(pdf_path):
    """Extract text from PDF"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(min(2, len(doc))):
            text += doc[page_num].get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def extract_info_with_ollama(text, model="llama3.2"):
    """Use Ollama to extract title and authors"""
    ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    
    prompt = f"""
    Extract the article title and author names from this academic paper text.
    Return ONLY a JSON object with this exact format:
    {{
        "title": "article title here",
        "authors": ["author1", "author2", "author3"]
    }}
    
    Paper text:
    {text[:3000]}
    """
    
    try:
        response = requests.post(
            f'{ollama_host}/api/generate',
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        return response.json()['response']
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None

def main():
    # Find all PDFs in the pdfs folder
    pdf_files = glob.glob("/app/pdfs/*.pdf")
    
    if not pdf_files:
        print("No PDF files found in /app/pdfs/")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s)")
    print("-" * 50)
    
    # Create output directory
    os.makedirs("/app/output", exist_ok=True)
    
    # Process each PDF
    all_results = []
    
    for pdf_path in pdf_files:
        pdf_name = os.path.basename(pdf_path)
        print(f"\n Processing: {pdf_name}")
        
        # Read PDF
        text = read_pdf(pdf_path)
        if not text:
            print(f"Skipping {pdf_name} - couldn't read file")
            continue
        
        print(f"✓ Read {len(text)} characters")
        
        # Extract info using Ollama
        print("Extracting information with Ollama...")
        result = extract_info_with_ollama(text)
        
        if not result:
            print(f"Skipping {pdf_name} - Ollama error")
            continue
        
        # Parse JSON
        try:
            start = result.find('{')
            end = result.rfind('}') + 1
            json_str = result[start:end]
            article_info = json.loads(json_str)
            
            # Add filename to the result
            article_info['source_file'] = pdf_name
            
            # Save individual JSON file
            output_filename = pdf_name.replace('.pdf', '_info.json')
            output_path = f"/app/output/{output_filename}"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(article_info, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved to: {output_filename}")
            print(f"  Title: {article_info.get('title', 'N/A')}")
            print(f"  Authors: {len(article_info.get('authors', []))} author(s)")
            
            all_results.append(article_info)
            
        except Exception as e:
            print(f"Error parsing JSON for {pdf_name}: {e}")
            print(f"Raw response: {result[:200]}...")
            continue
    
    # Save combined results
    if all_results:
        combined_path = "/app/output/all_articles.json"
        with open(combined_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 50)
        print(f"Successfully processed {len(all_results)} article(s)")
        print(f"Individual files saved in: /app/output/")
        print(f"Combined file: all_articles.json")
        print("=" * 50)
    else:
        print("\n No articles were successfully processed")

if __name__ == "__main__":
    main()
