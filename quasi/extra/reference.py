"""
Reference Management Module
"""
import re


def is_valid_doi(doi: str) -> bool:
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
    if not all(isinstance(bib_dict[key], str) for key in ["author", "title"]):
        return False
    pattern = "^\\d{1,4}$"  # regular expression pattern to match numbers up to four digits
    if not re.match(pattern, str(bib_dict["year"])):
        return False
    return True


class Reference:  # pylint: disable=too-few-public-methods
    """
    Reference class, for recording references
    """

    def __init__(self, doi=None, bib_dict=None):
        """
        Initialization Method
        """
        if doi and is_valid_doi(doi):
            self.doi = doi
        if bib_dict and is_valid_bib(bib_dict):
            self.bib_dict = bib_dict
        if self.doi is None and self.bib_dict is None:
            raise InvalidBibEntryException(
                "Either 'bib_dict' or 'doi' should be specified in correct manner!"
            )

    def get_bibliography(self) -> str:
        """
        Returns bib entry: TODO Implementation
        Should prefer to fetch the bibliography from doi entries
        if doi and bib_dict given
        """
        return ""

    def _get_bib_from_doi(self) -> bool:
        """
        Should get the bib from the web
        """
        return False


class InvalidBibEntryException(Exception):
    """
    Exception, raised when invalid bib entries are given to
    the Reference object
    """
