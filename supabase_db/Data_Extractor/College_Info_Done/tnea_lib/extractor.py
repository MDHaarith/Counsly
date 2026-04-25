import os
import re
import json

from .raw_stream import decode_hex_string, extract_blocks_from_pdf

DISTRICT_FROM_NAME_RE = re.compile(r',\s*([A-Za-z .&-]+?)\s+District\b', re.I)
DISTRICT_FROM_ADDRESS_RE = re.compile(r'([A-Za-z .&-]+?)\s+DISTRICT\b', re.I)

class TNEAPDFExtractor:
    """
    A custom raw PDF parser tailored for TNEA_2025_Information_abt_colleges.pdf.
    Extracts text directly from FlateDecode streams and decodes custom font encoding.
    """
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def _decode_hex_string(self, hex_str):
        """
        Decodes a hex string using the custom 4-digit chunk and +29 decimal shift.
        """
        return decode_hex_string(hex_str)

    def extract_raw_text(self):
        """
        Extracts raw text from PDF streams using a very robust manual stream locator.
        """
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF file not found at {self.pdf_path}")
        full_text_blocks = extract_blocks_from_pdf(self.pdf_path)
        return "\n".join(full_text_blocks)

    def parse_colleges(self):
        """
        Extracts exactly 466 colleges by systematically processing each page footer.
        """
        raw_text = self.extract_raw_text()
        text = "\n".join([line.strip() for line in raw_text.split("\n")])
        
        footer_pattern = re.compile(r"Page\s+(\d+)\s*/\s*466", re.I)
        footers = list(footer_pattern.finditer(text))
        
        colleges = []
        
        first_code_match = re.search(r"\n1\s*\nUniversity Departments of Anna University, Chennai - CEG Campus", text, re.I)
        first_code_pos = first_code_match.start() + 1 if first_code_match else 0
        
        for i in range(len(footers)):
            page_num = int(footers[i].group(1))
            f_curr_pos = footers[i].start()
            f_prev_pos = footers[i-1].end() if i > 0 else 0
            
            if i == 0:
                block = text[first_code_pos:f_curr_pos].strip()
            else:
                block = text[f_prev_pos:f_curr_pos].strip()
            
            if "Dean/Principal" not in block:
                next_pos = footers[i+1].start() if i < len(footers)-1 else len(text)
                after_block = text[f_curr_pos:next_pos].strip()
                if "Dean/Principal" in after_block:
                    block = after_block
            
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            college_code = None
            college_name = None
            
            # Search for the code at the top
            for j, line in enumerate(lines):
                m_full = re.match(r"^(\d{1,4})\s+(.*)$", line)
                if m_full:
                    college_code = m_full.group(1)
                    college_name = m_full.group(2).strip()
                    # Capture remaining name lines
                    for k in range(j+1, len(lines)):
                        if "Dean/Principal" in lines[k] or "Address" in lines[k]: break
                        college_name += " " + lines[k]
                    break
                elif line.isdigit() and 1 <= len(line) <= 4:
                    college_code = line
                    name_parts = []
                    for k in range(j+1, len(lines)):
                        if "Dean/Principal" in lines[k] or "Address" in lines[k]: break
                        name_parts.append(lines[k])
                    college_name = " ".join(name_parts).strip()
                    break
            
            if college_code and college_name:
                college_name = re.sub(r"\(Previous Year Data\)", "", college_name, flags=re.I).strip()
                details = self._extract_detailed_fields(block, college_code, college_name, page_num)
                # Keep every page's entry to reach exactly 466
                colleges.append(details)
                    
        return colleges

    def _extract_detailed_fields(self, block, code, name, page_num):
        def clean_num(val):
            if val is None: return 0
            try:
                digits = re.sub(r'\D', '', str(val))
                return int(digits) if digits else 0
            except: return 0

        def clean_null(val):
            v = str(val).strip()
            if not v or v.lower() in ['x', '0000000000', '-', 'nil', 'none']: return None
            return v

        def normalize_district_text(val):
            text = str(val).strip().upper()
            text = re.sub(r'\bDISTRICT\b', '', text, flags=re.I).strip(' ,.-')
            text = re.sub(r'\bPINCODE\b.*$', '', text, flags=re.I).strip(' ,.-')
            text = re.sub(r'\b\d{6}\b$', '', text).strip(' ,.-')
            text = re.sub(r'\s+', ' ', text).strip()
            if not text or text.isdigit() or text in {'TALUK', 'PINCODE'}:
                return ''
            return text

        def infer_district(name, address, taluk, pincode):
            for source, pattern in [
                (name, DISTRICT_FROM_NAME_RE),
                (address, DISTRICT_FROM_ADDRESS_RE),
            ]:
                if source:
                    m = pattern.search(source)
                    if m:
                        district = normalize_district_text(m.group(1))
                        if district:
                            return district
            district = normalize_district_text(data.get('District', ''))
            if district:
                return district
            return ''

        data = {
            "College_Code": code,
            "PDF_Page_Number": page_num + 64,
            "College_Name": name,
            "Dean_Principal": "",
            "Bank_A_c_No": None,
            "Address": "",
            "Bank_Name": None,
            "Taluk": "",
            "District": "",
            "Distance_in_KMS_from_Dist_HQ": 0,
            "Pincode": 0,
            "Nearest_Railway_Station": "",
            "Phone_Fax": None,
            "Email-ID": "",
            "Distance_in_KMS_from_Nearest_Railway_Station": 0,
            "Website": "",
            "Anti_Ragging_Phone_No": None,
            "Autonomous_Status": "Non-Autonomous",
            "Placement_Record": "-",
            "Hostel_Boys_Permanent_or_Rental": "",
            "Hostel_Girls_Permanent_or_Rental": "",
            "Type_of_Mess": "",
            "Room_Rent": "0",
            "Electricity_Charges": "0",
            "Caution_Deposit": 0,
            "Establishment_Charges": 0,
            "Admission_Fees": 0,
            "Transport_Facilities": "no",
            "Min_Transport_Charges": 0,
            "Max_Transport_Charges": 0,
            "Internal_Page_Number": page_num
        }
        
        patterns = {
            "Dean_Principal": r"Dean\s*/\s*Principal\s+(.*?)(?=\n|$)",
            "Address": r"Address\s+(.*?)(?=Taluk)",
            "Taluk": r"Taluk\s+(.*?)(?=\n|$)",
            "District": r"District\s+(.*?)(?=\n|$)",
            "Pincode": r"Pincode\s+(\d+)",
            "Phone_Fax": r"Phone\s*/\s*Fax\s+(.*?)(?=\n|$)",
            "Email-ID": r"Email\s*-\s*ID\s+(.*?)(?=\n|$)",
            "Website": r"Website\s+(.*?)(?=\n|$)",
            "Placement_Record": r"Placement\s+(.*?)(?=\n|$)",
            "Bank_A_c_No": r"Bank\s+A/c\s+No\s+(.*?)(?=\n|$)",
            "Bank_Name": r"Bank\s+Name\s+(.*?)(?=\n|$)",
            "Distance_in_KMS_from_Dist_HQ": r"Distance\s+in\s+KMS\s+from\s+Dist\.\s+HQ\s+(\d+)",
            "Nearest_Railway_Station": r"Nearest\s+Railway\s+Station\s+(.*?)(?=\n|$)",
            "Distance_in_KMS_from_Nearest_Railway_Station": r"Distance\s+in\s+KMS\s+from\s+Nearest\s+Railway\s+Station\s+(\d+)",
            "Minority_Status": r"Minority\s+Status\s+(.*?)(?=\n|$)",
            "Autonomous_Status": r"Autonomous\s+Status\s+(.*?)(?=\n|$)",
            "Anti_Ragging_Phone_No": r"Anti\s*-\s*Ragging\s+Phone\s+No\s+(.*?)(?=\n|$)"
        }

        for key, pattern in patterns.items():
            if key == "Address":
                match = re.search(pattern, block, re.DOTALL | re.I)
                if match: data[key] = " ".join(match.group(1).split()).strip()
            else:
                match = re.search(pattern, block, re.I)
                if match:
                    val = match.group(1).strip()
                    if key in ["Pincode", "Distance_in_KMS_from_Dist_HQ", "Distance_in_KMS_from_Nearest_Railway_Station"]:
                        data[key] = clean_num(val)
                    elif key in ["Bank_A_c_No", "Bank_Name"]:
                        data[key] = clean_null(val)
                    elif key == "Autonomous_Status":
                        data[key] = "Autonomous" if val.lower() == 'yes' else "Non-Autonomous"
                    elif key in ["Phone_Fax", "Anti_Ragging_Phone_No"]:
                        v = clean_null(val)
                        if v:
                            digits = re.sub(r'\D', '', v)
                            data[key] = int(digits) if digits else None
                    elif key == "District":
                        data[key] = normalize_district_text(val)
                    else:
                        data[key] = val

        # Hostel
        por = re.search(r"Permanent\s+or\s+Rental\s+\(P/R\)\s+(\w+)\s+(\w+)", block, re.I)
        if por:
            data["Hostel_Boys_Permanent_or_Rental"] = por.group(1).capitalize()
            data["Hostel_Girls_Permanent_or_Rental"] = por.group(2).capitalize()
        
        mess = re.search(r"Type\s+of\s+Mess\s+\(Veg/NV\)\s+(\w+)\s+(\w+)", block, re.I)
        if mess: data["Type_of_Mess"] = mess.group(1).lower()
        
        rent = re.search(r"Room\s+Rent\s+(\d+)\s+(\d+)", block, re.I)
        if rent: data["Room_Rent"] = rent.group(1)
        
        elec = re.search(r"Electricity\s+Charges\s+(\d+)\s+(\d+)", block, re.I)
        if elec: data["Electricity_Charges"] = elec.group(1)

        single_nums = ["Caution_Deposit", "Establishment_Charges", "Admission_Fees", "Min_Transport_Charges", "Max_Transport_Charges"]
        for k in single_nums:
            p = k.replace("_", r"\s*")
            m = re.search(p + r"\s+(\d+)", block, re.I)
            if m: data[k] = clean_num(m.group(1))

        trans = re.search(r"Transport\s+Facilities\s+\(Y/N\)\s+(\w+)", block, re.I)
        if trans: data["Transport_Facilities"] = trans.group(1).lower()

        data["District"] = infer_district(data.get("College_Name", name), data.get("Address", ""), data.get("Taluk", ""), data.get("Pincode", 0)) or data.get("District", "")

        # Courses
        courses = []
        table_start = re.search(r"Valid\s+Upto", block, re.I)
        if table_start:
            table_text = block[table_start.end():table_start.end()+2500]
            table_rows = re.findall(r"(?:^|\n)(\d+)\s+([A-Z]{2})\s+(\d+)\s+(\d{4})\s+(Yes|No)\s+(.*?)(?=\n|$)", table_text)
            for row in table_rows:
                courses.append({
                    "Branch_Code": row[1],
                    "Approved_Intake": int(row[2]),
                    "Year_Starting": int(row[3]),
                    "NBA_Accredited": row[4],
                    "Valid_Upto": row[5].strip()
                })
        data["courses"] = courses
        return data
