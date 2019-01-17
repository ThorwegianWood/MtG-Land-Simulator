from random import shuffle
from itertools import combinations, combinations_with_replacement
from collections import Counter, OrderedDict
import re
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QGridLayout,
        QTableWidget, QTableWidgetItem, QPushButton, QSpinBox, QMainWindow)
from PyQt5.QtGui import QFont
from PyQt5 import QtCore

class LandMeta(type):
    """We define a metaclass to ensure duolands inherit the colors of both
    parents. Also remembers all subclasses of Land for convenience in setting up
    the GUI.
    """
    CHILDREN = []
    def __init__(cls, name, bases, clsdict):
        cls.CHILDREN.append(cls)
        super().__init__(name, bases, clsdict)

    def __new__(cls, name, bases, clsdict):
        if "COLORS" not in clsdict:
            clsdict["COLORS"] = ""
            for klass in bases:
                if hasattr(klass, 'COLORS'):
                    clsdict["COLORS"] += klass.COLORS
        return type.__new__(cls, name, bases, clsdict)

class NonLand:
    """Convenience class for issubclass comparisons.
    """
    pass

class Land(metaclass=LandMeta):
    """The basic land class, defines some basic functionality.
    """
    COLORS = ""

    @classmethod
    def get_colors(cls):
        return cls.COLORS

    @classmethod
    def name(cls):
        return re.sub(r"(\w)([A-Z])", r"\1 \2", cls.__name__)

    def __str__(self):
        return re.sub(r"(\w)([A-Z])", r"\1 \2", self.__class__.__name__)

### BASIC LANDS ###

class Mountain(Land):
    COLORS = "R"

class Island(Land):
    COLORS = "U"

class Swamp(Land):
    COLORS = "B"

class Plains(Land):
    COLORS = "W"

class Forest(Land):
    COLORS = "G"


### CHECKLANDS ###

class GlacialFortress(Plains, Island):
    pass

class DrownedCatacomb(Swamp, Island):
    pass

class DragonskullSummit(Swamp, Mountain):
    pass

class RootboundCrag(Mountain, Forest):
    pass

class SunpetalGrove(Plains, Forest):
    pass

class IsolatedChapel(Plains, Swamp):
    pass

class SulfurFalls(Mountain, Island):
    pass

class WoodlandCemetery(Forest, Swamp):
    pass

class ClifftopRetreat(Mountain, Plains):
    pass

class HinterlandHarbor(Forest, Island):
    pass


### SHOCKLANDS ###

class HallowedFountain(Plains, Island):
    pass

class WateryGrave(Swamp, Island):
    pass

class BloodCrypt(Swamp, Mountain):
    pass

class StompingGrounds(Mountain, Forest):
    pass

class TempleGarden(Forest, Plains):
    pass

class GodlessShrine(Plains, Swamp):
    pass

class SteamVents(Mountain, Island):
    pass

class OvergrownTomb(Forest, Swamp):
    pass

class SacredFoundry(Mountain, Plains):
    pass

class BreedingPool(Forest, Island):
    pass


### GATELANDS ###

class AzoriusGuildgate(Plains, Island):
    pass

class DimirGuildgate(Swamp, Island):
    pass

class RakdosGuildgate(Swamp, Mountain):
    pass

class GruulGuildgate(Mountain, Forest):
    pass

class SelesnyaGuildgate(Forest, Plains):
    pass

class OrzhovGuildgate(Plains, Island):
    pass

class IzzetGuildgate(Island, Mountain):
    pass

class GolgariGuildgate(Swamp, Forest):
    pass

class BorosGuildgate(Mountain, Plains):
    pass

class SimicGuildgate(Forest, Island):
    pass


### TAPLANDS ###

class MeanderingRiver(Plains, Island):
    pass

class ForsakenSanctuary(Plains, Swamp):
    pass

class SubmergedBoneyard(Swamp, Island):
    pass

class HighlandLake(Island, Mountain):
    pass

class CinderBarrens(Swamp, Mountain):
    pass

