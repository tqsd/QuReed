#!/usr/bin/env python3
import re

def is_valid_doi(doi:str)->bool:
    """
    Function returns true, if doi is valid
    """
    pattern = r"^10.\d{4,9}/[-._;()/:A-Z0-9]+$"
    return bool(re.match(pattern, doi))

def is_valid_bib(bib_dict):
    """
    Function returns true, if bib dict is valid
    Vaild if has authors, title and year
    """
    required_keys = ["author", "title", "year"]
    if not all(key in bib_dict for key in required_keys):
        return False
    if not all(isinstance(bib_dict[key], str) for key in ["author","title"]):
        return False
    pattern = "^\\d{1,4}$" # regular expression pattern to match numbers up to four digits
    if not re.match(str(bib_dict["year"])):
        return False
    return True


class Reference:
    """
    Reference class, for recording references
    """

    def __init__(self, doi:str|None=None, bib_dict=None):
        """
        Initialization Method
        """
        if doi and is_valid_doi(doi):
            self.DOI=doi
        if bib_dict and is_valid_bib(bib_dict):
            self.bib_dict = bib_dict
        if self.DOI==None and self.bib_dict == None:
            raise Exception("Either 'bib_dict' or 'doi' should be specified in correct manner!")


    def get_bibliography(self)->str:
        """
        Returns bib entry: TODO Implementation
        Should prefer to fetch the bibliography from doi entries
        if doi and bib_dict given
        """
        return ""
