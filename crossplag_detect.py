#!/usr/bin/env python3

import requests, re, os, time
from typing import Optional, Dict, Tuple

API_URL = 'https://j1o8u6du62.execute-api.eu-central-1.amazonaws.com/production/detect'

def make_req(text : str) -> Optional[Dict]:
    headers = {
        'Origin': 'https://app.crossplag.com'
    }
    data = {
        'text': text,
    }
    res = requests.post(API_URL, headers=headers, json=data)
    if res.status_code != 200:
        print(res.text)
        return None
    return res.json().get('dataToreturn', {}).get('aiIndex', None)

def classify_text(s : str) -> Optional[Tuple[str, float]]:
    res = make_req(s)
    if res is None:
        print("Unable to classify!")
        return None
    else:
        #print(res)
        try:
            res = float(res)
        except TypeError as e:
            print("Unable to convert " + str(res) + " to float!")
        if res > 0.5:
            return ('AI', res)
        else:
            return ('Human', 1 - res)

def run_on_file_chunked(filename : str, chunk_size : int = 3000) -> Optional[Tuple[str, float]]:
	'''
	Given a filename (and an optional chunk size) returns the score for the contents of that file.
	This function chunks the file into at most chunk_size parts to score separately, then returns an average. This prevents a very large input
	overwhelming the model.
	'''
	with open(filename, 'r') as fp:
		contents = fp.read()
	return run_on_text_chunked(contents, chunk_size)

def run_on_text_chunked(contents : str, chunk_size : int = 3000) -> Optional[Tuple[str, float]]:
	'''
	Given a text (and an optional chunk size) returns the score for the contents of that string.
	This function chunks the string into at most chunk_size parts to score separately, then returns an average. This prevents a very large input
	overwhelming the model.
	'''

	# Remove extra spaces and duplicate newlines.
	contents = re.sub(' +', ' ', contents)
	contents = re.sub('\t', '', contents)
	contents = re.sub('\n+', '\n', contents)
	contents = re.sub('\n ', '\n', contents)

	res = classify_text(contents)
	if res is None:
		time.sleep(5)
		res = classify_text(contents)
	return res
	start = 0
	end = 0
	chunks = []
	while start + chunk_size < len(contents) and end != -1:
		end = contents.rfind(' ', start, start + chunk_size + 1)
		chunks.append(contents[start:end])
		start = end + 1
	chunks.append(contents[start:])
	scores = []
	for c in chunks:
		scores.append(classify_text(c))
	ssum : float = 0.0
	for s in scores:
		if s[0] == 'AI':
			ssum -= s[1]
		else:
			ssum += s[1]
	sa : float = ssum / len(scores)
	if sa < 0:
		return ('AI', abs(sa))
	else:
		return ('Human', abs(sa))