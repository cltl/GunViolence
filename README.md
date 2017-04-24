# LongTailQATask

This repository contains the code for the pilot of the task **Counting Events and Participants within Highly Ambiguous Data covering a very long tail** proposed to SemEval 2018. The pilot is described in *Section 7* of our proposal.

Following the conceptual division in the proposal text, the task implementation is divided into two parts: 

1) The folder **EventRegistries** contains the data preparation scripts and data (described in *Section 4.1* of the proposal)
2) The folder **QuestionCreation** creates questions based on the data in 1) and generates question stats (as described in *Section 5.3*)

### 1) EventRegistries

#### 1.1) GunViolenceArchive (GVA)



#### 1.2) FireRescue1

The data is crawled with the Python Notebook file `Crawler.ipynb`, it is stored in `firerescue.pickle`, and we analyze it in `Inspect.ipynb`. As we describe in *Section 7* of the proposal, in our pilot we only use the GVA data to create questions.

### 2) QuestionCreation