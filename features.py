#!/usr/bin/python3
# word feature extractor from text using ID3 
# by Merlin Carson

import os
import re
import sys
import time
import pickle
import argparse
import numpy as np
from glob import glob
from tqdm import tqdm
from info_gain import prune_dataset

def parse_args():
    parser = argparse.ArgumentParser(description='Feature creator for author classification')
    parser.add_argument('--text_dir', type=str, default='txts', help='Directory with texts to process for dataset')
    parser.add_argument('--full_ds', type=str, default='full_dataset.npy', help='File to save full feature set to')
    parser.add_argument('--pruned_ds', type=str, default='dataset.npy', help='File to save pruned dataset to')
    parser.add_argument('--load_full_ds', default=False, action='store_true', help='Loads full feature from file instead of generating them')
    parser.add_argument('--save_full_ds', default=False, action='store_true', help='Saves full feature set from file instead of generating them')
    parser.add_argument('--n_feats', type=int, default=300, help='Number features to keep')

    return parser.parse_args()

# returns a list of unique words for a text string
def find_unique_words(text):
    # regex for alpha chars only
    regex = re.compile('[^a-zA-Z]')
    clean_words = []
    words = text.split()
    for word in words:
        word = regex.sub('', word)
        # skip anything with 1 or less alpha chars
        if len(word) < 2:
            continue
        clean_words.append(word.lower())

    return list(set(clean_words))

# creates a dictionary of unique words for directory of text files
def create_dictionary(text_dir):

    dict_words = []
    #print('Creating dictionary of words')
    for txt in tqdm(glob(os.path.join(text_dir, '*.txt'), recursive=True)):
        with open(txt, 'r') as f:
            words = find_unique_words(f.read())
            dict_words.extend(words)

    dict_words = set(dict_words)

    dict_words = {key: value for value, key in enumerate(sorted(dict_words), start=1)}

    return dict_words

# seperates paragraphs from a text file
def read_paragraphs(txt):
    with open(txt, 'r') as f:
        text = f.read()
        lines = text.splitlines()
        paragraphs = [] 
        paragraph = ''
        # create paragraphs from lines where '' is the delimiter between them
        for line in lines:
            if line == '':
                paragraphs.append(paragraph)
                paragraph = ''
                continue
            paragraph = f'{paragraph} {line}' 

    # handle if there no newline at end of lines
    if len(paragraph) > 0:
        paragraphs.append(paragraph)

    return paragraphs

# for each word in the dictionary determines if it exists in a paragraph
# along with assigning a unique ID to paragraph and class label
def paragraphs_to_features(dict_words, txt, paragraphs, classes):
    paragraph_features = []
    for i, paragraph in enumerate(paragraphs, start=1):
        features = np.zeros((len(dict_words)+1)).astype('uint8')
        words = find_unique_words(paragraph)

        # set class
        for key, value in classes.items():
            if key.lower() in txt.lower():
                features[0] = value

        # set features (words from dictionary in paragraph)
        for key, value in dict_words.items():
            if key in words:
                features[value] = 1

        para_id = f'{os.path.basename(txt).replace(".txt", "")}.{i}'
        paragraph_features.append((para_id, features)) 

    return paragraph_features

# creates the dataset of paragraph features given a dictionary of words/author classes
# from a directory of texts 
def create_dataset(dict_words, text_dir, classes):
    
    paragraph_features = []

    #print('Creating full dataset')
    for txt in tqdm(glob(os.path.join(text_dir, '*.txt'), recursive=True)):
        txt_paragraphs = read_paragraphs(txt)
        features = paragraphs_to_features(dict_words, txt, txt_paragraphs, classes)
        paragraph_features.extend(features)

    return paragraph_features

# converts dataset into CSV format
def data_to_csv(dataset, features):
    csv = '' 
    for i, data in enumerate(dataset):
        csv += f'{data[0]}'
        for feat in features[i]:
            csv += f', {str(feat)}'
        csv += '\n'

    return csv

def main(args):
    start = time.time()

    # load all words from all texts in text dir
    dict_words = create_dictionary(args.text_dir)

    # define classes
    classes = {'austin': 0, 'shelley': 1}

    # Generate Dataset
    if not args.load_full_ds:
        # create dataset of all features from all paragraphs
        full_dataset = create_dataset(dict_words, args.text_dir, classes)

        # save full dataset to file
        if args.save_full_ds:
            pickle.dump(full_dataset, open(args.full_ds, 'wb'))
    # Load dataset from file
    else:
        # load full dataset from file
        full_dataset = pickle.load(open(args.full_ds,'rb'))

    # find top features
    pruned_features = prune_dataset(full_dataset, args.n_feats, dict_words)

    # print pruned dataset
    csv = data_to_csv(full_dataset, pruned_features)
    print(csv)

    #print(f'Script completed in {time.time()-start:.2f} secs')

    return 0

if __name__ == '__main__':
    args = parse_args()
    sys.exit(main(args))
