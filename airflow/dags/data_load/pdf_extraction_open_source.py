import pymupdf4llm
import pymupdf as fitz
import os
import boto3
import pandas as pd
import uuid
import mysql.connector
from dotenv import load_dotenv
from data_load.db_connection import get_db_connection
from io import BytesIO

load_dotenv()

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

# AWS S3 client initialization
s3_client = boto3.client('s3')

# MySQL connection
db_conn = get_db_connection()


s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)


# Function to extract and process PDF content from S3
def extract_pdf_content_from_s3(pdf_key, s3_input_bucket, s3_output_bucket, output_folder):


    pdf_obj = s3_client.get_object(Bucket=s3_input_bucket, Key=pdf_key)
    pdf_stream = BytesIO(pdf_obj['Body'].read())  # BytesIO object for the PDF file content

    # Correctly opening the PDF from the BytesIO object
    doc = fitz.open(stream=pdf_stream, filetype="pdf")  # Use stream parameter for BytesIO

    all_content = []
    num_pages = doc.page_count
    num_images = 0
    num_tables = 0
    num_tokens = 0

    # Create folder structure in S3 based on PDF file name
    pdf_file_name = os.path.splitext(os.path.basename(pdf_key))[0]
    base_s3_folder = f"Processed_files/{pdf_file_name}"
    image_s3_folder = f"{base_s3_folder}/images"
    table_s3_folder = f"{base_s3_folder}/tables"

    for page_num, page_data in enumerate(range(num_pages), start=1):
        print(f"Processing page {page_num}")
        
        page = doc[page_num - 1]
        
        # Extract tables using PyMuPDF's find_tables method
        tables = page.find_tables()
        
        # Combine all extracted elements
        elements = []
        table_bboxes = [table.bbox for table in tables]  # Table bounding boxes
        
        # Add text blocks (excluding text in tables)
        for block in page.get_text("blocks"):
            block_rect = fitz.Rect(block[:4])
            if not any(block_rect.intersects(table_bbox) for table_bbox in table_bboxes):
                elements.append({"type": "text", "content": block[4], "bbox": block[:4]})
                num_tokens += len(block[4].split())  # Count tokens (words)
        
        # Add images
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            img_name = f"page{page_num}_img{uuid.uuid4()}.{base_image['ext']}"
            img_s3_path = f"{image_s3_folder}/{img_name}"
            
            # Save image locally and upload to S3
            with BytesIO() as img_file:
                img_file.write(image_bytes)
                img_file.seek(0)
                s3_client.upload_fileobj(img_file, s3_output_bucket, img_s3_path)
            
            elements.append({
                "type": "image", 
                "content": img_s3_path, 
                "bbox": page.get_image_bbox(img)
            })
            num_images += 1
        
        # Add tables
        for table in tables:
            table_data = table.extract()
            table_name = f"page{page_num}_table{uuid.uuid4()}.csv"
            table_s3_path = f"{table_s3_folder}/{table_name}"
            
            # Convert table data to DataFrame and save as CSV
            df = pd.DataFrame(table_data)
            
            # Upload CSV to S3
            with BytesIO() as csv_file:
                df.to_csv(csv_file, index=False)
                csv_file.seek(0)
                s3_client.upload_fileobj(csv_file, s3_output_bucket, table_s3_path)
            
            elements.append({"type": "table", "content": table_s3_path, "bbox": table.bbox})
            num_tables += 1
        
        # Sort elements by vertical position on the page
        elements.sort(key=lambda x: x['bbox'][1])
        
        # Add sorted content to all_content
        for elem in elements:
            if elem['type'] == 'text':
                all_content.append({"type": "text", "content": elem['content']})
            elif elem['type'] == 'image':
                all_content.append({"type": "image", "content": elem['content']})
            elif elem['type'] == 'table':
                all_content.append({"type": "table", "content": elem['content']})

    # Insert metadata into MySQL RDS
    cursor = db_conn.cursor()
    query = """
        INSERT INTO bdia_team7_db.pdf_metadata_tbl (file_name, content, number_of_pages, number_of_tokens, number_of_images, number_of_tables)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (pdf_key, str(all_content), num_pages, num_tokens, num_images, num_tables))
    db_conn.commit()
    cursor.close()

    doc.close()
    return all_content


# Function to process all files in the S3 bucket directory
def process_all_pdfs_in_s3_directory(s3_input_bucket, s3_output_bucket, output_folder):
    # List all objects in the input S3 bucket
    response = s3_client.list_objects_v2(Bucket=s3_input_bucket, Prefix="gaia_files/")

    for obj in response.get('Contents', []):
        pdf_key = obj['Key']
        if pdf_key.endswith('.pdf'):
            print(f"Processing {pdf_key}")
            extract_pdf_content_from_s3(pdf_key, s3_input_bucket, s3_output_bucket, output_folder)
