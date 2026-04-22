import sys
import os

# Ensure the root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.gmail_tools import gmail_search
from tools.pdf_tools import parse_pdf

def main():
    print("Searching Gmail...")
    results = gmail_search("subject:Application has:attachment", max_results=2)
    print(f"Found {results['count']} messages.")
    
    for msg in results['messages']:
        print(f"--- Email from {msg['sender']} ---")
        print(f"Subject: {msg['subject']}")
        print(f"Attachments: {len(msg['attachments'])}")
        
        for att in msg['attachments']:
            filepath = att['filepath']
            print(f"  File: {att['filename']} -> {filepath}")
            if filepath.endswith('.pdf'):
                print("  Parsing PDF...")
                parsed = parse_pdf(filepath)
                text = parsed['text']
                preview = text[:200].replace('\n', ' ')
                print(f"  PDF Parsed. Has content: {parsed['has_content']}. Pages: {parsed['page_count']}")
                print(f"  Preview: {preview}...")

if __name__ == '__main__':
    main()
