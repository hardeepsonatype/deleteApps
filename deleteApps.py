import requests
import getpass
from datetime import datetime, timezone

# --- Script Parameters ---
# Set these variables directly in the script, or leave them as None to be prompted
IQ_SERVER_URL = None  # Example: "http://localhost:8070"
USERNAME = None       # Example: "admin"
PASSWORD = None       # Example: "admin123"
# Cutoff date in YYYY-MM-DD format. Applications with the latest scan older than this date will be targeted.
CUTOFF_DATE_STR = None # Example: "2023-01-01"

# --- Helper Functions --- (These remain the same)
def get_input_if_none(value, prompt_message, is_password=False):
    if value is None:
        if is_password:
            return getpass.getpass(prompt_message)
        else:
            return input(prompt_message)
    return value

def get_all_applications(base_url, auth):
    api_url = f"{base_url}/api/v2/applications"
    try:
        response = requests.get(api_url, auth=auth)
        response.raise_for_status()
        return response.json().get('applications', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching applications: {e}")
        return []
    except ValueError as e: # Catch JSON decoding errors
        print(f"Error decoding JSON response from {api_url}: {e}")
        print(f"Response text: {response.text}")
        return []


def get_application_scan_history(base_url, app_id_for_report, auth): # Renamed param for clarity
    """
    Retrieves the scan report history for a specific application.
    API: GET /api/v2/reports/applications/{applicationInternalId}
    Note: The API docs refer to it as applicationInternalId, which we're now using app.get('id') for.
    """
    api_url = f"{base_url}/api/v2/reports/applications/{app_id_for_report}"
    try:
        response = requests.get(api_url, auth=auth)
        response.raise_for_status()
        return response.json() # Returns a list of reports
    except requests.exceptions.RequestException as e:
        print(f"Error fetching scan history for application ID {app_id_for_report}: {e}")
        return []
    except ValueError as e: # Catch JSON decoding errors
        print(f"Error decoding JSON response from {api_url}: {e}")
        print(f"Response text: {response.text}")
        return []


def delete_application(base_url, app_id_to_delete, auth): # Renamed param for clarity
    """
    Deletes a specific application.
    API: DELETE /api/v2/applications/{applicationInternalId}
    Note: The API docs refer to it as applicationInternalId.
    """
    api_url = f"{base_url}/api/v2/applications/{app_id_to_delete}"
    try:
        response = requests.delete(api_url, auth=auth)
        response.raise_for_status()
        print(f"Successfully deleted application with ID: {app_id_to_delete}") # Changed to ID
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error deleting application with ID {app_id_to_delete}: {e}") # Changed to ID
        if response is not None:
            print(f"Response status code: {response.status_code}")
            print(f"Response text: {response.text}")
        return False

def main():
    global IQ_SERVER_URL, USERNAME, PASSWORD, CUTOFF_DATE_STR

    print("--- Sonatype IQ Server Application Cleanup Script ---")

    IQ_SERVER_URL = get_input_if_none(IQ_SERVER_URL, "Enter Sonatype IQ Server URL (e.g., http://localhost:8070): ")
    USERNAME = get_input_if_none(USERNAME, "Enter IQ Server Username: ")
    PASSWORD = get_input_if_none(PASSWORD, "Enter IQ Server Password: ", is_password=True)
    CUTOFF_DATE_STR = get_input_if_none(CUTOFF_DATE_STR, "Enter the cutoff date (YYYY-MM-DD) to delete applications older than: ")

    try:
        cutoff_date = datetime.strptime(CUTOFF_DATE_STR, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return

    auth = (USERNAME, PASSWORD)

    print("\nFetching all applications from IQ Server...")
    applications = get_all_applications(IQ_SERVER_URL, auth)

    if not applications:
        print("No applications found or an error occurred.")
        return

    print(f"Found {len(applications)} applications.")
    if applications and 'id' not in applications[0] and 'internalId' not in applications[0] : # Basic check if primary ID field is missing
        print("\n--- DEBUG: First application data (ID field check) ---")
        print(applications[0])
        print("--- End DEBUG ---")
        print("\n*** WARNING: The field 'id' (or 'internalId') might be missing from the application data.")
        print("Please ensure the script is using the correct field name to fetch the application ID required for subsequent API calls.")


    applications_to_delete = []
    print("\nChecking application scan histories...")

    for app_idx, app in enumerate(applications):
        app_name = app.get('name', f'UnnamedApp_Idx{app_idx}')
        app_public_id = app.get('publicId', 'UnknownPublicId') # Still useful for display

        # *** Using app.get('id') as per your feedback that it works for internalId equivalent ***
        app_id_for_apis = app.get('id')

        if not app_id_for_apis:
            print(f"Skipping application '{app_name}' (Public ID: {app_public_id}) as its 'id' field (used as internal ID) is missing or null.")
            if app_idx == 0 :
                 print(f"  Raw data for this app (if 'id' is missing): {app}")
            continue

        print(f"\nProcessing application: {app_name} (Public ID: {app_public_id}, ID for API calls: {app_id_for_apis})")

        scan_history = get_application_scan_history(IQ_SERVER_URL, app_id_for_apis, auth)

        if not scan_history:
            print(f"  No scan history found for {app_name} (ID: {app_id_for_apis}). Skipping.")
            continue

        latest_scan_report = scan_history[0]
        latest_scan_date_str = latest_scan_report.get('evaluationDate')

        if not latest_scan_date_str:
            print(f"  Could not determine latest scan date for {app_name} (ID: {app_id_for_apis}). Skipping.")
            continue

        try:
            # datetime.fromisoformat() is generally the most robust for ISO 8601 date strings.
            latest_scan_date = datetime.fromisoformat(latest_scan_date_str)
            latest_scan_date = latest_scan_date.astimezone(timezone.utc) # Ensure UTC for comparison
            print(f"  Latest scan date: {latest_scan_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        except ValueError as e_iso:
            print(f"  Could not parse scan date '{latest_scan_date_str}' for {app_name} using datetime.fromisoformat(): {e_iso}.")
            if latest_scan_date_str.endswith('Z'):
                print(f"    Attempting fallback strptime parsing for Z-formatted date.")
                try:
                    if '.' in latest_scan_date_str:
                        latest_scan_date = datetime.strptime(latest_scan_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                    else:
                        latest_scan_date = datetime.strptime(latest_scan_date_str, "%Y-%m-%dT%H:%M:%S%Z")
                    latest_scan_date = latest_scan_date.replace(tzinfo=timezone.utc)
                    print(f"    Fallback Z-format parsed: {latest_scan_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                except ValueError as e_strptime_z:
                    print(f"    Fallback strptime for Z-format also failed: {e_strptime_z}. Skipping.")
                    continue
            else:
                print(f"    No simple strptime fallback for this non-Z date format. Application will be skipped.")
                continue
        except AttributeError: # datetime.fromisoformat() not available (Python < 3.7)
            print(f"  datetime.fromisoformat() not available (requires Python 3.7+). Scan date '{latest_scan_date_str}' for {app_name} could not be parsed. Skipping.")
            continue


        if latest_scan_date < cutoff_date:
            print(f"  >> Marked for deletion: Latest scan ({latest_scan_date.strftime('%Y-%m-%d')}) is older than cutoff ({CUTOFF_DATE_STR}).")
            applications_to_delete.append({
                "name": app_name,
                "publicId": app_public_id,
                "id_for_apis": app_id_for_apis, # Store the ID used for deletion
                "latest_scan": latest_scan_date.strftime('%Y-%m-%d')
            })
        else:
            print(f"  Not marked for deletion: Latest scan ({latest_scan_date.strftime('%Y-%m-%d')}) is not older than cutoff ({CUTOFF_DATE_STR}).")


    if not applications_to_delete:
        print("\nNo applications found meeting the deletion criteria (or all were skipped).")
        return

    print("\n--- Applications Marked for Deletion ---")
    for i, app_info in enumerate(applications_to_delete):
        print(f"{i+1}. Name: {app_info['name']}, Public ID: {app_info['publicId']}, API ID: {app_info['id_for_apis']}, Latest Scan: {app_info['latest_scan']}")

    print("\nWARNING: Deleting an application is a destructive action that will permanently remove the application and all data associated with it.")
    confirm = input(f"Are you sure you want to delete these {len(applications_to_delete)} applications? (yes/no): ").strip().lower()

    if confirm == 'yes':
        print("\n--- Deleting Applications ---")
        deleted_count = 0
        failed_count = 0
        for app_info in applications_to_delete:
            print(f"Deleting application: {app_info['name']} (API ID: {app_info['id_for_apis']})...")
            if delete_application(IQ_SERVER_URL, app_info['id_for_apis'], auth):
                deleted_count +=1
            else:
                failed_count +=1
        print(f"\nDeletion complete. Successfully deleted: {deleted_count}, Failed to delete: {failed_count}")
    else:
        print("\nDeletion cancelled by the user.")

if __name__ == "__main__":
    main()
