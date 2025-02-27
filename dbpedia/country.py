# coding: utf-8

"""
Country related regex
"""

from refo import Plus, Question
from quepy.dsl import HasKeyword
from quepy.parsing import Lemma, Pos, QuestionTemplate, Token, Particle
from dsl import IsCountry, IncumbentOf, CapitalOf, \
    LabelOf, LanguageOf, PopulationOf, PresidentOf, IsCapital


class Country(Particle):
    regex = Plus(Pos("DT") | Pos("NN") | Pos("NNS") | Pos("NNP") | Pos("NNPS"))

    def interpret(self, match):
        name = match.words.tokens.title()
        return IsCountry() + HasKeyword(name)


class Capital(Particle):
    regex = Plus(Pos("DT") | Pos("NN") | Pos("NNS") | Pos("NNP") | Pos("NNPS"))

    def interpret(self, match):
        name = match.words.tokens.title()
        return IsCapital() + HasKeyword(name)


# NOT WORKING for any country
class PresidentOfQuestion(QuestionTemplate):
    """
    Regex for questions about the president of a country.
    Ex: "Who is the president of Argentina?"
    """

    regex = Pos("WP") + Token("is") + Question(Pos("DT")) + \
        Lemma("president") + Pos("IN") + Country() + Question(Pos("."))

    def interpret(self, match):
        president = PresidentOf(match.country)
        incumbent = IncumbentOf(president)
        label = LabelOf(incumbent)

        return label, "enum"


class IsCapitalOfQuestion(QuestionTemplate):

    regex = Token("is") + Capital() + Pos("DT") + Lemma("capital") + Pos("IN") + \
            Question(Pos("DT")) + Country() + Question(Pos("."))

    def interpret(self, match):
        capital = CapitalOf(match.country)
        label = LabelOf(capital)
        return label, "enum"


class CapitalOfQuestion(QuestionTemplate):
    """
    Regex for questions about the capital of a country.
    Ex: "What is the capital of Bolivia?"
    """

    opening = Lemma("what") + Token("is")
    regex = opening + Pos("DT") + Lemma("capital") + Pos("IN") + \
        Question(Pos("DT")) + Country() + Question(Pos("."))

    def interpret(self, match):
        capital = CapitalOf(match.country)
        label = LabelOf(capital)
        return label, "enum"


# FIXME: NOT WORKING - the generated query needs FILTER isLiteral() to the head
# because dbpedia sometimes returns different things
# working only for some countries
class LanguageOfQuestion(QuestionTemplate):
    """
    Regex for questions about the language spoken in a country.
    Ex: "What is the language of Argentina?"
        "what language is spoken in Argentina?"
    """

    openings = (Lemma("what") + Token("is") + Pos("DT") +
                Question(Lemma("official")) + Lemma("language")) | \
               (Lemma("what") + Lemma("language") + Token("is") +
                Lemma("speak"))

    regex = openings + Pos("IN") + Question(Pos("DT")) + Country() + \
        Question(Pos("."))

    def interpret(self, match):
        language = LanguageOf(match.country)
        return language, "enum"


class PopulationOfQuestion(QuestionTemplate):
    """
    Regex for questions about the population of a country.
    Ex: "What is the population of China?"
        "How many people live in China?"
    """

    openings = (Pos("WP") + Token("is") + Pos("DT") +
                Lemma("population") + Pos("IN")) | \
               (Pos("WRB") + Lemma("many") + Lemma("people") +
                Token("live") + Pos("IN"))
    regex = openings + Question(Pos("DT")) + Country() + Question(Pos("."))

    def interpret(self, match):
        population = PopulationOf(match.country)
        return population, "literal"
