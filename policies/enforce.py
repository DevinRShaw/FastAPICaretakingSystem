import pprint
from datetime import datetime

async def masectomy_first_week(patient_case, patient_records) -> list[str]:

    #date comparison checks
    operation_date = datetime.strptime(patient_case['operation_date'], "%d-%m-%Y")

    if (datetime.now() - operation_date).days > 7:
        return None 

    policy_flags = []

    #patient records sorted by most recent 
    cursor = patient_records.find({'patient_id' : patient_case['patient_id']}).sort({'_id' : -1})


    #one off checks during aggregation 
    async for doc in cursor: 

        doc_date = datetime.strptime(doc['date'], "%d-%m-%Y")

        #date range check 
        if (doc_date - operation_date ).days > 7: 
            continue

        if int(doc['pain_level']) >= 5:
            policy_flags.append({'week_1_excess_pain' : doc['pain_level']})

    return policy_flags


operation_policy_map = {
    "masectomy" : [masectomy_first_week]
} 


async def enforce_policies(patient_case : dict[str], patient_records) -> list[str]:

    flags = []
    for policy in operation_policy_map[patient_case['operation']]:

        results = await policy(patient_case, patient_records)

        if not results: 
            continue

        for result in results: 
                flags.append(result)

    return flags 
            


