import subprocess
import argparse

parser = argparse.ArgumentParser(description="Automated annotation of object assets.")

parser.add_argument('--unlabeled_objects', type=str, help='JSON file containing objects to be annotated')
parser.add_argument('--object_annotations', type=str, help='Output file of object annotation in xlsx format')
parser.add_argument('--receptacles', type=str, help='Output file about whether an object is a receptacle or not in xlsx format')
parser.add_argument('--relations', type=str, help='Output file about co-occurrence relationships in json format')

args=parser.parse_args()
scripts_and_args = [
    ('ann_main.py', args.unlabeled_objects, args.object_annotations),
    ('ann_rec.py', args.unlabeled_objects, args.receptacles),
    ('ann_relation.py', args.receptacles, args.relations),
]

for script, arg1, arg2 in scripts_and_args:
    subprocess.check_call(['python', script, arg1, arg2])