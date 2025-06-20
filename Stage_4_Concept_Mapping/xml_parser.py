import xml.etree.ElementTree as ET
import pandas as pd

def parse_icd10cm_xml_to_csv(xml_file_path: str, output_csv_path: str):
    """
    Parses the official ICD-10-CM Tabular XML file and converts the diagnosis
    codes and their descriptions into a structured CSV file.

    Args:
        xml_file_path (str): The full path to your icd10cm-tabular-....xml file.
        output_csv_path (str): The path where the output CSV will be saved.
    """
    print(f"--- Starting XML Parsing ---")
    print(f"Reading from: '{xml_file_path}'")

    try:
        # Parse the entire XML file into an ElementTree object.
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        # This list will store all the extracted records.
        records = []

        # The diagnosis codes are nested within chapter -> section -> diag.
        # We use .//diag to find all 'diag' elements anywhere in the tree.
        for diag in root.findall('.//diag'):
            # Find the 'name' and 'desc' tags within each 'diag' element.
            name_tag = diag.find('name')
            desc_tag = diag.find('desc')

            # Ensure both tags exist to avoid errors.
            if name_tag is not None and desc_tag is not None:
                # Extract the text content, stripping whitespace.
                # The 'if tag.text else' part handles empty tags gracefully.
                code = name_tag.text.strip() if name_tag.text else ''
                description = desc_tag.text.strip() if desc_tag.text else ''

                # Add the extracted data as a dictionary to our list.
                records.append({
                    'CUI': code,  # Using 'CUI' as the column name for consistency
                    'Description': description
                })
        
        if not records:
            print("⚠️ Warning: No diagnosis codes were found. Please check the XML file structure.")
            return

        # Convert the list of dictionaries into a pandas DataFrame.
        df = pd.DataFrame(records)

        # Save the DataFrame to a CSV file.
        df.to_csv(output_csv_path, index=False, encoding='utf-8')

        print(f"\n✅ Success! Extracted {len(df)} diagnosis codes.")
        print(f"   Knowledge base saved to: '{output_csv_path}'")

    except ET.ParseError as e:
        print(f"❌ XML Parse Error: The file '{xml_file_path}' may be corrupted or malformed.")
        print(f"   Details: {e}")
    except FileNotFoundError:
        print(f"❌ File Not Found Error: The file '{xml_file_path}' does not exist.")
        print("   Please make sure the path and filename are correct.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")


# ==============================================================================
# How to Use This Script
# ==============================================================================
if __name__ == "__main__":
    # --- Configuration ---
    # 1. Update this with the name of your full XML file.
    INPUT_XML_FILE = r"input_files\icd10cm-tabular-April-2025.xml"
    
    # 2. This will be the name of your final CSV knowledge base.
    OUTPUT_CSV_FILE = r"output_files\icd_code_with_descriptions.csv" 
    
    # --- Run the conversion ---
    parse_icd10cm_xml_to_csv(INPUT_XML_FILE, OUTPUT_CSV_FILE)