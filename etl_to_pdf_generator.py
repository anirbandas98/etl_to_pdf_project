import json
import logging
import os
from datetime import datetime
from pymongo import MongoClient
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- Configuration ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "etl_db"
COLLECTION_NAME = "students"
OUTPUT_DIR = "pdf_reports"
OUTPUT_FILENAME = os.path.join(OUTPUT_DIR, "student_report.pdf")

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("etl_process.log"),
        logging.StreamHandler()
    ]
)

def connect_to_mongodb():
    """
    Establishes a connection to the MongoDB database.

    Returns:
        MongoClient: The MongoClient object, or None if connection fails.
    """
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
        logging.info("Connected to MongoDB successfully!")
        return client
    except Exception as e:
        logging.error(f"Error connecting to MongoDB: {e}", exc_info=True)
        return None

def extract_data():
    """
    Extracts data from the MongoDB collection.

    Returns:
        list: A list of dictionaries with raw student data.
    """
    logging.info("--- Starting Data Extraction ---")
    client = connect_to_mongodb()
    if client is None:
        logging.error("Exiting due to database connection failure.")
        return []

    try:
        db = client.get_database(DB_NAME)
        collection = db[COLLECTION_NAME]
        
        # Check if the collection exists
        if COLLECTION_NAME not in db.list_collection_names():
            logging.error(f"Collection '{COLLECTION_NAME}' does not exist.")
            return []

        # Get the documents from the collection.
        data = list(collection.find())
        
        if not data:
            logging.warning("No data found in the collection.")

        logging.info(f"Extracted {len(data)} records from MongoDB.")
        return data
        
    except Exception as e:
        logging.error(f"An error occurred during data extraction: {e}", exc_info=True)
        return []
    finally:
        if client:
            client.close()
            logging.info("MongoDB connection closed.")
        logging.info("--- Data Extraction Finished ---")

def transform_data(raw_data):
    """
    Transforms the raw student data.

    Args:
        raw_data (list): A list of dictionaries with student data.

    Returns:
        list: A list of lists with transformed data for PDF table.
    """
    logging.info("--- Starting Data Transformation ---")
    transformed_data = []
    
    for record in raw_data:
        # Check for required fields and provide default values
        name = record.get("name", "N/A")
        if name == "N/A":
            logging.warning(f"Record with roll_no {record.get('roll_no', 'N/A')} is missing a 'name' field. Using 'N/A'.")
        
        roll_no = record.get("roll_no", "N/A")
        grade = record.get("grade", "N/A")
        fees_paid = record.get("fees_paid", False)
        
        # Determine the result based on fees paid and grade
        if not fees_paid:
            result = "Fees Due"
        elif grade in ["A", "B", "C", "D"]:
            result = "Pass"
        else:
            result = "Fail"
            
        transformed_data.append([
            name,
            roll_no,
            grade,
            "Yes" if fees_paid else "No",
            result
        ])

    logging.info("Data transformation complete.")
    return transformed_data

def generate_pdf(data):
    """
    Generates a PDF report from the transformed data.

    Args:
        data (list): A list of lists with data for the PDF table.
    """
    logging.info("Starting PDF generation...")
    
    # Ensure the output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logging.info(f"Created output directory: {OUTPUT_DIR}")

    # Check if the file already exists and remove it
    if os.path.exists(OUTPUT_FILENAME):
        logging.info(f"Existing file '{OUTPUT_FILENAME}' found. Removing it.")
        os.remove(OUTPUT_FILENAME)

    try:
        doc = SimpleDocTemplate(OUTPUT_FILENAME, pagesize=letter)
        styles = getSampleStyleSheet()
        flowables = []
        
        # Title
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Normal'],
            fontSize=18,
            leading=22,
            alignment=1,
            spaceAfter=12
        )
        title = Paragraph("Student Result Report", title_style)
        flowables.append(title)
        
        # Add a note about the data
        info_style = styles['Normal']
        info = Paragraph(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style)
        flowables.append(info)
        
        # Add a note about the data limit for the PDF
        record_note = Paragraph(
            f"Total records processed: {len(data)}",
            info_style
        )
        flowables.append(record_note)
        flowables.append(Spacer(1, 12))
        
        # Define table headers
        header_data = [["name", "roll_no", "grade", "fees_paid", "result"]]
        
        # Combine header with page data
        table_data = header_data + data
        
        # Corrected column widths to fix the formatting
        available_width = letter[0] - doc.leftMargin - doc.rightMargin
        col_widths = [
            available_width * 0.25, # name
            available_width * 0.15, # roll_no
            available_width * 0.1,  # grade
            available_width * 0.15, # fees_paid
            available_width * 0.15, # result
        ]
        
        table = Table(table_data, colWidths=col_widths)
        
        # Add style to the table
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black)
        ])
        table.setStyle(style)
        flowables.append(table)
        
        # Build the PDF
        doc.build(flowables)
        
        logging.info(f"PDF report successfully generated at: {os.path.abspath(OUTPUT_FILENAME)}")
        
    except Exception as e:
        logging.error(f"Failed to generate PDF report: {e}", exc_info=True)

def main():
    """
    Main function to run the ETL process and generate the PDF report.
    """
    logging.info("--- Starting ETL Process ---")
    
    # Extract data from MongoDB
    raw_data = extract_data()
    
    if raw_data:
        # Transform all records
        transformed_data = transform_data(raw_data)
        
        # Generate the PDF report with all records
        generate_pdf(transformed_data)
    else:
        logging.error("No data available to generate PDF. Check previous logs for errors.")

    logging.info("--- ETL Process Finished ---")

if __name__ == "__main__":
    main()
