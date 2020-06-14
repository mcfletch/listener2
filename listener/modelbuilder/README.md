# Language Models for Dictation

##  Generic language model

The only significant  difference between the language models that we will generate
and the core deep speech language models  is that we will include the necessary commands
to do capitalization and other formatting.

##  Programming language model 

The programming language model is based off a free corpus of
Python programming projects' source code  and is, again,
pre processed in order to include the necessary formatting and 
capitalization  to dictate the text as observed.

## Process for generation

We follow the [DeepSpeech LM Model Process](https://deepspeech.readthedocs.io/en/v0.7.3/Scorer.html) to produce our scorers.

Things we use for setting up language models:

* [LibreSpeeh](http://www.openslr.org/resources/11/librispeech-lm-norm.txt.gz)
* [Raw Python Code Corpus](https://figshare.com/articles/Raw_Python_Code_Corpus/11777217/1)
* [WestburyLab.Wikipedia.Corpus](https://www.psych.ualberta.ca/~westburylab/downloads/westburylab.wikicorp.download.html)

* [google-10000-english.txt](https://github.com/first20hours/google-10000-english/blob/master/google-10000-english.txt)
* System dictionary `/usr/share/dict/words`
