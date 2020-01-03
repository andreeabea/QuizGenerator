
import traceback
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import quepy
import numpy

from dataHandlers import DataHandler, random


class QuizGenerator:

    def __init__(self):

        self.sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        self.dbpedia = quepy.install("dbpedia")

    # transform question to sparql query
    def get_SparqlQuery(self, question):
        target, query, metadata = self.dbpedia.get_query(question)
        # filter answers only in English
        # query += "FILTER (langMatches(lang(?x2),\"en\"))\n}"
        return query

    # get answers as list from sparql query
    def get_answer_list_test(self, query):
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        try:
            response = self.sparql.query().convert()
        except Exception as e:
            traceback.print_exc(file=sys.stdout)

        # Now to parse the response
        variables = [x for x in response[u'head'][u'vars']]

        # NOTE: Assuming that there's only one variable
        results = [x[variables[0]][u'value'].encode('ascii', 'ignore') for x in response[u'results'][u'bindings']]

        return results

    def get_answer(self, question):
        if "-d" in sys.argv:
            quepy.set_loglevel("DEBUG")
            sys.argv.remove("-d")

        if len(sys.argv) > 1:
            question = " ".join(sys.argv[1:])

        target, query, metadata = self.dbpedia.get_query(question)

        if query is None:
            return "Query not generated :(\n"

        if target.startswith("?"):
            target = target[1:]
        if query:
            self.sparql.setQuery(query)
            self.sparql.setReturnFormat(JSON)
            results = self.sparql.query().convert()

        if not results["results"]["bindings"]:
            return "No answer found"

        return query

    @staticmethod
    def getQuestion():
        print "-" * 100
        s = str(raw_input("enter a question: \n"))
        print "-" * 100
        return s

    def getQuestions(self):
        i = 0
        questions = []

        nbQuestions = input("Number of questions of the quiz: ")

        while i < nbQuestions:
            question = QuizGenerator.getQuestion()
            query = self.get_answer(question)

            if query != "Query not generated :(\n" and query != "No answer found" or question.startswith("Is"):
                i += 1
                questions.append(question)
            else:
                print "Choose another question\n"

        return questions

    @staticmethod
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

        if "dbpedia:Place" in query or "dbpedia-owl:location" in query or "dbpedia-owl:capital" in query:
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

    def findWrongAnswers(self, question, jsonData):

        answers = []

        num_lines = sum(1 for line in open('questions.txt'))

        i = 0
        while i < 3:
            x = random.randint(0, num_lines - 1)
            with open('questions.txt') as filein:
                line = filein.readline()
                cnt = 0
                while cnt < x:
                    cnt += 1
                    line = filein.readline()

            if line.startswith("Is"):
                trueFalseAnswer = line.split(" ")[1]
                line = line.replace("Is " + trueFalseAnswer, "What is")

            target, query, metadata = self.dbpedia.get_query(line)

            if len(line) > 0 and line[len(line) - 1] == '\n':
                line = line[:-1]

            # check if question already has its category in the json file
            if jsonData[line][0]['category'] == '' or jsonData[line][0]['category'] == 'none':
                category = QuizGenerator.findCategory(query)
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
                self.sparql.setQuery(query)
                self.sparql.setReturnFormat(JSON)
                results = self.sparql.query().convert()

            dataHandler = DataHandler(results, target, metadata)
            answer = dataHandler.data_handlers[query_type]()

            if answer in answers:
                continue

            answers.append(answer)
            i += 1

        return answers

    def generateQuiz(self, questions, jsonData):

        score = 0
        for question in questions:

            initQuestion = question
            isTrueFalseQuestion = False
            if question.startswith("Is"):
                isTrueFalseQuestion = True
                trueFalseAnswer = question.split(" ")[1]
                question = question.replace("Is " + trueFalseAnswer, "What is")

            target, query, metadata = self.dbpedia.get_query(question)

            print "-" * 100
            print initQuestion
            print "-" * 100

            # check if question already has its category in the json file
            if jsonData[question][0]['category'] == '' or jsonData[question][0]['category'] == 'none':
                category = QuizGenerator.findCategory(query)
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
                self.sparql.setQuery(query)
                self.sparql.setReturnFormat(JSON)
                results = self.sparql.query().convert()

            dataHandler = DataHandler(results, target, metadata)
            correctAnswer = dataHandler.data_handlers[query_type]()

            if isTrueFalseQuestion:
                print(str(0) + ". " + "True")
                print(str(1) + ". " + "False")
                answers = None
            else:
                answers = self.findWrongAnswers(question, jsonData)
                answers.append(correctAnswer)

                randomPositions = numpy.random.permutation(4)
                for i in range(4):
                    print(str(i) + ". " + answers[randomPositions[i]])

            givenAnswer = input("Choose an answer: ")

            if isTrueFalseQuestion:
                if (trueFalseAnswer == correctAnswer and givenAnswer == 0) \
                        or (trueFalseAnswer != correctAnswer and givenAnswer == 1):
                    print("Correct!\n")
                    score += 1
                else:
                    print("Incorrect!:(\nThe correct answer is: " + correctAnswer + " \n")
            else:
                if answers[randomPositions[givenAnswer]] == correctAnswer:
                    print("Correct!\n")
                    score += 1
                else:
                    print("Incorrect!:(\nThe correct answer is: " + correctAnswer + " \n")

        print("Final score: " + str(score))