class FoulOrchard(Swamp, Forest):
    pass

class TimberGorge(Mountain, Forest):
    pass

class StoneQuarry(Mountain, Plains):
    pass

class TranquilExpanse(Forest, Plains):
    pass

class WoodlandStream(Forest, Island):
    pass

#SAMPLE_LANDS = [Swamp() for i in range(10)]


LANDVAL = ['x', 'W', 'U', 'B', 'R', 'G']
def sort_lands(lands):
    """A function to sort the lands we use"""
    return int("".join(str(LANDVAL.index(c)+1) for c in lands))


def count_lands(hand, land=Land):
    return sum(issubclass(x, land) for x in hand)


def colors_in_deck(lands):
    """Convenience function that returns the colors available in the deck.
    """
    colors = []
    for land in lands:
        for c in land.COLORS:
            if c not in colors:
                colors.append(c)
    return sorted(colors, key=lambda l: sort_lands(l))

def check_lands(mana, lands):
    """Check whether we have the requisite lands to cast a certain spell.
    This function is important for things like Niv-Mizzet, where a more general
    function would let a dual land "double-dip" on the casting cost.

    colors: the color combination we are considering, incl. x as colorless
    lands: the lands we have available

    Returns whether we can cast the spell.
    """
    manacost = len(mana)
    color = Counter(mana)
    if "x" in color:
        del color["x"]
    duos = []
    nonduos = []
    costs = {}
    for x in lands:
        if set(x.COLORS) == set(mana):
            duos.append(x)
        else:
            nonduos.append(x)

    for k, v in color.items():
        costs[k] = max(v - sum(1 if k in x.COLORS else 0 for x in nonduos), 0)
    if sum(costs.values()) <= len(duos) and manacost <= len(lands):
        return True
    return False

def two_color_combos(colors, maxmana, minmana=1):
    """Find all available combinations of colors in the deck (R, UR, UUR etc.)
    x is used to represent uncolored mana. We only consider combinations of up
    to 2 colors.

    Returns a sorted list of all combinations.
    """
    combos = list(combinations(colors, 2)) or colors
    tccs = []
    for i in range(minmana, maxmana + 1):
        for c in combos:
            tccs = tccs + list(set(combinations_with_replacement(["x"]+list(c), i)) - set(tccs))
    return sorted(tccs, key=lambda l: sort_lands(l))

def is_land(x):
    return True if issubclass(x, Land) else False

def simulate(lands, turns, decksize, runs):
    """Simulate the first few turns of a Magic game with a given landbase to
    find the regularity with which cards can be cast on curve.

    lands: list of Land objects in the deck
    turns: number of turns to simulate
    decksize: number of cards in the deck
    runs: number of times to run the simulation (more=more accurate results)
    """
    library = [lands[i] if i < len(lands) else NonLand for i in range(decksize)]
    colors = colors_in_deck(lands)
    tccs = two_color_combos(colors, turns)
    results = OrderedDict()
    for k in tccs:
        results["".join(k)] = []
    avghand = []
    for i in range(runs):
        shuffle(library)

        # START OF GAME
        hand = library[:7]
        library = library[7:]

        # MULLIGAN PHASE
        # GUIDELINES FROM https://www.channelfireball.com/articles/how-many-lands-do-you-need-to-consistently-hit-your-land-drops/
        if not (1 < count_lands(hand) < 6):
            library = hand + library
            shuffle(library)
            hand = library[:6]
            library = library[6:]
            if not (1 < count_lands(hand) < 5):
                library = hand + library
                shuffle(library)
                hand = library[:5]
                library = library[5:]
                if not (0 < count_lands(hand) < 5):
                    library = hand + library
                    shuffle(library)
                    hand = library[:4]
                    library = library[4:]
            if library[0] == NonLand:
                library = library[1:] + library[:1]

        # Hand size post-mull is saved
        avghand.append(len(hand))

        # To simplify, we assume all cards we are casting require at most two
        # different colors (true for most decks).
        for j in range(1, turns+1):
            lands = list(filter(is_land, hand))
            for c in two_color_combos(colors, j, j):
                results["".join(c)].append(check_lands(c, lands))
            hand = hand + library[:1]
            library = library[1:]
        library = library + hand

    return (results, avghand)

