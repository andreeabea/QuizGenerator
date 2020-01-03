# coding=utf-8

import time
import datetime
import random


class DataHandler:

    def __init__(self, results, target, metadata=None):

        self.results = results
        self.target = target
        self.metadata = metadata
        self.data_handlers = {
            "define": self.definition_handler,
            "enum": self.enum_handler,
            "time": self.datetime_handler,
            "literal": self.literal_answer_handler,
            "age": self.age_handler,
        }

    def definition_handler(self):
        answer = ""

        for result in self.results["results"]["bindings"]:
            if result[self.target]["xml:lang"] == "en":
                answer += result[self.target]["value"]

        if answer.find(" is") >= 0:
            return answer.split(" is", 1)[1].split(".", 1)[0]

        if answer.find(" was") >= 0:
            return answer.split(" was", 1)[1].split(".", 1)[0]

        return answer

    def enum_handler(self):
        used_labels = []

        for result in self.results["results"]["bindings"]:
            if result[self.target]["type"] == u"literal":
                if result[self.target]["xml:lang"] == "en":
                    label = result[self.target]["value"]
                    if label not in used_labels:
                        used_labels.append(label)

        return random.choice(used_labels)

    def literal_answer_handler(self):
        answer = ""

        for result in self.results["results"]["bindings"]:
            literal = result[self.target]["value"]
            if self.metadata:
                answer += self.metadata.format(literal)
            else:
                answer += literal

        return answer

    # time format for questions like "What time is it in Romania?"
    def datetime_handler(self):
        gmt = time.mktime(time.gmtime())
        gmt = datetime.datetime.fromtimestamp(gmt)
        answer = ""

        for result in self.results["results"]["bindings"]:
            offset = result[self.target]["value"].replace(u"−", u"-")

            if ("to" in offset) or ("and" in offset):
                if "to" in offset:
                    connector = "and"
                    from_offset, to_offset = offset.split("to")
                else:
                    connector = "or"
                    from_offset, to_offset = offset.split("and")

                # time zone can also be GMT 10.5
                from_offset = float(from_offset) if from_offset.find('.') > -1 else int(from_offset)
                to_offset = float(to_offset) if to_offset.find('.') > -1 else int(to_offset)

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

    def age_handler(self):
        answer = ""

        if len(self.results["results"]["bindings"]) == 1:
            birth_date = self.results["results"]["bindings"][0][self.target]["value"]
        else:
            birth_date = self.results["results"]["bindings"][1][self.target]["value"]

        year, month, days = birth_date.split("-")

        birth_date = datetime.date(int(year), int(month), int(days))

        now = datetime.datetime.utcnow()
        now = now.date()

        age = now - birth_date
        answer += "{} years old".format(age.days / 365)

        return answer



