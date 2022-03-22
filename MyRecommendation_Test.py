# -*- coding: utf-8 -*-

import operator

#Give recommendation
def IwantTo(Input):
    # example (Input = Run)
    global ParkRecAct,Activity,Keyactivity,Locations
    for item in Keyactivity:
        A = Activity[item]
        for B in A:
            if (bool(B == Input)==True):
                Note = item;
    Recc = ParkRecAct[Note]
    accset = Activity[Note]
    LocRec = {}; SortLocRec = {};
    for lcc in Locations:
        Subtract = {};
        Loc = Recc[lcc]
        for aac in accset:
            Subtract[aac] = Loc[1][aac]-Loc[0][aac];
        LocRec[lcc] = Subtract;
        SortLocRec[lcc] = sorted(Subtract.items(), key=operator.itemgetter(1));
    return SortLocRec

Testing = IwantTo('run')