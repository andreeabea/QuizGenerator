# coding=utf-8
import datetime
import json
import sys
import time
import traceback
import quepy
import random
import numpy

from SPARQLWrapper import SPARQLWrapper, JSON

# use dbpedia
from quepy.parsing import Lemma

sparql = SPARQLWrapper("http://dbpedia.org/sparql")

dbpedia = quepy.install("dbpedia")

# questions data dictionary obtained from the json file
jsonData = {}

# get question from user input
def getQuestion():
    print "-" * 100
    s = str(raw_input("enter a question: \n"))
    print "-" * 100
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
    answer = ""
    for result in results["results"]["bindings"]:
        if result[target]["xml:lang"] == "en":
            answer += result[target]["value"]

    if answer.find(" is") >= 0:
        return answer.split(" is", 1)[1].split(".", 1)[0]

    if answer.find(" was") >= 0:
        return answer.split(" was", 1)[1].split(".", 1)[0]

    return answer


def print_enum(results, target, metadata=None):
    used_labels = []

    for result in results["results"]["bindings"]:
        if result[target]["type"] == u"literal":
            if result[target]["xml:lang"] == "en":
                label = result[target]["value"]
                if label not in used_labels:
                    used_labels.append(label)

    return random.choice(used_labels)


def print_literal(results, target, metadata=None):
    answer = ""
    for result in results["results"]["bindings"]:
        literal = result[target]["value"]
        if metadata:
            answer += metadata.format(literal)
        else:
            answer += literal

    return answer


# print time format for questions like "What time is it in Romania?"
def print_time(results, target, metadata=None):
    gmt = time.mktime(time.gmtime())
    gmt = datetime.datetime.fromtimestamp(gmt)
    answer = ""

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

            answer += "Between %s %s %s, depending on %s" % \
                  (from_time.strftime("%H:%M"),
                   connector,
                   to_time.strftime("%H:%M on %A"),
                   location_string)

        else:
            offset = int(offset)

            delta = datetime.timedelta(hours=offset)
            the_time = gmt + delta

            # prints time, day of week and date
            answer += the_time.strftime("%H:%M on %A, %d %B %Y")

    return answer


def print_age(results, target, metadata=None):
    # assert len(results["results"]["bindings"]) == 1
    # because there might be more results
    answer = ""

    if len(results["results"]["bindings"]) == 1:
        birth_date = results["results"]["bindings"][0][target]["value"]
    else:
        birth_date = results["results"]["bindings"][1][target]["value"]

    year, month, days = birth_date.split("-")

    birth_date = datetime.date(int(year), int(month), int(days))

    now = datetime.datetime.utcnow()
    now = now.date()

    age = now - birth_date
    answer += "{} years old".format(age.days / 365)

    return answer


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


def findCategory(query):
    # returns category of question based on the query structure

    if "dbpedia-owl:numberOfEpisodes" in query:
        return "number"

    if "dbpedia-owl:Film" in query:
        return "film"

    if "dbpedia-owl:TelevisionShow" in query:
        return "TVshow"

    if "dbpedia-owl:Album" in query:
        return "album"

    if "dbpedia-owl:author" in query or "dbpprop:creator" in query:
        return "person"

    if "foaf:Person" in query:
        if "dbpedia-owl:birthPlace" in query:
            return "place"
        else:
            if "dbo:birthDate" in query:
                return "number"
            else:
                if "rdfs:comment" in query:
                    return "whoIs"
        return "person"

    if "dbpedia-owl:bandMember" in query:
        return "person"

    if "dbpprop:utcOffset" in query:
        return "datetime"

    if "dbpedia:Place" in query or "dbpedia-owl:location" in query:
        return "place"

    if "dbpedia-owl:PopulatedPlace" in query:
        return "number"

    if "dbpedia-owl:genre" in query:
        return "genre"

    if "dbpedia-owl:Band" in query:
        return "band"

    if "dbpedia-owl:releaseDate" in query or "dbpprop:yearsActive" in query:
        return "datetime"

    if "rdfs:comment" in query:
        return "definition"

    return "none"


def getQuestions():
    i = 0
    questions = []
    while i < 1:
        question = getQuestion()
        query = get_answer(question, sparql)

        if query != "Query not generated :(\n" and query != "No answer found":
            i += 1
            questions.append(question)
        else:
            print "Choose another question\n"

    return questions


def dumpJsonData():
    with open('questions.json', 'w') as outfile:
        json.dump(jsonData, outfile)


def saveQuestions(questions):
    global jsonData
    # questions data in json format
    with open('questions.json') as json_file:
        jsonData = json.load(json_file)

    # checks if question already exists
    for question in questions:
        if question not in jsonData:
            jsonData[question] = []
            jsonData[question].append({
                'category': '',
                })
            with open('questions.txt', 'a') as outfile:
                outfile.write(question + "\n")

    dumpJsonData()


print_handlers = {
        "define": print_define,
        "enum": print_enum,
        "time": print_time,
        "literal": print_literal,
        "age": print_age,
    }


def findWrongAnswers(question):

    global jsonData

    answers = []

    num_lines = sum(1 for line in open('questions.txt'))

    i = 0
    while i < 3:
        x = random.randint(0, num_lines-1)
        with open('questions.txt') as filein:
            line = filein.readline()
            cnt = 0
            while cnt < x:
                cnt += 1
                line = filein.readline()
        target, query, metadata = dbpedia.get_query(line)

        if len(line) > 0 and line[len(line)-1] == '\n':
            line = line[:-1]

        # check if question already has its category in the json file
        if jsonData[line][0]['category'] == '' or jsonData[line][0]['category'] == 'none':
            category = findCategory(query)
            jsonData[line][0]['category'] = category

        if jsonData[question][0]['category'] != jsonData[line][0]['category'] or line.lower() == question.lower():
            continue

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

        answer = print_handlers[query_type](results, target, metadata)

        if answer in answers:
            continue

        answers.append(answer)
        i += 1

    return answers


def generateQuiz(questions):

    global jsonData

    for question in questions:
        target, query, metadata = dbpedia.get_query(question)

        print "-" * 100
        print question
        print "-" * 100

        # check if question already has its category in the json file
        if jsonData[question][0]['category'] == '' or jsonData[question][0]['category'] == 'none':
            category = findCategory(query)
            jsonData[question][0]['category'] = category

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
        print(query)
        correctAnswer = print_handlers[query_type](results, target, metadata)

        answers = findWrongAnswers(question)
        answers.append(correctAnswer)

        randomPositions = numpy.random.permutation(4)
        for i in range(4):
            print(str(i) + ". " + answers[randomPositions[i]])

        givenAnswer = input("Choose an answer: ")
        if answers[randomPositions[givenAnswer]] == correctAnswer:
            print("Correct!\n")
        else:
            print("Incorrect!:(\n")


questions = getQuestions()
saveQuestions(questions)
generateQuiz(questions)

dumpJsonData()

