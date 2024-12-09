import PyPDF2 as pypdf2


def pdf_to_text(pdf_path, output_path):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = pypdf2.PdfReader(pdf_file)

        text = ''
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return text.strip()


def extract_resume_info(pdf_path, output_path):
    # Write the extracted text to a text file
    extracted_info = pdf_to_text(pdf_path, output_path)
    with open(output_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(extracted_info)
