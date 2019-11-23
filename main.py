# coding=utf-8
import datetime
import random
import sys
import time
import traceback
import quepy
import json

from SPARQLWrapper import SPARQLWrapper, JSON

# use dbpedia
sparql = SPARQLWrapper("http://dbpedia.org/sparql")

dbpedia = quepy.install("dbpedia")


# get question from user input
def getQuestion():
    s = str(raw_input("enter a question: \n"))
    return s


# transform question to sparql query
def get_SparqlQuery(question):
    target, query, metadata = dbpedia.get_query(question)
    # query = query[:-2]
    # query += "FILTER (langMatches(lang(?x2),\"en\"))\n}"
    return query


# get answers as list from sparql query
def get_answer_list(sparql_query, sparql):
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    try:
        response = sparql.query().convert()
    except:
        traceback.print_exc()

    # Now to parse the response
    variables = [x for x in response[u'head'][u'vars']]

    # NOTE: Assuming that there's only one variable
    results = [x[variables[0]][u'value'].encode('ascii', 'ignore') for x in response[u'results'][u'bindings']]

    return results


def print_define(results, target, metadata=None):
    for result in results["results"]["bindings"]:
        if result[target]["xml:lang"] == "en":
            print result[target]["value"]
            print


def print_enum(results, target, metadata=None):
    used_labels = []

    for result in results["results"]["bindings"]:
        if result[target]["type"] == u"literal":
            if result[target]["xml:lang"] == "en":
                label = result[target]["value"]
                if label not in used_labels:
                    used_labels.append(label)
                    print label


def print_literal(results, target, metadata=None):
    for result in results["results"]["bindings"]:
        literal = result[target]["value"]
        if metadata:
            print metadata.format(literal)
        else:
            print literal


# print time format for questions like "What time is it in Romania?"
def print_time(results, target, metadata=None):
    gmt = time.mktime(time.gmtime())
    gmt = datetime.datetime.fromtimestamp(gmt)

    for result in results["results"]["bindings"]:
        offset = result[target]["value"].replace(u"−", u"-")

        if ("to" in offset) or ("and" in offset):
            if "to" in offset:
                connector = "and"
                from_offset, to_offset = offset.split("to")
            else:
                connector = "or"
                from_offset, to_offset = offset.split("and")

            from_offset, to_offset = int(from_offset), int(to_offset)

            if from_offset > to_offset:
                from_offset, to_offset = to_offset, from_offset

            from_delta = datetime.timedelta(hours=from_offset)
            to_delta = datetime.timedelta(hours=to_offset)

            from_time = gmt + from_delta
            to_time = gmt + to_delta

            location_string = random.choice(["where you are",
                                             "your location"])

            print "Between %s %s %s, depending on %s" % \
                  (from_time.strftime("%H:%M"),
                   connector,
                   to_time.strftime("%H:%M on %A"),
                   location_string)

        else:
            offset = int(offset)

            delta = datetime.timedelta(hours=offset)
            the_time = gmt + delta

            # prints time, day of week and date
            print the_time.strftime("%H:%M on %A, %d %B %Y")


def print_age(results, target, metadata=None):
    # assert len(results["results"]["bindings"]) == 1
    # because there might be more results
    if len(results["results"]["bindings"]) == 1:
        birth_date = results["results"]["bindings"][0][target]["value"]
    else:
        birth_date = results["results"]["bindings"][1][target]["value"]

    year, month, days = birth_date.split("-")

    birth_date = datetime.date(int(year), int(month), int(days))

    now = datetime.datetime.utcnow()
    now = now.date()

    age = now - birth_date
    print "{} years old".format(age.days / 365)


def wikipedia2dbpedia(wikipedia_url):
    """
    Given a wikipedia URL returns the dbpedia resource
    of that page.
    """

    query = """
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    SELECT * WHERE {
        ?url foaf:isPrimaryTopicOf <%s>.
    }
    """ % wikipedia_url

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    if not results["results"]["bindings"]:
        print "Snorql URL not found"
        sys.exit(1)
    else:
        return results["results"]["bindings"][0]["url"]["value"]


def get_answer(question, sparql):
    if "-d" in sys.argv:
        quepy.set_loglevel("DEBUG")
        sys.argv.remove("-d")

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])

        if question.count("wikipedia.org"):
            print wikipedia2dbpedia(sys.argv[1])
            sys.exit(0)

    print question
    print "-" * len(question)

    target, query, metadata = dbpedia.get_query(question)

    if query is None:
        return "Query not generated :(\n"

    if target.startswith("?"):
        target = target[1:]
    if query:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

    if not results["results"]["bindings"]:
        return "No answer found"

    return query


def getQuestions():
    i = 0
    questions = []
    while i < 5:
        question = getQuestion()
        query = get_answer(question, sparql)

        if query != "Query not generated :(\n" and query != "No answer found":
            i += 1
            questions.append(question)
        else:
            print "Choose another question\n"

    return questions


questions = getQuestions()

with open('questions.txt', 'a') as outfile:
    json.dump(questions, outfile)


def generateQuiz(questions):
    print_handlers = {
        "define": print_define,
        "enum": print_enum,
        "time": print_time,
        "literal": print_literal,
        "age": print_age,
    }

    for question in questions:
        answers = []
        target, query, metadata = dbpedia.get_query(question)

        if isinstance(metadata, tuple):
            query_type = metadata[0]
            metadata = metadata[1]
        else:
            query_type = metadata
            metadata = None

        if target.startswith("?"):
            target = target[1:]
        if query:
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()

        correctAnswer = print_handlers[query_type](results, target, metadata)
        print

        answers.append(correctAnswer)


generateQuiz(questions)