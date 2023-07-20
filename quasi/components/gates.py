from __future__ import unicode_literals, print_function, absolute_import
from builtins import str
import requests

from abc import ABC
from quasi._math.fock import displacement, beamsplitter, phase, squeezing


class Components(ABC):
    """
     singlton

    we should agree on specific methods and properties that relates to
    signals.
    """

    def __init__(
        self,
        cutoff: int = None,
        physical_description: dict = None,
        math_eqation: str = None,
        doi: str = None,
        author_name: str = None,
    ) -> None:
        self.cutoff = cutoff
        self.physical_description = physical_description
        self.math_equation = math_eqation
        self.doi = doi
        self.author_name = author_name
        self.matrix = None
        self.author_name = None

    def physical_properties(self):
        self.frequency = self.physical_description["frequency"]
        self.gaussian = self.physical_description["gaussianity"]
        self.passive = self.physical_description["passive"]
        self.name = self.physical_description["name"]
        """
        many parameters to set here

        """

    def get_operator(self, math_equation):
        raise NotImplementedError

    def generate_bibtex(self, doi):
        bare_url = "http://api.crossref.org/"
        url = "{}works/{}/transform/application/x-bibtex"
        url = url.format(bare_url, doi)

        r = requests.get(url)
        found = False if r.status_code != 200 else True
        bib = r.content

        bib = str(bib, "utf-8")
        if self.author_name is not None:
            print("name allocation is not implpemente yet in this case")
            raise NotImplementedError  # we should think of how to include author
            # name inside the bibtex
        return found, bib


class Beamsplitter(Components):
    def __init__(
        self,
        theta,
        phi,
        cutoff,
        physical_description: dict = None,
        math_eqation: str = None,
        doi: str = None,
        author_name: str = None,
    ) -> None:
        self.theta = theta
        self.doi = doi
        self.phi = phi
        self.cutoff = cutoff
        self.math_equation = math_eqation
        self.matrix = self.get_operator(self.math_equation)
        self.author_name = author_name

    def get_operator(self, math_equation):
        if math_equation is None:
            self.matrix = beamsplitter(self.theta, self.phi, self.cutoff)
        else:
            raise NotImplementedError

    def generate_bibtex(self):
        return super().generate_bibtex(self.doi)


class Displacment(Components):
    def __init__(
        self,
        r,
        phi,
        cutoff,
        physical_description: dict = None,
        math_eqation: str = None,
        doi: str = None,
        author_name: str = None,
    ) -> None:
        self.r = r
        self.doi = doi
        self.author_name = author_name
        self.phi = phi
        self.cutoff = cutoff
        self.math_equation = math_eqation
        self.matrix = self.get_operator()
        self.author_name = author_name

    def get_operator(self):
        if self.math_equation is None:
            return displacement(self.r, self.phi, self.cutoff)
        else:
            raise NotImplementedError

    def generate_bibtex(self):
        return super().generate_bibtex(self.doi)


class Squeezing(Components):
    def __init__(
        self,
        r,
        phi,
        cutoff,
        physical_description: dict = None,
        math_eqation: str = None,
        doi: str = None,
        author_name: str = None,
    ) -> None:
        self.r = r
        self.phi = phi
        self.doi = doi
        self.author_name = author_name
        self.cutoff = cutoff
        self.math_equation = math_eqation
        self.matrix = self.get_operator()
        self.physical_description = physical_description

    def get_operator(self):
        if self.math_equation is None:
            return squeezing(self.r, self.phi, self.cutoff)
        else:
            raise NotImplementedError

    def generate_bibtex(self):
        return super().generate_bibtex(self.doi)


class Phase(Components):
    def __init__(
        self,
        phi,
        cutoff,
        physical_description: dict = None,
        math_eqation: str = None,
        doi: str = None,
        author_name: str = None,
    ) -> None:
        self.phi = phi
        self.doi = doi
        self.author_name = author_name
        self.cutoff = cutoff
        self.math_equation = math_eqation
        self.matrix = self.get_operator(self.math_equation)

    def get_operator(self):
        if self.math_equation is None:
            self.matrix = phase(self.theta, self.phi, self.cutoff)
        else:
            raise NotImplementedError

    def generate_bibtex(self):
        return super().generate_bibtex(self.doi)
