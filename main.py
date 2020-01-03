# coding=utf-8

from fileWriter import FileWriter
from quizGenerator import QuizGenerator


def main():
    quizGen = QuizGenerator()
    fileWriter = FileWriter()

    questions = quizGen.getQuestions()
    fileWriter.saveQuestions(questions)
    quizGen.generateQuiz(questions, fileWriter.jsonData)

    fileWriter.dumpJsonData()


if __name__ == '__main__':
    main()
