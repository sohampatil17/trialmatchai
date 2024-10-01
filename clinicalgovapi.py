import requests
import json
import xml.etree.ElementTree as ET

def test_new_json_api():
    print("Testing new JSON API (v2):")
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        'query.term': 'heart attack',
        'fields': 'NCTId,BriefTitle,Condition',
        'pageSize': 5
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print("\nStudies Found:")
        
        for study in data.get('studies', []):
            nct_id = study.get('protocolSection', {}).get('identificationModule', {}).get('nctId', 'N/A')
            title = study.get('protocolSection', {}).get('identificationModule', {}).get('briefTitle', 'N/A')
            conditions = study.get('protocolSection', {}).get('conditionsModule', {}).get('conditions', [])
            condition = ', '.join(conditions) if conditions else "N/A"
            
            print(f"\nNCT ID: {nct_id}")
            print(f"Title: {title}")
            print(f"Condition: {condition}")

    except requests.RequestException as e:
        print(f"Error making request: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print("Response content:")
        print(response.text[:1000])  # Print first 1000 characters
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def test_legacy_xml_api():
    print("\nTesting legacy XML API support:")
    base_url = "https://clinicaltrials.gov/api/legacy/study-fields"
    params = {
        'expr': 'heart attack',
        'fields': 'NCTId,BriefTitle,Condition',
        'min_rnk': 1,
        'max_rnk': 5,
        'fmt': 'xml'
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        
        print(f"Status Code: {response.status_code}")
        print("\nStudies Found:")
        
        for study in root.findall('.//study'):
            nct_id = study.find('nct_id').text if study.find('nct_id') is not None else "N/A"
            title = study.find('brief_title').text if study.find('brief_title') is not None else "N/A"
            conditions = [cond.text for cond in study.findall('.//condition')]
            condition = ', '.join(conditions) if conditions else "N/A"
            
            print(f"\nNCT ID: {nct_id}")
            print(f"Title: {title}")
            print(f"Condition: {condition}")

    except requests.RequestException as e:
        print(f"Error making request: {e}")
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        print("Response content:")
        print(response.content.decode('utf-8')[:1000])  # Print first 1000 characters
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_new_json_api()
    test_legacy_xml_api()