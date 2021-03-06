import subprocess
import os
import json

from glob import glob
from collections import defaultdict
from collections import Counter
from datetime import datetime


# folder rm and mkdir
def reset():
    """
    remove folder 'v2' if it exists and create this structure:
    v2
        input
            s1
            s2
            s3
        dev_data
            s1
            s2
            s3
    """

    commands = ['rm -rf v2',
                'mkdir -p v2/input/s1',
                'mkdir -p v2/input/s2',
                'mkdir -p v2/input/s3',
                'mkdir -p v2/dev_data/s1',
                'mkdir -p v2/dev_data/s2',
                'mkdir -p v2/dev_data/s3',
                'cp v1/readme.txt v2/README.txt'
                ]

    for command in commands:
        try:
            subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError as e:
            print(e)

# load conll + create q_id2docs
def load_conll(debug=False):
    """
    load all docs from all conll from all subtasks

    :rtype: tuple
    :return: (subtask2conll, q_id2docs)
    """
    subtask2conll = dict()
    q_id2docs = defaultdict(set)

    iterable = glob('v1/input/**/CONLL/*.conll')

    for num_conll, conll_path in enumerate(iterable, 1):

        if all([debug,
                num_conll % 100 == 0]):
            print(num_conll, datetime.now())
        with open(conll_path) as infile:

            basename = os.path.basename(conll_path)
            q_id = basename.replace('.conll', '')

            doc_id2conll = defaultdict(list)


            for line in infile:

                token_id = None

                if not line.startswith('#'):
                    token_id, token, discourse, anno = line.strip().split('\t')

                elif line.startswith('#begin document'):
                    doc_id = line[17:-3]
                    q_id2docs[q_id].add(doc_id)

                doc_id2conll[doc_id].append((token_id, line))

                if line.startswith('#end document'):
                    if doc_id not in subtask2conll:
                        subtask2conll[doc_id] = doc_id2conll[doc_id]

    if debug:
        print('num conll files', num_conll)
        print('num unique docs', len(subtask2conll))
        print('num qs', len(q_id2docs))

    return subtask2conll, q_id2docs




