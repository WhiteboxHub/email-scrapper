import csv

def log_csv(contact, extracted_by, extraction_run_end, filename="extracted_contacts.csv"):
    file_exists = False
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            file_exists = True
    except FileNotFoundError:
        pass
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                [field for field in contact.__dataclass_fields__] +
                ['extracted_by', 'extraction_run_end']
            )
        writer.writerow(
            [getattr(contact, field) for field in contact.__dataclass_fields__] +
            [extracted_by, extraction_run_end]
        )

def log_summary(extracted_by, extraction_run_end, count, filename="extracted_contacts.csv"):
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([])
        writer.writerow(['Summary'])
        writer.writerow(['Extracted By', extracted_by])
        writer.writerow(['Extraction Run End', extraction_run_end])
        writer.writerow(['Total Extracted', count])

def report_summary(count):
    print(f"Extracted {count} new contacts today.")