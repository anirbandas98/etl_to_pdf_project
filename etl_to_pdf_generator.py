# Python script to extract data from MongoDB and generate a PDF report.

# --- Step 1: Import necessary libraries ---
# pymongo is the official Python driver for MongoDB.
# reportlab is a powerful library for creating PDFs in Python.
from pymongo import MongoClient
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --- Step 2: Configuration ---
# You can change these variables to match your MongoDB setup and desired output.
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "etl_db"
COLLECTION_NAME = "students"
OUTPUT_PDF_PATH = "student_report.pdf"

def connect_to_mongodb():
    """
    Establishes a connection to the MongoDB database.
    
    Returns:
        pymongo.database.Database: The database object if connection is successful,
                                    None otherwise.
    """
    try:
        # Create a MongoClient to connect to the MongoDB instance.
        client = MongoClient(MONGO_URI)
        # Check if the connection is successful by listing database names.
        client.admin.command('ping')
        print("Connected to MongoDB successfully!")
        return client.get_database(DB_NAME)
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def fetch_data(db):
    """
    Fetches all documents from the specified MongoDB collection.

    Args:
        db (pymongo.database.Database): The database object.

    Returns:
        list: A list of dictionaries, where each dictionary is a document
              from the MongoDB collection.
    """
    try:
        collection = db[COLLECTION_NAME]
        # Find all documents in the collection and convert the cursor to a list.
        data = list(collection.find({}))
        print(f"Fetched {len(data)} documents from the '{COLLECTION_NAME}' collection.")
        return data
    except Exception as e:
        print(f"Error fetching data from MongoDB: {e}")
        return []

def generate_pdf(data):
    """
    Generates a PDF report from the provided data.

    Args:
        data (list): The list of dictionaries to be included in the report.
    """
    try:
        # Create a PDF document template.
        doc = SimpleDocTemplate(OUTPUT_PDF_PATH, pagesize=letter)
        story = []
        
        # Get standard ReportLab styles.
        styles = getSampleStyleSheet()

        # Add a title to the document.
        title_style = styles['Title']
        story.append(Paragraph("Student Enrollment Report", title_style))
        story.append(Spacer(1, 12))
        
        # Check if there is data to process.
        if not data:
            no_data_style = styles['Normal']
            no_data_style.textColor = colors.red
            story.append(Paragraph("No data found to generate the report.", no_data_style))
        else:
            # Create a header row for the table.
            table_data = [
                ['Student ID', 'Name', 'Course', 'Grade', 'Enrollment Date', 'Fees Paid']
            ]
            
            # Populate the table with data from MongoDB.
            for doc in data:
                row = [
                    doc.get('student_id', 'N/A'),
                    doc.get('name', 'N/A'),
                    doc.get('course', 'N/A'),
                    doc.get('grade', 'N/A'),
                    doc.get('enrollment_date', 'N/A'),
                    'Yes' if doc.get('fees_paid') else 'No'
                ]
                table_data.append(row)

            # Create the table object and apply a style.
            table = Table(table_data)
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
            ])
            table.setStyle(table_style)
            
            story.append(table)
        
        # Build the PDF document.
        doc.build(story)
        print(f"PDF report generated successfully at '{OUTPUT_PDF_PATH}'.")

    except Exception as e:
        print(f"Error generating PDF: {e}")

def main():
    """
    Main function to orchestrate the ETL process.
    """
    print("--- Starting ETL Process ---")
    
    # 1. Connect to MongoDB and fetch data.
    db = connect_to_mongodb()
    if db:
        data = fetch_data(db)
        
        # 2. Generate the PDF report using the fetched data.
        generate_pdf(data)
    
    print("--- ETL Process Complete ---")

if __name__ == "__main__":
    main()
