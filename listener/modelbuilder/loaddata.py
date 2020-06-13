"""Build a language model from various sources

Ideas for sources:

https://figshare.com/articles/Raw_Python_Code_Corpus/11777217/1 1.88GB

WestBury Lab WikiPedia

TEDLIUM_release2

"""
import bz2


def open_wikipedia(filename='/var/datasets/text/WestburyLab.Wikipedia.Corpus.txt.bz2'):
    """Open the WestBury WikiPedia dump for processing"""
    try:
        file = bz2.open(filename, encoding='utf-8',)
    except (OSError, IOError) as err:
        raise OSError(
            "Expected the WestBury text corpus untarred into %s" % (filename,)
        )
    else:
        return file
