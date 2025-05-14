# deleteApps
Delete Applications in IQ Server with latest scan older than given data.

# WARNING - Deleting an application is a destructive action that will permanently remove the application and all data associated with it. Please proceed with caution when deleting applications in bulk. 

# Edit Configuration in deleteApps.py :
IQ_SERVER_URL - Replace with your IQ Server URL

USERNAME - Replace with your username

PASSWORD - Replace with your password

CUTOFF_DATE_STR - Replace 

# Run
1. Install requests - pip install requests
2. You can set IQ_SERVER_URL, USERNAME, PASSWORD, and CUTOFF_DATE_STR at the top of the script. If any of these are None, the script will prompt you to enter them when it runs. Passwords are entered securely using getpass.
3. python deleteApps.py
4. Script will find applications to delete, provide a list then prompt you to enter "yes" if you wish to continue and delete the applications, or "no" to exit without deletion.

Please ensure you have thoroughly tested the script in a lower environment. This script is not supported by Sonatype. 


How the Script Works:

Parameters:
You can set IQ_SERVER_URL, USERNAME, PASSWORD, and CUTOFF_DATE_STR at the top of the script.
If any of these are None, the script will prompt you to enter them when it runs. Passwords are entered securely using getpass.

Get All Applications:
It calls the /api/v2/applications endpoint to get a list of all applications.

Get Scan History:
For each application, it calls the /api/v2/reports/applications/{applicationInternalId} endpoint to get its scan history.

It extracts the evaluationDate from the latest report (assuming the first report in the response is the latest). You might need to adjust the key (evaluationDate) and the date parsing logic based on your IQ Server's actual API response format.

Check Condition:
It compares the application's latest scan date with the cutoff_date.
If the latest scan is older than the cutoff date, the application is added to a list of candidates for deletion.

Prompt for Deletion:
It lists all applications marked for deletion.
It then prominently warns the user about the permanent nature of the deletion and asks for confirmation (yes/no).

Delete Applications:
If the user confirms with "yes", it iterates through the list and calls the DELETE /api/v2/applications/{applicationInternalId} endpoint for each application.
If the user does not confirm, the script exits.

Important Considerations and Potential Adjustments:
API Versioning: Sonatype IQ Server APIs can change between versions. The script uses /api/v2/. Ensure these are the correct paths for your server version. If you are on an older version, you might need to use /rest/ or other paths.

Internal ID vs. Public ID: The API documentation (and the links you provided) sometimes refers to applicationId (which is often the public ID) and internalId. The "Delete Application" API specifically uses the applicationInternalId. The script tries to fetch and use the internalId.

Date Fields in Scan History: The field name for the scan date (evaluationDate in the script) and its format can vary. Inspect the actual JSON response from the retrieving-the-scan-report-history API for one of your applications to confirm the correct field name and date format. The script currently tries to parse a couple of common ISO 8601 formats.

Pagination: If you have a very large number of applications or scan reports, the APIs might use pagination. This script does not currently handle pagination for get_all_applications or get_application_scan_history. If you encounter issues where not all items are retrieved, you'll need to add pagination logic (checking for nextPage tokens or similar in the API responses and making subsequent requests).

Error Handling: The script includes basic error handling for network requests and JSON decoding. You might want to enhance this based on specific error codes or messages from the IQ Server.

Rate Limiting: If you are processing a very large number of applications, be mindful of potential API rate limits on the IQ Server. You might need to add delays between API calls if you encounter issues.

Testing: Test this script thoroughly in a non-production environment first! Deleting applications is irreversible. Start by commenting out the delete_application call and just printing which applications would be deleted.

Authentication: The script uses basic authentication. Ensure this is appropriate for your IQ Server setup.

Timezones: The script converts both the cutoff date and the scan dates to UTC for consistent comparison. This is generally a good practice.
Remember to replace placeholder values and adapt the API interaction parts (especially date parsing) to match your specific Sonatype IQ Server version and configuration.







