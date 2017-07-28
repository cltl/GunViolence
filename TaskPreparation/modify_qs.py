import json

inputs=['package/input/s%d/old_questions.json' % num for num in range(1,4)]
outputs=['package/input/s%d/questions.json' % num for num in range(1,4)]

for infile, outfile in zip(inputs,outputs):
    with open(infile, 'r') as qj:
        q_json=json.load(qj)
        new_json={}
        for q_id in q_json.keys():
            new_json[q_id]=q_json[q_id]
            for prop in ['time', 'location', 'participant']:
                if prop in new_json[q_id]:
                    new_json[q_id][prop]={new_json[q_id][prop][1]: new_json[q_id][prop][0]}
        with open(outfile, 'w') as w:
            w.write(json.dumps(new_json, indent=4, sort_keys=True))
