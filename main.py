import os
from openai import OpenAI
import requests
import json
from flask import Flask, request, render_template, flash
import markdown

app = Flask(__name__)
app.secret_key = os.urandom(24)

client = OpenAI()
client.api_key = os.environ.get("OPENAI_API_KEY")

DISEASES_OF_INTEREST = [
    "Sickle Cell Disease", "Type 2 Diabetes", "Hypertension", "Breast Cancer",
    "Prostate Cancer", "Colorectal Cancer", "Asthma", "Obesity", "HIV/AIDS"
]

def get_clinical_trials(search_terms):
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        'query.term': search_terms,
        'fields': 'NCTId,BriefTitle,Phase,EligibilityCriteria,Condition,LocationFacility,LocationCity,LocationState,StartDate,CompletionDate,LeadSponsorName',
        'pageSize': 30
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        studies = []
        for study in data.get('studies', []):
            protocol = study.get('protocolSection', {})
            identification = protocol.get('identificationModule', {})
            design = protocol.get('designModule', {})
            eligibility = protocol.get('eligibilityModule', {})
            status = protocol.get('statusModule', {})
            sponsor = protocol.get('sponsorCollaboratorsModule', {})
            
            studies.append({
                'NCTId': identification.get('nctId', 'N/A'),
                'BriefTitle': identification.get('briefTitle', 'N/A'),
                'Phase': design.get('phases', ['N/A']),
                'EligibilityCriteria': eligibility.get('eligibilityCriteria', 'No eligibility criteria provided'),
                'Condition': protocol.get('conditionsModule', {}).get('conditions', ['No condition specified']),
                'StartDate': status.get('startDateStruct', {}).get('date', 'N/A'),
                'CompletionDate': status.get('completionDateStruct', {}).get('date', 'N/A'),
                'LeadSponsor': sponsor.get('leadSponsor', {}).get('name', 'N/A')
            })
        
        return studies
    except requests.RequestException as e:
        raise Exception(f"Error fetching data from ClinicalTrials.gov API: {e}")

def evaluate_trial(patient_info, trial):
    prompt = f"""
    Patient: Age {patient_info['age']}, {patient_info['gender']}, {patient_info['race_ethnicity']}, {patient_info['location']}, Disease: {patient_info['disease']}
    Additional Info: {patient_info['additional_info']}

    Trial: {trial['BriefTitle']}
    Condition: {', '.join(trial['Condition'])}
    Eligibility: {trial['EligibilityCriteria']}

    Evaluate if the patient is eligible for this trial. Provide a brief explanation (3-4 lines) focusing on key inclusion/exclusion criteria and any relevant health disparity considerations. Return the result as 'Eligible' or 'Ineligible', and the brief explanation.
    """

    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {"role": "system", "content": "You are an AI assistant helping match patients from underserved communities with clinical trials"},
            {"role": "user", "content": prompt}
        ]
    )
    
    evaluation = response.choices[0].message.content
    
    result = "Ineligible"
    if "Eligible" in evaluation:
        result = "Eligible"
    
    explanation = evaluation.split("\n", 1)[-1].strip()
    
    return {"result": result, "explanation": explanation}

@app.route('/find_trials', methods=['GET', 'POST'])
def find_trials():
    if request.method == 'POST':
        patient_info = {
            'age': request.form['age'],
            'gender': request.form['gender'],
            'location': request.form['location'],
            'disease': request.form['disease'],
            'race_ethnicity': request.form['race_ethnicity'],
            'additional_info': request.form.get('additional_info', '')
        }
        
        search_terms = f"{patient_info['disease']} AND AREA[LocationCountry] United States"
        
        try:
            studies = get_clinical_trials(search_terms)
            eligible_trials = []
            ineligible_trials = []
            
            for trial in studies:
                evaluation = evaluate_trial(patient_info, trial)
                trial_info = {
                    "NCTId": trial['NCTId'],
                    "BriefTitle": trial['BriefTitle'],
                    "Phase": ', '.join(trial['Phase']),
                    "Result": evaluation["result"],
                    "Explanation": evaluation["explanation"],
                    "StartDate": trial['StartDate'],
                    "CompletionDate": trial['CompletionDate'],
                    "LeadSponsor": trial['LeadSponsor']
                }
                
                if evaluation["result"] == "Eligible":
                    eligible_trials.append(trial_info)
                else:
                    ineligible_trials.append(trial_info)
                
                if len(eligible_trials) == 5:
                    break
            
            return render_template('find_trials.html', 
                                   eligible_trials=eligible_trials, 
                                   ineligible_trials=ineligible_trials, 
                                   diseases=DISEASES_OF_INTEREST)
        except Exception as e:
            flash(str(e), 'error')
            print(f"Error: {e}")
            return render_template('find_trials.html', diseases=DISEASES_OF_INTEREST)
    
    return render_template('find_trials.html', diseases=DISEASES_OF_INTEREST)

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)