######
# GRAPHICS LOOP
######

def mainloop():
    """Run the graphics interface for the program.
    """
    def on_click():
        l = []
        for k in lands:
            if k[1].value() > 0:
                l += [k[0] for i in range(k[1].value())]
        res, avghand = simulate(l, turns.value(), deck.value(), numruns.value())
        i = 0
        output.setRowCount(2)
        output.setColumnCount(len(res)+1)
        for k, v in res.items():
            output.setItem(0, i, QTableWidgetItem(k))
            output.setItem(1, i, QTableWidgetItem(str(100*sum(v)/numruns.value())))
            i += 1
        output.setItem(0, i, QTableWidgetItem("Hand"))
        output.setItem(1, i, QTableWidgetItem(str(sum(avghand)/numruns.value())))
        output.resizeColumnsToContents()
        output.resizeRowsToContents()


    def land_table_layout(k, j):
        for i in range(k, j):
            c = LandMeta.CHILDREN[i]
            x = 0 if k == 1 else 3*(k-6)//10+3
            layout.addWidget(QLabel(c.name()), i-k+1+loy, x+lox)
            layout.addWidget(QLabel(c.get_colors()), i-k+1+loy, x+1+lox)
            lands.append((c, QSpinBox()))
            if i > 5:
                lands[i-1][1].setMaximum(4)
            layout.addWidget(lands[i-1][1], i-k+1+loy, x+2+lox)

    app = QApplication([])
    main = QMainWindow()
    main.setWindowTitle("Land Simulator (Standard)")
    window = QWidget()
    window.resize(800, 600)
    layout = QGridLayout()
    lands = []

    output = QTableWidget()
    output.horizontalHeader().hide()
    output.verticalHeader().hide()
    output.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
    layout.addWidget(output, 0, 0, 1, 15)

    controlslayout = QGridLayout()
    controlslayout.addWidget(QLabel("Runs: "), 0, 0)
    controlslayout.setContentsMargins(0, 0, 0, 20)
    numruns = QSpinBox()
    numruns.setMaximum(1000000)
    numruns.setValue(10000)
    controlslayout.addWidget(numruns, 0, 1)

    controlslayout.addWidget(QLabel("Turns: "), 0, 2)
    turns = QSpinBox()
    turns.setValue(4)
    controlslayout.addWidget(turns, 0, 3)

    controlslayout.addWidget(QLabel("Deck size: "), 0, 4)
    deck = QSpinBox()
    deck.setValue(60)
    controlslayout.addWidget(deck, 0, 5)

    layout.addLayout(controlslayout, 1, 0, 1, 4)

    titlefont = QFont()
    titlefont.setBold(True)

    titles = [
        QLabel("Basic Lands"),
        QLabel("Checklands"),
        QLabel("Shocklands"),
        QLabel("Gatelands"),
        QLabel("Taplands")
    ]

    [i.setFont(titlefont) or i.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom) for i in titles]


    lox = 0
    loy = 2
    layout.addWidget(titles[0], loy, lox)
    land_table_layout(1, 6)
    layout.addWidget(titles[1], loy, 3+lox)
    land_table_layout(6, 16)
    layout.addWidget(titles[2], loy, 6+lox)
    land_table_layout(16, 26)
    layout.addWidget(titles[3], loy, 9+lox)
    land_table_layout(26, 36)
    layout.addWidget(titles[4], loy, 12+lox)
    land_table_layout(36, 46)
    button = QPushButton("Calculate")
    button.clicked.connect(on_click)
    layout.addWidget(button, 8, 0, 1, 3)
    window.setLayout(layout)
    main.setCentralWidget(window)
    main.show()
    app.exec_()

if __name__ == "__main__":
    mainloop()
