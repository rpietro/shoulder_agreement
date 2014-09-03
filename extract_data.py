# -*- coding: utf-8 -*-
import json

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from pymongo import MongoClient
from bs4 import BeautifulSoup, UnicodeDammit

Base = automap_base()
engine = create_engine('mysql+mysqldb://root@localhost/edxapp')

Base.prepare(engine, reflect=True)
StudentModule = Base.classes.courseware_studentmodule
User = Base.classes.auth_user
session = Session(engine)

client = MongoClient()
db = client.edxapp


if __name__ == '__main__':
    chapters_radius = ['2b59542edcc54ec8a0fe3e14ef3008c7'] # 4aAvaliação
    # chapters_neer = ['e25d9e0f8c594a25b753f02542493377'] # Dia1
    chapters_neer = ['e44592f09b8a4269bd9ea7cb380c845d'] # Dia60
    # chapters_neer = ['5f701314d1bd4003af965aa12006702e'] # Dia30

    student_dict = {}
    problem_keys = set([])

    modulestore = db['modulestore']
    for chapter_id in chapters_neer:
        chap = modulestore.find_one({"_id.category": "chapter",
                                     "_id.name": chapter_id})
        # print chap['metadata']['display_name']
        for seq_id in chap['definition']['children']:
            seq = modulestore.find_one({"_id.category": "sequential",
                                        "_id.name": seq_id.split('/')[-1]})
            # print seq['metadata']['display_name']
            # find vertical with problem
            for ver_id in seq['definition']['children']:
                ver = modulestore.find_one({"_id.category": "vertical",
                                            "_id.name": ver_id.split('/')[-1]})
                for child_id in ver['definition']['children']:
                    if 'problem' in child_id:
                        pro = modulestore.find_one({"_id.category": "problem",
                                                    "_id.name":
                                                    child_id.split('/')[-1]})
                        soup = BeautifulSoup(unicode(pro['definition']['data']))
                        map_choices = {}
                        for ch in enumerate(soup.find_all('choice')):
                            map_choices['choice_' + str(ch[0]+1)] = unicode(BeautifulSoup(unicode(ch[1])).choice.contents[0])
                        for instance in session.query(StudentModule)\
                                .filter(StudentModule.module_id.like('%'
                                        + child_id + '%')):
                            state = json.loads(instance.state)
                            try:
                                k = ''.join(chap['metadata']['display_name'].split(' ')) + ''.join(seq['metadata']['display_name'].split(' '))
                                problem_keys.add(k)
                                if student_dict.get(instance.student_id):
                                    student_dict[instance.student_id].append((k, UnicodeDammit(map_choices[state["student_answers"].values()[0]]).unicode_markup))
                                else:
                                    student_dict[instance.student_id] = []
                                    student_dict[instance.student_id].append((k, UnicodeDammit(map_choices[state["student_answers"].values()[0]]).unicode_markup))
                            except KeyError:
                                pass
        # print student_dict
        # print sorted(problem_keys, cmp=lambda x,y: cmp(int(x.split('aso')[1]), int(y.split('aso')[1])))
        cols = sorted(problem_keys, cmp=lambda x,y: cmp(int(x.split('aso')[1]), int(y.split('aso')[1])))
        print u"subject_id;" + u";".join(cols)
        for k in student_dict.keys():
            d_k = dict(student_dict[k])
            stu_line = []
            for col in cols:
                stu_line.append(d_k.get(col, ''))
            u = session.query(User).get(k)
            print (unicode(u.email) + u";" + u';'.join(stu_line)).encode("utf-8")
            # print seq['_id']['name']
            # for ver in get_verticals(seq['_id']['name']):
                # print ver
