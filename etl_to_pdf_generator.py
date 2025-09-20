import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from pymongo import MongoClient
import os

# --- Configuration ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "etl_db"
COLLECTION_NAME = "students"

def get_data_from_mongodb():
    """
    Connects to MongoDB and retrieves data from the specified collection.

    Returns:
        list: A list of dictionaries representing the documents, or None if an error occurs.
    """
    client = None
    try:
        # Create a MongoClient to connect to the MongoDB instance.
        client = MongoClient(MONGO_URI)
        # The ismaster command is a quick way to check if the connection is active.
        client.admin.command('ismaster')
        print("Connected to MongoDB successfully!")
        
        db = client.get_database(DB_NAME)
        collection = db[COLLECTION_NAME]
        
        # Find all documents in the collection and convert the cursor to a list.
        # We also remove the MongoDB '_id' field as it's not JSON serializable.
        data = list(collection.find({}, {'_id': False}))
        print(f"Retrieved {len(data)} documents from '{COLLECTION_NAME}'.")
        return data

    except Exception as e:
        print(f"Error retrieving data from MongoDB: {e}")
        return None
    finally:
        if client:
            client.close()

def generate_pdf(data):
    """
    Generates a PDF report from the provided data.

    Args:
        data (list): A list of dictionaries with student information.
    """
    try:
        doc = SimpleDocTemplate("student_report.pdf", pagesize=letter)
        styles = getSampleStyleSheet()
        flowables = []

        # Title
        title_style = styles['Title']
        title_style.alignment = 1  # Center alignment
        flowables.append(Paragraph("Student Academic Report", title_style))
        flowables.append(Spacer(1, 12))

        # Check if data exists before processing
        if not data:
            no_data_style = ParagraphStyle(
                name='NoDataStyle',
                parent=styles['Normal'],
                alignment=1,
                textColor=colors.red
            )
            flowables.append(Paragraph("No data found to generate the report.", no_data_style))
        else:
            # Table data headers
            table_data = [['Name', 'Roll No.', 'Grade', 'Result']]
            for student in data:
                table_data.append([
                    student.get('name', 'N/A'),
                    student.get('roll_no', 'N/A'),
                    student.get('grade', 'N/A'),
                    student.get('result', 'N/A')
                ])

            # Create table and apply styles
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ])
            
            table = Table(table_data)
            table.setStyle(table_style)
            
            flowables.append(table)
            
            # Signature and Date
            flowables.append(Spacer(1, 24))
            flowables.append(Paragraph("Signature:", styles['Normal']))
            flowables.append(Spacer(1, 12))
            flowables.append(Paragraph("Date:", styles['Normal']))
            
        doc.build(flowables)
        print("PDF report 'student_report.pdf' generated successfully!")

    except Exception as e:
        print(f"Error generating PDF report: {e}")

def main():
    """
    Main function to orchestrate the ETL process.
    """
    print("--- Starting ETL Process ---")
    
    # Extract data from MongoDB
    data = get_data_from_mongodb()

    # Corrected check: check if the data list is not None and not empty.
    if data is not None and len(data) > 0:
        # Transform and Load (generate PDF)
        generate_pdf(data)
    else:
        print("No data retrieved or an error occurred. Cannot generate PDF.")

if __name__ == "__main__":
    main()
