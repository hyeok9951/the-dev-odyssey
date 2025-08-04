public with sharing class ContactCsvExportController {
    public String csvResult { get; private set; }
    public String fileName { get; private set; }

    // Constructor for extension (must be StandardController for VF extension)
    public ContactCsvExportController(ApexPages.StandardController controller) {
        fileName = 'ContactExport_' + Datetime.now().format('yyyyMMdd_HHmmss') + '.csv';
        csvResult = ''; // Will be set in initDownload()
    }

    // Action for Visualforce page: prepare CSV
    public PageReference initDownload() {
        csvResult = generateCsv();
        return null;
    }

    // Generates the CSV string
    private String generateCsv() {
        List<String> lines = new List<String>();
        // Add BOM for Excel compatibility and header row
        lines.add('\uFEFF"Name","Email","Phone","CreatedDate"');

        List<Contact> contacts = [
            SELECT Name, Email, Phone, CreatedDate
            FROM Contact
            ORDER BY CreatedDate DESC
            LIMIT 1000
        ];

        for (Contact c : contacts) {
            String line =
                '"' + safe(c.Name) + '",' +
                '"' + safe(c.Email) + '",' +
                '"' + safe(c.Phone) + '",' +
                '"' + safe(stringValue(c.CreatedDate)) + '"';
            lines.add(line);
        }
        return String.join(lines, '\n');
    }

    // CSV getter for VF page
    public String getCsv() {
        ApexPages.currentPage().getHeaders().put(
            'Content-Disposition',
            'attachment; filename=' + fileName
        );
        return csvResult;
    }

    // Helper to safely handle nulls and escape quotes
    private String safe(String value) {
        return value != null ? value.replace('"', '""') : '';
    }
    private String stringValue(Object val) {
        return val != null ? String.valueOf(val) : '';
    }
}
