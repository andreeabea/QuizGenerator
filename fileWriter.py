
import json


class FileWriter:

    def __init__(self):

        self.jsonData = {}
        self.jsonFileName = 'questions.json'

    def dumpJsonData(self):
        with open(self.jsonFileName, 'w') as outfile:
            json.dump(self.jsonData, outfile)

    def saveQuestions(self, questions):
        # questions data in json format
        with open(self.jsonFileName) as json_file:
            self.jsonData = json.load(json_file)

        for question in questions:

            if question.startswith("Is"):
                trueFalseAnswer = question.split(" ")[1]
                question = question.replace("Is " + trueFalseAnswer, "What is")

            # checks if question already exists
            if question not in self.jsonData:
                self.jsonData[question] = []
                self.jsonData[question].append({
                    'category': '',
                })
                with open('questions.txt', 'a') as outfile:
                    outfile.write(question + "\n")

        self.dumpJsonData()
