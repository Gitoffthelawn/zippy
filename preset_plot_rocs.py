#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
import re
from junitparser import JUnitXml

MODEL = 'zippy-zlib'
PRESETS = range(0, 10)
SKIPCASES = ['gpt2', 'gpt3']

MAX_PER_CASE = 500

plt.figure()

for preset in PRESETS:
    xml = JUnitXml.fromfile(f'{MODEL}-{preset}.xml')
    cases = []
    for suite in xml:
        for case in suite:
            cases.append(case)
    
    truths = []
    scores = []
    per_case = {}
    fails_per_case = {}
    for c in cases:
        if c.name is None:
            print("ERROR")
            continue
        cname = re.sub('\[.*$', '', c.name)
        if any(sub in cname for sub in SKIPCASES):
            continue
        if cname in per_case.keys():
            per_case[cname] += 1
        else:
            per_case[cname] = 1
            fails_per_case[cname] = 0
        if per_case[cname] > MAX_PER_CASE:
            continue
        try:
            score = float(c._elem.getchildren()[0].getchildren()[0].values()[1])
        except:
            continue
        if 'human' in c.name:
            truths.append(1)
            if c.is_passed:
                scores.append(score)
            else:
                fails_per_case[cname] += 1
                scores.append(score * -1.0)
        else: # AI
            truths.append(-1.0)
            if c.is_passed:
                scores.append(score * -1.0)
            else:
                fails_per_case[cname] += 1
                scores.append(score)

    y_true = np.array(truths)
    y_scores = np.array(scores) 
    print("Failures per case for " + MODEL + ' ' + str(preset))
    #print(fails_per_case)
    tf = 0
    for k in fails_per_case.keys():
        tf += fails_per_case[k]
    print('Total fails: ' + str(tf))
    tp = len(cases) - tf
    # Compute the false positive rate (FPR), true positive rate (TPR), and threshold values
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    gmeans = np.sqrt(tpr * (1-fpr))
    ix = np.argmax(gmeans)
    print('Best Threshold=%f, G-Mean=%.3f' % (thresholds[ix], gmeans[ix]))
    #print(thresholds)
    # calculate the g-mean for each threshold
    # locate the index of the largest g-mean
    # Calculate the area under the ROC curve (AUC)
    roc_auc = auc(fpr, tpr)

    # Plot the ROC curve
    plt.plot(fpr, tpr, lw=2, label=f'{MODEL.split("-")[1].capitalize()}-{preset}: ROC curve (%Acc = {tp/len(cases):0.2f}; AUC = {roc_auc:0.2f})')
    plt.scatter(fpr[ix], tpr[ix], marker='o', color='black')#, label=model.capitalize() + ': Best @ threshold = %0.2f' % thresholds[ix])

plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label="Random classifier")
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic for LLM detection')
plt.legend(loc="lower right")
plt.savefig('preset_ai_detect_roc.png')