# create new questions.json + save
def update_questions_and_answers_json(subtask, q_id2docs, total_num_docs, add_input_docs_ids=False):
    """
    add key 'input_doc_ids' to json and save it in new folder

    :param str subtask: s1 | s2 | s3
    :param collections.defaultdict q_id2docs: mapping from q_id to input documents for participants
    (output from load_conll function)

    """
    question_json_path = 'v1/input/%s/questions.json' % subtask
    questions = json.load(open(question_json_path))

    answers_json_path = 'v1/dev_data/%s/answers.json' % subtask
    answers = json.load(open(answers_json_path))

    stats_input = {}

    # needed if you want to add the key 'input_doc_ids' to the questions json
    for q_id, q_info in answers.items():

        num_answer_docs = sum([len(docs)
                               for docs in q_info['answer_docs'].values()
                               ])

        confusion_docs = list(q_id2docs[q_id])
        num_confusion_docs = len(confusion_docs)

        num_noise_docs = total_num_docs - (num_confusion_docs + num_answer_docs)

        assert (num_answer_docs + num_confusion_docs + num_noise_docs) == total_num_docs, 'total: %s, answer: %s, confusion: %s, noise: %s' % (total_num_docs,
                                                                                                                                               num_answer_docs,
                                                                                                                                               num_confusion_docs,
                                                                                                                                               num_noise_docs)

        q_stats_info = {
            'answer' : q_info['numerical_answer'],
            'num_answer_docs' : num_answer_docs,
            'num_confunsion_docs' : num_confusion_docs,
            'num_noise_docs' : num_noise_docs
        }

        stats_input[q_id] = q_stats_info

        if add_input_docs_ids:
            questions[q_id]['input_doc_ids'] = list(q_id2docs[q_id])

    output_question_json_path = 'v2/input/%s/questions.json' % subtask

    with open(output_question_json_path, 'w') as outfile:
        json.dump(questions, outfile, indent=4, sort_keys=True)


    # mv answers.json
    command = 'cp v1/dev_data/%s/answers.json v2/dev_data/%s/answers.json' % (subtask, subtask)
    try:
        subprocess.check_output(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(e)

    return stats_input


def mwu_token_list(mwu_ids, debug=False):
    """
    given a list of token ids, return the same token ids
    but with missing token ids added,

    e.g. mwu_ids = ['1', '2,', '4'] -> ['1', '2', '3', '4']

    syntax of identifier is 'DOC_ID.SENT_ID.W_ID'
    :param list mwu_ids: e.g.
    ['abc4c58e9b7621b10a4732a98dc273b3.b3.15',
    'abc4c58e9b7621b10a4732a98dc273b3.b3.17',
    'abc4c58e9b7621b10a4732a98dc273b3.b3.18']

    :rtype: list
    :return: list of token ids
    """
    assert len(mwu_ids) >= 2, 'mwu_ids should be a length 2 at least: %s' % mwu_ids

    new_mwu_ids = []

    first_id = mwu_ids[0]
    doc_id, sent_id, first_token_id = first_id.split('.')

    last_id = mwu_ids[-1]
    doc_id, sent_id, last_token_id = last_id.split('.')

    for w_id in range(int(first_token_id),
                      int(last_token_id) + 1):

        new_id = '{doc_id}.{sent_id}.{w_id}'.format_map(locals())
        new_mwu_ids.append(new_id)

        if debug:
            if new_id not in mwu_ids:
                print()
                print('added', new_id)
                print('old mwu_ids', mwu_ids)

    return new_mwu_ids

# load annotations
def load_men_annotations(input_path, debug=False):
    """
    load mention annotations

    :param str input_path: path to mention annotations

    :rtype: dict
    :return: token_id -> annotation info
    """
    annotations = json.load(open(input_path))
    token_id2anno = dict()


    for inc_id, inc_info in annotations.items():
        if inc_id in {'739413', '773797', '761837', '759131'}: # trial data gold incidents

            if debug:
                print(inc_id, len(inc_info))

            for token_id, ann_info in inc_info.items():

                if 'mwu' not in ann_info:
                    anno_template = '(%s)'
                    token_id2anno[token_id] = (inc_id, ann_info, anno_template)
                else:
                    mwu_ids = mwu_token_list(ann_info['mwu'], debug=False)
                    mw_length = len(mwu_ids)

                    for index, token_id in enumerate(mwu_ids, 1):

                        if index == 1:
                            anno_template = '(%s'
                        elif index == mw_length:
                            anno_template = '%s)'
                        else:
                            anno_template = '%s'

                        token_id2anno[token_id] = (inc_id, ann_info, anno_template)

    return token_id2anno


# lumping function
def lump(inc_id, anno, debug=False):
    """
    convert an annotation, e.g.
    {'cardinality': 'UNK', 'eventtype': 'd', 'participants': ['2']}

    to an integer.

    the eventtypes 'b' and 's' are lumped to 'bs'


    :rtype: str
    :return: an integer as a string


    """
    for key in {'cardinality',
                'eventtype'}:
        assert key in anno, '%s not in anno: %s' % (key, anno)

    event_type = anno['eventtype']
    cardinality = anno['cardinality']
    if 'participants' not in anno:
        participants = 'UNK'
    else:
        participants = anno['participants']

    # prefix
    if event_type == 'g':
        return '0'
    elif event_type == 'o':
        prefix = '1'
    elif event_type in {'b', 'd', 'h', 'i', 'm', 's'}:
        prefix = '2'
    else:
        assert False, 'event_type %s not in accepted eventtypes' % event_type

    # event types
    event_type_ord = str(ord(event_type))
    if event_type in {'b', 's'}:

        if debug:
            print()
            print('before lumping', event_type, cardinality, participants)

        if event_type == 'b':
            assert participants == 'ALL', '{participants} should be ALL with b'.format_map(locals())

            cardinality = 'UNK'
            participants = 'UNK'
            event_type = 'bs'
            event_type_ord = str(ord('b')) + str(ord('s'))

        elif all([event_type == 's',
                  type(participants) != list]):

            cardinality = 'UNK'
            participants = 'UNK'

            event_type = 'bs'
            event_type_ord = str(ord('b')) + str(ord('s'))

        if debug:
            print('after lumping', event_type, cardinality, participants)

    # participants
    part_string = ''.join(participants)
    if type(participants) != list:
        part_string = ''.join([str(ord(char))
                               for char in cardinality])

    # cardinality
    card_ord = ''.join([str(ord(char))
                        for char in cardinality])

    # to integer
    the_integer = '999'.join([prefix,
                              inc_id,
                              card_ord,
                              event_type_ord,
                              part_string
                              ])

    if debug:
        print('prefix', prefix)
        print('cardinality', cardinality, card_ord)
        print('event_type', event_type, event_type_ord)
        print('participants', participants, part_string)
        print('integer', the_integer)

    return the_integer


# output conll with and without annotations (same time two files)
def to_conll(subtask, subtask2conll, token_id2anno):
    """
    write two conll files
    a) v2/dev_data/SUBTASK/docs.conll -> with annotations
    b) v2/input/SUBTASK/docs.conll -> without annotations

    :param dict doc_id2conll: output of load_conll function
    :param dict token_id2anno: output of load_men_annotations function

    """
    added = set()
    chains = defaultdict(int)

    anno_output_path = 'v2/dev_data/%s/docs.conll' % subtask
    no_anno_output_path = 'v2/input/%s/docs.conll' % subtask

    outfile_anno = open(anno_output_path, 'w')
    outfile_no_anno = open(no_anno_output_path, 'w')

    for doc_id, conll_info in subtask2conll.items():

        for token_id, line in conll_info:

            if token_id in token_id2anno:
                inc_id, ann_info, anno_template = token_id2anno[token_id]
                integer = lump(inc_id, ann_info)

                splitted = line.strip().split('\t')
                splitted[3] = anno_template % integer

                outfile_anno.write('\t'.join(splitted) + '\n')

                added.add(token_id)

                chains[anno_template % integer] += 1

            else:
                outfile_anno.write(line)

            outfile_no_anno.write(line)


    outfile_anno.close()
    outfile_no_anno.close()

    print('num chains', len(chains))
    print('distr', Counter(chains.values()))

    return added

def compute_stats(stats_input, output_path=None, debug=False):
    """
    compute stats:
    a) avg num of gold incidents
    b) avg num of gold docs
    c) 1 to n confusion documents
    d) 1 to n noise documents

    :param dict stats_input: mapping of q_id ->
    {
            'answer' : q_info['numerical_answer']
            'num_answer_docs' : num_answer_docs,
            'num_confunsion_docs' : num_confusion_docs,
            'num_noise_docs' : num_noise_docs
        }

    :rtype: dict
    :return:
    """
    stats = dict()

    for metric_name, input_key in [('gold_incidents', 'answer'),
                                   ('gold_docs', 'num_answer_docs'),
                                   ('confusion_docs', 'num_confunsion_docs'),
                                   ('noise_docs', 'num_noise_docs')
                                   ]:

        the_sum = sum([q_info[input_key]
                       for q_info in stats_input.values()])
        the_avg = the_sum / len(stats_input)

        stats[metric_name] = (the_sum, round(the_avg, 2))


    num_confusion_docs_per_gold_document = stats['confusion_docs'][0] / stats['gold_docs'][0]
    num_noise_docs_per_gold_document = stats['noise_docs'][0] / stats['gold_docs'][0]

    stats['num_confusion_docs_per_gold_document'] = round(num_confusion_docs_per_gold_document, 2)
    stats['num_noise_docs_per_gold_document'] = round(num_noise_docs_per_gold_document, 2)

    if debug:
        print(stats)

    if output_path:
        with open(output_path, 'w') as outfile:
            json.dump(stats, outfile, indent=4, sort_keys=True)


# TODO: add stats txt with
    # avg num of gold incidents
    # avg num of gold docs
    # 1 to n confusion documents
    # 1 to n noise documents

if __name__ == '__main__':

    # call functions
    debug_value = True

    # reset directories
    reset()

    # main loop
    all_added = set()

    anno_path = 'resources/ann_piek_men.json'
    token_id2anno = load_men_annotations(anno_path, debug=debug_value)

    subtask2conll, q_id2docs = load_conll(debug=debug_value)
    total_num_docs = len(subtask2conll)

    for subtask in ['s1',
                    's2',
                    's3'
                    ]:

        if debug_value:
            print()
            print('subtask', subtask)

        stats_input = update_questions_and_answers_json(subtask,
                                                        q_id2docs,
                                                        total_num_docs,
                                                        add_input_docs_ids=False)

        #stats_output_path = 'v2/dev_data/%s/stats.json' % subtask

        compute_stats(stats_input, output_path=None, debug=True)

        added = to_conll(subtask, subtask2conll, token_id2anno)

        all_added.update(added)


    missing = set(token_id2anno) - all_added
    print('added', len(all_added))
    print('missing', len(missing))
    print(missing)