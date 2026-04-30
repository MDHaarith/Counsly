import json
import os
from tnea_lib.extractor import TNEAPDFExtractor

def main():
    # Configuration - use absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(script_dir, "TNEA_2025_Information_abt_colleges_copy.pdf")
    output_path = os.path.join(script_dir, "output.json")
    
    # Initialize extractor
    extractor = TNEAPDFExtractor(pdf_path)
    
    print(f"Starting fresh extraction from: {pdf_path}")
    
    # Perform extraction
    colleges = extractor.parse_colleges()
    
    # Save to fresh output.json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(colleges, f, indent=2)
    
    print(f"Successfully extracted {len(colleges)} colleges.")
    print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    main()
