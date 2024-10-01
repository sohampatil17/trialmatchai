from openai import OpenAI
client = OpenAI()

def get_keywords(patient_info):
    prompt = f"Patient description: {patient_info}\n\n Based on this patient's description, give me keyword(s) that I should be using to search for clinical trials on clinicaltrials.gov that the patient could potentially be matched to. Give me the output in the format of - keyword1 AND keyword2 (strictly return only the output without any extra information. return between 1 to 2 keywords)"

    response = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=[
            {"role": "system", "content": "You are an AI assistant"},
            {"role": "user", "content": prompt}
        ]
    )
    
    keywords = response.choices[0].message.content
    return keywords

if __name__ == "__main__":
    patient_info = """
    The patient is a 68-year-old male with a history of Alzheimer's.
    He has been experiencing memory loss, confusion, and difficulty completing familiar tasks.
    The patient is currently on Donepezil and Memantine.
    """

    keywords = get_keywords(patient_info)
    print(keywords)