from PySide6 import QtCore, QtWidgets
from UI.ui_form import Ui_MainWindow
from UI.progress_window import ProgressWindow
from update import UpdateProcess
from randomizer_paths import IS_RUNNING_FROM_SOURCE
from randomizer_data import *

import yaml
from indentation import MyDumper

import os
import random
from re import findall, sub



class MainWindow(QtWidgets.QMainWindow):
    
    def __init__(self):
        super (MainWindow, self).__init__()
        # self.trans = QtCore.QTranslator(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # self.options = ([('English', ''), ('Français', 'eng-fr' ), ('中文', 'eng-chs'), ])

        # Keep track of stuff
        self.mode = str('light')
        self.excluded_checks = set()
        self.starting_gear = list()
        self.overworld_owls = bool(False)
        self.dungeon_owls = bool(False)

        # Load User Settings
        if not DEFAULTS:
            self.loadSettings()
        else:
            self.applyDefaults()
        
        self.updateOwls()
        
        if self.mode == 'light':
            self.setStyleSheet(LIGHT_STYLESHEET)
            self.ui.explainationLabel.setStyleSheet('color: rgb(80, 80, 80);')
        else:
            self.setStyleSheet(DARK_STYLESHEET)
            self.ui.explainationLabel.setStyleSheet('color: rgb(175, 175, 175);')

        ### SUBSCRIBE TO EVENTS
        
        # menu bar items
        self.ui.actionLight.triggered.connect(self.setLightMode)
        self.ui.actionDark.triggered.connect(self.setDarkMode)
        self.ui.actionChangelog.triggered.connect(self.showChangelog)
        self.ui.actionKnown_Issues.triggered.connect(self.showIssues)
        # folder browsing, seed generation, and randomize button
        self.ui.browseButton1.clicked.connect(self.romBrowse)
        self.ui.browseButton2.clicked.connect(self.outBrowse)
        self.ui.seedButton.clicked.connect(self.generateSeed)
        self.ui.randomizeButton.clicked.connect(self.randomizeButton_Clicked)
        self.ui.resetButton.clicked.connect(self.applyDefaults)
        # progress checks
        self.ui.chestsCheck.clicked.connect(self.chestsCheck_Clicked)
        self.ui.fishingCheck.clicked.connect(self.fishingCheck_Clicked)
        self.ui.rapidsCheck.clicked.connect(self.rapidsCheck_Clicked)
        self.ui.dampeCheck.clicked.connect(self.dampeCheck_Clicked)
        # self.ui.trendyCheck.clicked.connect(self.trendyCheck_Clicked)
        self.ui.giftsCheck.clicked.connect(self.giftsCheck_Clicked)
        self.ui.tradeGiftsCheck.clicked.connect(self.tradeQuest_Clicked)
        self.ui.bossCheck.clicked.connect(self.bossCheck_Clicked)
        self.ui.miscellaneousCheck.clicked.connect(self.miscellaneousCheck_Clicked)
        self.ui.heartsCheck.clicked.connect(self.heartsCheck_Clicked)
        self.ui.rupCheck.clicked.connect(self.rupCheck_Clicked)
        self.ui.seashellsComboBox.currentIndexChanged.connect(self.updateSeashells)
        self.ui.leavesCheck.clicked.connect(self.leavesCheck_Clicked)
        self.ui.owlsComboBox.currentIndexChanged.connect(self.updateOwls)
        # locations tab
        self.ui.tabWidget.currentChanged.connect(self.tab_Changed)
        self.ui.includeButton.clicked.connect(self.includeButton_Clicked)
        self.ui.excludeButton.clicked.connect(self.excludeButton_Clicked)
        self.ui.includeButton_3.clicked.connect(self.includeButton_3_Clicked)
        self.ui.excludeButton_3.clicked.connect(self.excludeButton_3_Clicked)
        ### DESCRIPTIONS
        desc_items = self.ui.tab.findChildren(QtWidgets.QCheckBox)
        desc_items.extend([
            self.ui.seashellsComboBox,
            self.ui.tricksComboBox,
            self.ui.instrumentsComboBox,
            self.ui.owlsComboBox,
            self.ui.goalComboBox
        ])
        for item in desc_items:
            item.installEventFilter(self)
        
        ### show and check for updates
        self.setFixedSize(780, 640)
        self.setWindowTitle(f'{self.windowTitle()} v0.3.0-alpha-2') # {VERSION}')

        # self.ui.retranslateUi(self)

        self.show()

        if IS_RUNNING_FROM_SOURCE:
            self.ui.updateChecker.setText('Running from source. No updates will be checked')
        else:
            self.process = UpdateProcess() # initialize a new QThread class
            self.process.can_update.connect(self.showUpdate) # connect a boolean signal to ShowUpdate()
            self.process.start() # start the thread



    # event filter for showing option info onto label
    def eventFilter(self, source, event):
        
        if event.type() == QtCore.QEvent.Type.HoverEnter: # Display description text of items when hovered over
            self.ui.explainationLabel.setText(source.whatsThis())
            if self.mode == 'light':
                self.ui.explainationLabel.setStyleSheet('color: black;')
            else:
                self.ui.explainationLabel.setStyleSheet('color: white;')
        
        elif event.type() == QtCore.QEvent.Type.HoverLeave: # Display default text when item is no longer hovered over
            self.ui.explainationLabel.setText('Hover over an option to see what it does')
            if self.mode == 'light':
                self.ui.explainationLabel.setStyleSheet('color: rgb(80, 80, 80);')
            else:
                self.ui.explainationLabel.setStyleSheet('color: rgb(175, 175, 175);')
            
            # if isinstance(source, QtWidgets.QComboBox) and source.hasFocus():
            #     source.clearFocus()
                
        return QtWidgets.QWidget.eventFilter(self, source, event)
    


    # show update if there is one
    def showUpdate(self, update):
        if update:
            self.ui.updateChecker.setText(f"<a href='{DOWNLOAD_PAGE}'>Update found!</a>")
        else:
            self.ui.updateChecker.setText('No updates available')
    


    # apply defaults
    def applyDefaults(self):
        self.ui.chestsCheck.setChecked(True)
        self.excluded_checks.difference_update(MISCELLANEOUS_CHESTS)

        self.ui.fishingCheck.setChecked(True)
        self.excluded_checks.difference_update(FISHING_REWARDS)

        self.ui.rapidsCheck.setChecked(False)
        self.excluded_checks.update(RAPIDS_REWARDS)

        self.ui.dampeCheck.setChecked(False)
        self.excluded_checks.update(DAMPE_REWARDS)

        # self.ui.trendyCheck.setChecked(False)
        # self.excluded_checks.update(TRENDY_REWARDS)

        self.ui.giftsCheck.setChecked(True)
        self.excluded_checks.difference_update(FREE_GIFT_LOCATIONS)

        self.ui.tradeGiftsCheck.setChecked(False)
        self.excluded_checks.update(TRADE_GIFT_LOCATIONS)

        self.ui.bossCheck.setChecked(True)
        self.excluded_checks.difference_update(BOSS_LOCATIONS)

        self.ui.miscellaneousCheck.setChecked(True)
        self.excluded_checks.difference_update(MISC_LOCATIONS)

        self.ui.heartsCheck.setChecked(True)
        self.excluded_checks.difference_update(HEART_PIECE_LOCATIONS)

        self.ui.instrumentCheck.setChecked(True)
        self.ui.instrumentsComboBox.setCurrentIndex(0)

        self.ui.seashellsComboBox.setCurrentIndex(2)
        self.excluded_checks.difference_update(set(['5-seashell-reward', '15-seashell-reward']))
        self.excluded_checks.update(set(['30-seashell-reward', '40-seashell-reward', '50-seashell-reward']))

        self.ui.leavesCheck.setChecked(True)
        self.excluded_checks.difference_update(LEAF_LOCATIONS)

        self.ui.tricksComboBox.setCurrentIndex(0)

        self.ui.bookCheck.setChecked(True)
        self.ui.unlockedBombsCheck.setChecked(True)
        self.ui.shuffledBombsCheck.setChecked(False)
        self.ui.fastTrendyCheck.setChecked(False)
        self.ui.stealingCheck.setChecked(True)
        self.ui.farmingCheck.setChecked(True)
        self.ui.shuffledPowderCheck.setChecked(False)
        self.ui.musicCheck.setChecked(False)
        self.ui.enemyCheck.setChecked(False)
        self.ui.spoilerCheck.setChecked(True)
        self.ui.kanaletCheck.setChecked(True)
        self.ui.badPetsCheck.setChecked(False)
        self.ui.trapsCheck.setChecked(False)
        self.ui.rupCheck.setChecked(False)
        self.ui.bridgeCheck.setChecked(True)
        self.ui.mazeCheck.setChecked(True)
        self.ui.swampCheck.setChecked(False)
        self.ui.fastMSCheck.setChecked(False)
        self.ui.chestSizesCheck.setChecked(False)
        self.ui.songsCheck.setChecked(False)
        self.ui.fastFishingCheck.setChecked(True)
        self.ui.owlsComboBox.setCurrentIndex(0)
        self.ui.dungeonsCheck.setChecked(False)

        self.starting_gear = list() # fully reset starting items

        self.tab_Changed() # just call the same event as when changing the tab to refresh the list



    def saveSettings(self):
        settings_dict = {
            'Theme': self.mode,
            'Romfs_Folder': self.ui.lineEdit.text(),
            'Output_Folder': self.ui.lineEdit_2.text(),
            'Seed': self.ui.lineEdit_3.text(),
            'Logic': LOGIC_PRESETS[self.ui.tricksComboBox.currentIndex()],
            'Create_Spoiler': self.ui.spoilerCheck.isChecked(),
            'NonDungeon_Chests': self.ui.chestsCheck.isChecked(),
            'Fishing': self.ui.fishingCheck.isChecked(),
            'Rapids': self.ui.rapidsCheck.isChecked(),
            'Dampe': self.ui.dampeCheck.isChecked(),
            # 'Trendy': self.ui.trendyCheck.isChecked(),
            'Free_Gifts': self.ui.giftsCheck.isChecked(),
            'Trade_Quest': self.ui.tradeGiftsCheck.isChecked(),
            'Boss_Drops': self.ui.bossCheck.isChecked(),
            'Miscellaneous': self.ui.miscellaneousCheck.isChecked(),
            'Heart_Pieces': self.ui.heartsCheck.isChecked(),
            'Golden_Leaves': self.ui.leavesCheck.isChecked(),
            'Instruments': self.ui.instrumentCheck.isChecked(),
            'Starting_Instruments': self.ui.instrumentsComboBox.currentIndex(),
            'Seashells': SEASHELL_VALUES[self.ui.seashellsComboBox.currentIndex()],
            'Free_Book': self.ui.bookCheck.isChecked(),
            'Unlocked_Bombs': self.ui.unlockedBombsCheck.isChecked(),
            'Shuffled_Bombs': self.ui.shuffledBombsCheck.isChecked(),
            'Bad_Pets': self.ui.badPetsCheck.isChecked(),
            'Fast_Fishing': self.ui.fastFishingCheck.isChecked(),
            'Fast_Stealing': self.ui.stealingCheck.isChecked(),
            'Fast_Trendy': self.ui.fastTrendyCheck.isChecked(),
            'Fast_Songs': self.ui.songsCheck.isChecked(),
            'Fast_Master_Stalfos': self.ui.fastMSCheck.isChecked(),
            'Scaled_Chest_Sizes': self.ui.chestSizesCheck.isChecked(),
            'Reduced_Farming': self.ui.farmingCheck.isChecked(),
            'Shuffled_Powder': self.ui.shuffledPowderCheck.isChecked(),
            'Open_Kanalet': self.ui.kanaletCheck.isChecked(),
            'Open_Bridge': self.ui.bridgeCheck.isChecked(),
            'Open_Mamu': self.ui.mazeCheck.isChecked(),
            'Trapsanity': self.ui.trapsCheck.isChecked(),
            'Blupsanity': self.ui.rupCheck.isChecked(),
            'Classic_D2': self.ui.swampCheck.isChecked(),
            'Owl_Statues': OWLS_SETTINGS[self.ui.owlsComboBox.currentIndex()],
            # 'Shuffled_Companions': self.ui.companionCheck.isChecked(),
            # 'Randomize_Entrances': self.ui.loadingCheck.isChecked(),
            'Randomize_Music': self.ui.musicCheck.isChecked(),
            'Randomize_Enemies': self.ui.enemyCheck.isChecked(),
            'Shuffled_Dungeons': self.ui.dungeonsCheck.isChecked(),
            'Starting_Items': self.starting_gear,
            'Excluded_Locations': list(self.excluded_checks)
        }
        
        with open(SETTINGS_PATH, 'w') as settingsFile:
            yaml.dump(settings_dict, settingsFile, Dumper=MyDumper, sort_keys=False)



    def loadSettings(self):
        
        # theme
        try:
            if SETTINGS['Theme'].lower() in ['light', 'dark']:
                self.mode = str(SETTINGS['Theme'].lower())
            else:
                self.mode = str('light')
        except (KeyError, AttributeError, TypeError):
            self.mode = str('light')

        # romfs folder
        try:
            if os.path.exists(SETTINGS['Romfs_Folder']):
                self.ui.lineEdit.setText(SETTINGS['Romfs_Folder'])
        except (KeyError, TypeError):
            pass
        
        # output folder
        try:
            if os.path.exists(SETTINGS['Output_Folder']):
                self.ui.lineEdit_2.setText(SETTINGS['Output_Folder'])
        except (KeyError, TypeError):
            pass
        
        # seed
        try:
            if SETTINGS['Seed'] != "":
                self.ui.lineEdit_3.setText(SETTINGS['Seed'])
        except (KeyError, TypeError):
            pass
        
        # nondungeon chests
        try:
            self.ui.chestsCheck.setChecked(SETTINGS['NonDungeon_Chests'])
        except (KeyError, TypeError):
            self.ui.chestsCheck.setChecked(True)
        
        # fishing
        try:
            self.ui.fishingCheck.setChecked(SETTINGS['Fishing'])
        except (KeyError, TypeError):
            self.ui.fishingCheck.setChecked(True)
        
        # fast fishing
        try:
            self.ui.fastFishingCheck.setChecked(SETTINGS['Fast-Fishing'])
        except (KeyError, TypeError):
            self.ui.fastFishingCheck.setChecked(True)
        
        # rapids
        try:
            self.ui.rapidsCheck.setChecked(SETTINGS['Rapids'])
        except (KeyError, TypeError):
            self.ui.rapidsCheck.setChecked(False)
        
        # dampe
        try:
            self.ui.dampeCheck.setChecked(SETTINGS['Dampe'])
        except (KeyError, TypeError):
            self.ui.dampeCheck.setChecked(False)
        
        # # trendy
        # try:
        #     self.ui.trendyCheck.setChecked(SETTINGS['Trendy'])
        # except (KeyError, TypeError):
        #     self.ui.trendyCheck.setChecked(True)
        
        # free gifts
        try:
            self.ui.giftsCheck.setChecked(SETTINGS['Free_Gifts'])
        except (KeyError, TypeError):
            self.ui.giftsCheck.setChecked(True)
        
        # trade gifts
        try:
            self.ui.tradeGiftsCheck.setChecked(SETTINGS['Trade_Quest'])
        except (KeyError, TypeError):
            self.ui.tradeGiftsCheck.setChecked(False)
        
        # boss drops
        try:
            self.ui.bossCheck.setChecked(SETTINGS['Boss_Drops'])
        except (KeyError, TypeError):
            self.ui.bossCheck.setChecked(True)
        
        # misc items
        try:
            self.ui.miscellaneousCheck.setChecked(SETTINGS['Miscellaneous'])
        except (KeyError, TypeError):
            self.ui.miscellaneousCheck.setChecked(True)
        
        # heart pieces
        try:
            self.ui.heartsCheck.setChecked(SETTINGS['Heart_Pieces'])
        except (KeyError, TypeError):
            self.ui.heartsCheck.setChecked(True)
        
        # instruments
        try:
            self.ui.instrumentCheck.setChecked(SETTINGS['Instruments'])
        except (KeyError, TypeError):
            self.ui.instrumentCheck.setChecked(True)
        
        # golden leaves
        try:
            self.ui.leavesCheck.setChecked(SETTINGS['Golden_Leaves'])
        except (KeyError, TypeError):
            self.ui.leavesCheck.setChecked(True)

        # starting instruments
        try:
            self.ui.instrumentsComboBox.setCurrentIndex(SETTINGS['Starting_Instruments'])
        except (KeyError, TypeError):
            self.ui.instrumentsComboBox.setCurrentIndex(0)

        # seashells
        try:
            self.ui.seashellsComboBox.setCurrentIndex(SEASHELL_VALUES.index(SETTINGS['Seashells']))
        except (KeyError, TypeError, IndexError) as e:
            print(e.args)
            self.ui.seashellsComboBox.setCurrentIndex(2)
        
        # logic
        try:
            self.ui.tricksComboBox.setCurrentIndex(LOGIC_PRESETS.index(SETTINGS['Logic'].lower().strip()))
        except (KeyError, TypeError, IndexError):
            self.ui.tricksComboBox.setCurrentIndex(0)
        
        # free book
        try:
            self.ui.bookCheck.setChecked(SETTINGS['Free_Book'])
        except (KeyError, TypeError):
            self.ui.bookCheck.setChecked(True)
        
        # unlocked bombs
        try:
            self.ui.unlockedBombsCheck.setChecked(SETTINGS['Unlocked_Bombs'])
        except (KeyError, TypeError):
            self.ui.unlockedBombsCheck.setChecked(True)
        
        # fast trendy
        try:
            self.ui.fastTrendyCheck.setChecked(SETTINGS['Fast_Trendy'])
        except (KeyError, TypeError):
            self.ui.fastTrendyCheck.setChecked(False)
        
        # shuffled bombs
        try:
            self.ui.shuffledBombsCheck.setChecked(SETTINGS['Shuffled_Bombs'])
        except (KeyError, TypeError):
            self.ui.shuffledBombsCheck.setChecked(False)

        # fast stealing
        try:
            self.ui.stealingCheck.setChecked(SETTINGS['Fast_Stealing'])
        except (KeyError, TypeError):
            self.ui.stealingCheck.setChecked(True)
        
        # fast songs
        try:
            self.ui.songsCheck.setChecked(SETTINGS['Fast_Songs'])
        except (KeyError, TypeError):
            self.ui.songsCheck.setChecked(False)
        
        # fast master stalfos
        try:
            self.ui.fastMSCheck.setChecked(SETTINGS['Fast_Master_Stalfos'])
        except (KeyError, TypeError):
            self.ui.fastMSCheck.setChecked(False)
        
        # scaled chest sizes
        try:
            self.ui.chestSizesCheck.setChecked(SETTINGS['Scaled_Chest_Sizes'])
        except (KeyError, TypeError):
            self.ui.chestSizesCheck.setChecked(False)
        
        # reduced farming
        try:
            self.ui.farmingCheck.setChecked(SETTINGS['Reduced_Farming'])
        except (KeyError, TypeError):
            self.ui.farmingCheck.setChecked(True)
        
        # shuffled powder
        try:
            self.ui.shuffledPowderCheck.setChecked(SETTINGS['Shuffled_Powder'])
        except (KeyError, TypeError):
            self.ui.shuffledPowderCheck.setChecked(False)
        
        # open kanalet
        try:
            self.ui.kanaletCheck.setChecked(SETTINGS['Open_Kanalet'])
        except (KeyError, TypeError):
            self.ui.kanaletCheck.setChecked(True)
        
        # open bridge
        try:
            self.ui.bridgeCheck.setChecked(SETTINGS['Open_Bridge'])
        except (KeyError, TypeError):
            self.ui.bridgeCheck.setChecked(True)
        
        # open mamu
        try:
            self.ui.mazeCheck.setChecked(SETTINGS['Open_Mamu'])
        except (KeyError, TypeError):
            self.ui.mazeCheck.setChecked(True)
        
        # bad pets - companions follow inside dungeons
        try:
            self.ui.badPetsCheck.setChecked(SETTINGS['Bad_Pets'])
        except (KeyError, TypeError):
            self.ui.badPetsCheck.setChecked(False)

        # trapsanity
        try:
            self.ui.trapsCheck.setChecked(SETTINGS['Trapsanity'])
        except (KeyError, TypeError):
            self.ui.trapsCheck.setChecked(False)
        
        # color dungeon rupees
        try:
            self.ui.rupCheck.setChecked(SETTINGS['Blupsanity'])
        except(KeyError, TypeError):
            self.ui.rupCheck.setChecked(False)
        
        # classic d2
        try:
            self.ui.swampCheck.setChecked(SETTINGS['Classic_D2'])
        except (KeyError, TypeError):
            self.ui.swampCheck.setChecked(False)
        
        # owl statues
        try:
            self.ui.owlsComboBox.setCurrentIndex(OWLS_SETTINGS.index(SETTINGS['Owl_Statues'].lower().strip()))
        except (KeyError, TypeError, IndexError, ValueError):
            self.ui.owlsComboBox.setCurrentIndex(0)
        
        # # companions
        # try:
        #     self.ui.companionCheck.setChecked(SETTINGS['Shuffled_Companions'])
        # except (KeyError, TypeError):
        #     self.ui.companionCheck.setChecked(True)

        # # randomize entances
        # try:
        #     self.ui.loadingCheck.setChecked(SETTINGS['Randomize_Entrances'])
        # except (KeyError, TypeError):
        #     self.ui.loadingCheck.setChecked(False)

        # randomize music
        try:
            self.ui.musicCheck.setChecked(SETTINGS['Randomize_Music'])
        except (KeyError, TypeError):
            self.ui.musicCheck.setChecked(False)
        
        # randomize enemies
        try:
            self.ui.enemyCheck.setChecked(SETTINGS['Randomize_Enemies'])
        except (KeyError, TypeError):
            self.ui.enemyCheck.setChecked(False)
        
        # shuffled dungeons
        try:
            self.ui.dungeonsCheck.setChecked(SETTINGS['Shuffled_Dungeons'])
        except (KeyError, TypeError):
            self.ui.dungeonsCheck.setChecked(False)
        
        # spoiler log
        try:
            self.ui.spoilerCheck.setChecked(SETTINGS['Create_Spoiler'])
        except (KeyError, TypeError):
            self.ui.spoilerCheck.setChecked(True)
        
        # excluded checks
        try:
            for check in SETTINGS['Excluded_Locations']:
                if check in TOTAL_CHECKS:
                    self.excluded_checks.add(check)
        except (KeyError, TypeError):
            if not self.ui.chestsCheck.isChecked():
                self.excluded_checks.update(MISCELLANEOUS_CHESTS)
            if not self.ui.fishingCheck.isChecked():
                self.excluded_checks.update(FISHING_REWARDS)
            if not self.ui.rapidsCheck.isChecked():
                self.excluded_checks.update(RAPIDS_REWARDS)
            if not self.ui.dampeCheck.isChecked():
                self.excluded_checks.update(DAMPE_REWARDS)
            if not self.ui.giftsCheck.isChecked():
                self.excluded_checks.update(FREE_GIFT_LOCATIONS)
            if not self.ui.tradeGiftsCheck.isChecked():
                self.excluded_checks.update(TRADE_GIFT_LOCATIONS)
            if not self.ui.bossCheck.isChecked():
                self.excluded_checks.update(BOSS_LOCATIONS)
            if not self.ui.miscellaneousCheck.isChecked():
                self.excluded_checks.update(MISC_LOCATIONS)
            if not self.ui.heartsCheck.isChecked():
                self.excluded_checks.update(HEART_PIECE_LOCATIONS)
            if not self.ui.leavesCheck.isChecked():
                self.excluded_checks.update(LEAF_LOCATIONS)
            # if not self.ui.trendyCheck.isChecked():
            #     self.excluded_checks.update(TRENDY_REWARDS)
        
        # starting items
        try:
            for item in SETTINGS['Starting_Items']:
                if item in STARTING_ITEMS:
                    if self.starting_gear.count(item) < STARTING_ITEMS.count(item):
                        self.starting_gear.append(item)
        except (KeyError, TypeError):
            self.starting_gear = list() # reset starting gear to default if error


    
    # RomFS Folder Browse
    def romBrowse(self):
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folderpath != "":
            self.ui.lineEdit.setText(folderpath)
    
    
    
    # Output Folder Browse
    def outBrowse(self):
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folderpath != "":
            self.ui.lineEdit_2.setText(folderpath)
    
    
    
    # Generate New Seed
    def generateSeed(self):
        adj1 = random.choice(ADJECTIVES)
        adj2 = random.choice(ADJECTIVES)
        char = random.choice(CHARACTERS)
        self.ui.lineEdit_3.setText(adj1 + adj2 + char)
    
    
    
    # Chests Check Changed
    def chestsCheck_Clicked(self):
        if self.ui.chestsCheck.isChecked():
            self.excluded_checks.difference_update(MISCELLANEOUS_CHESTS)
        else:
            self.excluded_checks.update(MISCELLANEOUS_CHESTS)
    
    
    
    # Fishing Check Changed
    def fishingCheck_Clicked(self):
        if self.ui.fishingCheck.isChecked():
            self.excluded_checks.difference_update(FISHING_REWARDS)
        else:
            self.excluded_checks.update(FISHING_REWARDS)
    
    
    
    # Rapids Check Changed
    def rapidsCheck_Clicked(self):
        if self.ui.rapidsCheck.isChecked():
            self.excluded_checks.difference_update(RAPIDS_REWARDS)
        else:
            self.excluded_checks.update(RAPIDS_REWARDS)
    
    
    
    # Dampe Check Changed
    def dampeCheck_Clicked(self):
        if self.ui.dampeCheck.isChecked():
            self.excluded_checks.difference_update(DAMPE_REWARDS)
        else:
            self.excluded_checks.update(DAMPE_REWARDS)
    
    
    
    # # Trendy Check Changed
    # def trendyCheck_Clicked(self):
    #     if self.ui.trendyCheck.isChecked():
    #         self.excluded_checks.difference_update(TRENDY_REWARDS)
    #     else:
    #         self.excluded_checks.update(TRENDY_REWARDS)



    # Gifts Check Changed
    def giftsCheck_Clicked(self):
        if self.ui.giftsCheck.isChecked():
            self.excluded_checks.difference_update(FREE_GIFT_LOCATIONS)
        else:
            self.excluded_checks.update(FREE_GIFT_LOCATIONS)
    
    
    
    # Trade Quest Check Changed
    def tradeQuest_Clicked(self):
        if self.ui.tradeGiftsCheck.isChecked():
            self.excluded_checks.difference_update(TRADE_GIFT_LOCATIONS)
        else:
            self.excluded_checks.update(TRADE_GIFT_LOCATIONS)
    
    
    
    # Bosses Check Changed
    def bossCheck_Clicked(self):
        if self.ui.bossCheck.isChecked():
            self.excluded_checks.difference_update(BOSS_LOCATIONS)
        else:
            self.excluded_checks.update(BOSS_LOCATIONS)
    
    
    
    # Miscellaneous Standing Items Check Changed
    def miscellaneousCheck_Clicked(self):
        if self.ui.miscellaneousCheck.isChecked():
            self.excluded_checks.difference_update(MISC_LOCATIONS)
        else:
            self.excluded_checks.update(MISC_LOCATIONS)
    
    
    
    # Heart Pieces Check Changed
    def heartsCheck_Clicked(self):
        if self.ui.heartsCheck.isChecked():
            self.excluded_checks.difference_update(HEART_PIECE_LOCATIONS)
        else:
            self.excluded_checks.update(HEART_PIECE_LOCATIONS)
    


    def leavesCheck_Clicked(self):
        if self.ui.leavesCheck.isChecked():
            self.excluded_checks.difference_update(LEAF_LOCATIONS)
        else:
            self.excluded_checks.update(LEAF_LOCATIONS)
    


    def rupCheck_Clicked(self):
        self.excluded_checks.difference_update(BLUE_RUPEES) # regardless of if it's checked or not, reset blue rupees
    


    # Update Number of Max Seashells
    def updateSeashells(self):
        value = self.ui.seashellsComboBox.currentIndex()
        
        if value == 0:
            self.excluded_checks.update(SEASHELL_REWARDS)
        elif value == 1:
            self.excluded_checks.difference_update(SEASHELL_REWARDS)
            self.excluded_checks.update(['15-seashell-reward', '30-seashell-reward', '40-seashell-reward', '50-seashell-reward'])
        elif value == 2:
            self.excluded_checks.difference_update(SEASHELL_REWARDS)
            self.excluded_checks.update(['30-seashell-reward', '40-seashell-reward', '50-seashell-reward'])
        elif value == 3:
            self.excluded_checks.difference_update(SEASHELL_REWARDS)
            self.excluded_checks.update(['40-seashell-reward', '50-seashell-reward'])
        elif value == 4:
            self.excluded_checks.difference_update(SEASHELL_REWARDS)
            self.excluded_checks.update(['50-seashell-reward'])
        else:
            self.excluded_checks.difference_update(SEASHELL_REWARDS)
    


    # Update which owls show up in the locations tab
    def updateOwls(self):
        value = self.ui.owlsComboBox.currentIndex()

        if value == 0:
            self.overworld_owls = False
            self.excluded_checks.difference_update(OVERWORLD_OWLS)
            self.dungeon_owls = False
            self.excluded_checks.difference_update(DUNGEON_OWLS)
        elif value == 1:
            self.overworld_owls = True
            self.dungeon_owls = False
            self.excluded_checks.difference_update(DUNGEON_OWLS)
        elif value == 2:
            self.overworld_owls = False
            self.excluded_checks.difference_update(OVERWORLD_OWLS)
            self.dungeon_owls = True
        else:
            self.overworld_owls = True
            self.dungeon_owls = True



    # Randomize Button Clicked
    def randomizeButton_Clicked(self):
        
        if os.path.exists(self.ui.lineEdit.text()) and os.path.exists(self.ui.lineEdit_2.text()):
            
            # get needed params
            rom_path = self.ui.lineEdit.text()
            
            seed = self.ui.lineEdit_3.text()
            if seed.lower().strip() in ("", "random"):
                random.seed()
                seed = str(random.getrandbits(32))
            
            outdir = f"{self.ui.lineEdit_2.text()}/{seed}"
            
            logic = LOGIC_PRESETS[self.ui.tricksComboBox.currentIndex()]

            settings = {
                'create-spoiler': self.ui.spoilerCheck.isChecked(),
                'free-book': self.ui.bookCheck.isChecked(),
                'unlocked-bombs': self.ui.unlockedBombsCheck.isChecked(),
                'shuffle-bombs': self.ui.shuffledBombsCheck.isChecked(),
                'shuffle-powder': self.ui.shuffledPowderCheck.isChecked(),
                'reduce-farming': self.ui.farmingCheck.isChecked(),
                'fast-fishing': self.ui.fastFishingCheck.isChecked(),
                'fast-stealing': self.ui.stealingCheck.isChecked(),
                'fast-trendy': self.ui.fastTrendyCheck.isChecked(),
                'fast-songs': self.ui.songsCheck.isChecked(),
                'shuffle-instruments': self.ui.instrumentCheck.isChecked(),
                'starting-instruments': self.ui.instrumentsComboBox.currentIndex(),
                'bad-pets': self.ui.badPetsCheck.isChecked(),
                'open-kanalet': self.ui.kanaletCheck.isChecked(),
                'open-bridge': self.ui.bridgeCheck.isChecked(),
                'open-mamu': self.ui.mazeCheck.isChecked(),
                'trap-sanity': self.ui.trapsCheck.isChecked(),
                'blup-sanity': self.ui.rupCheck.isChecked(),
                'classic-d2': self.ui.swampCheck.isChecked(),
                'owl-overworld-gifts': True if OWLS_SETTINGS[self.ui.owlsComboBox.currentIndex()] in ('overworld', 'all') else False,
                'owl-dungeon-gifts': True if OWLS_SETTINGS[self.ui.owlsComboBox.currentIndex()] in ('dungeons', 'all') else False,
                # 'owl-hints': True if OWLS_SETTINGS[self.ui.owlsComboBox.currentIndex()] in ['hints', 'hybrid'] else False,
                'fast-master-stalfos': self.ui.fastMSCheck.isChecked(),
                'scaled-chest-sizes': self.ui.chestSizesCheck.isChecked(),
                'seashells-important': True if len([s for s in SEASHELL_REWARDS if s not in self.excluded_checks]) > 0 else False,
                'trade-important': True if len([t for t in TRADE_GIFT_LOCATIONS if t not in self.excluded_checks]) > 0 else False,
                # 'shuffle-companions': self.ui.companionCheck.isChecked(),
                # 'randomize-entrances': self.ui.loadingCheck.isChecked(),
                'randomize-music': self.ui.musicCheck.isChecked(),
                'randomize-enemies': self.ui.enemyCheck.isChecked(),
                'panel-enemies': True if len([s for s in DAMPE_REWARDS if s not in self.excluded_checks]) > 0 else False,
                'shuffled-dungeons': self.ui.dungeonsCheck.isChecked(),
                'starting-items': self.starting_gear,
                'excluded-locations': self.excluded_checks
            }
            
            self.progress_window = ProgressWindow(rom_path, outdir, seed, logic, ITEM_DEFS, LOGIC_DEFS, settings)
            self.progress_window.setFixedSize(472, 125)
            self.progress_window.setWindowTitle(f"{seed}")

            if self.mode == 'light':
                self.progress_window.setStyleSheet(LIGHT_STYLESHEET)
            else:
                self.progress_window.setStyleSheet(DARK_STYLESHEET)
            
            self.progress_window.show()
    
    
    
    # Tab changed
    def tab_Changed(self):

        # starting items
        if self.ui.tabWidget.currentIndex() == 1:
            randomized_gear = STARTING_ITEMS[:]
            for x in self.starting_gear:
                randomized_gear.remove(x)
            
            self.ui.listWidget_5.clear()
            for item in randomized_gear:
                self.ui.listWidget_5.addItem(self.checkToList(str(item)))
            
            self.ui.listWidget_6.clear()
            for item in self.starting_gear:
                self.ui.listWidget_6.addItem(self.checkToList(str(item)))
            
            return
        
        # locations
        if self.ui.tabWidget.currentIndex() == 2:
            self.ui.listWidget.clear()
            for check in TOTAL_CHECKS.difference(self.excluded_checks):
                if check in DUNGEON_OWLS and not self.dungeon_owls:
                    continue
                if check in OVERWORLD_OWLS and not self.overworld_owls:
                    continue
                if check in BLUE_RUPEES and not self.ui.rupCheck.isChecked():
                    continue
                self.ui.listWidget.addItem(NumericalListWidget(self.checkToList(str(check))))
            
            self.ui.listWidget_2.clear()
            for check in self.excluded_checks:
                if check in DUNGEON_OWLS and not self.dungeon_owls:
                    continue
                if check in OVERWORLD_OWLS and not self.overworld_owls:
                    continue
                if check in BLUE_RUPEES and not self.ui.rupCheck.isChecked():
                    continue
                self.ui.listWidget_2.addItem(NumericalListWidget(self.checkToList(str(check))))
            
            return
        
        # logic tricks
        if self.ui.tabWidget.currentIndex() == 3:
            return
    
    
    
    # Locations Include Button Clicked
    def includeButton_Clicked(self):
        for i in self.ui.listWidget_2.selectedItems():
            self.ui.listWidget_2.takeItem(self.ui.listWidget_2.row(i))
            self.excluded_checks.remove(self.listToCheck(i.text()))
            self.ui.listWidget.addItem(NumericalListWidget(i.text()))
    
    
    
    # Locations Exclude Button Clicked
    def excludeButton_Clicked(self):
        for i in self.ui.listWidget.selectedItems():
            self.ui.listWidget.takeItem(self.ui.listWidget.row(i))
            self.ui.listWidget_2.addItem(NumericalListWidget(i.text()))
            self.excluded_checks.add(self.listToCheck(i.text()))
    
    
    
    # Starting Items Include Button Clicked - 'including' is moving starting items into the randomized pool
    def includeButton_3_Clicked(self):
        for i in self.ui.listWidget_6.selectedItems():
            self.ui.listWidget_6.takeItem(self.ui.listWidget_6.row(i))
            self.starting_gear.remove(self.listToItem(i.text()))
            self.ui.listWidget_5.addItem(i.text())



    # Starting Items Exclude Button Clicked - 'excluding' is moving randomized items into starting items
    def excludeButton_3_Clicked(self):
        for i in self.ui.listWidget_5.selectedItems():
            self.ui.listWidget_5.takeItem(self.ui.listWidget_5.row(i))
            self.ui.listWidget_6.addItem(i.text())
            self.starting_gear.append(self.listToItem(i.text()))



    # some-check to Some Check
    def checkToList(self, check):
        s = sub("-", " ", check).title()
        return s
    
    
    
    # Some Check to some-check
    def listToCheck(self, check):
        stayUpper = ('d0', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8')
        
        s = sub(" ", "-", check).lower()
        
        if s.startswith(stayUpper):
            s = s.replace('d', 'D', 1)
        
        return s
    


    # Starting Item to starting-item and also converts names that were changed to look nicer
    def listToItem(self, item):
        s = sub(" ", "-", item).lower()
        
        return s
    


    # Sets the app to Light Mode
    def setLightMode(self):
        self.mode = str('light')
        self.setStyleSheet(LIGHT_STYLESHEET)
        if self.ui.explainationLabel.text() == 'Hover over an option to see what it does':
            self.ui.explainationLabel.setStyleSheet('color: rgb(80, 80, 80);')
        else:
            self.ui.explainationLabel.setStyleSheet('color: black;')
    


    # Sets the app to Dark Mode
    def setDarkMode(self):
        self.mode = str('dark')
        self.setStyleSheet(DARK_STYLESHEET)
        if self.ui.explainationLabel.text() == 'Hover over an option to see what it does':
            self.ui.explainationLabel.setStyleSheet('color: rgb(175, 175, 175);')
        else:
            self.ui.explainationLabel.setStyleSheet('color: white;')
    


    # Display new window listing the new features and bug fixes
    def showChangelog(self):
        message = QtWidgets.QMessageBox()
        message.setWindowTitle("What's New")
        message.setText(CHANGE_LOG)

        if self.mode == 'light':
            message.setStyleSheet(LIGHT_STYLESHEET)
        else:
            message.setStyleSheet(DARK_STYLESHEET)
        
        message.exec()
    


    # Display new window listing the currently known issues
    def showIssues(self):
        message = QtWidgets.QMessageBox()
        message.setWindowTitle("Known Issues")
        message.setText(KNOWN_ISSUES)

        if self.mode == 'light':
            message.setStyleSheet(LIGHT_STYLESHEET)
        else:
            message.setStyleSheet(DARK_STYLESHEET)
        
        message.exec()
    


    # Override mouse click event to make certain stuff lose focus
    def mousePressEvent(self, event):
        focused_widget = self.focusWidget()
        if isinstance(focused_widget, QtWidgets.QLineEdit):
            focused_widget.clearFocus()
    


    # Override close event to save settings
    def closeEvent(self, event):
        self.saveSettings()
        event.accept()



# Create custom QListWidgetItem to sort locations alphanumerically
class NumericalListWidget(QtWidgets.QListWidgetItem):
    def __lt__(self, other):
        locations = [self.text(), other.text()]
        locations.sort()

        try:
            nums_a = []
            for c in self.text():
                if c.isdigit():
                    nums_a.append(c)
            if self.text()[0] == 'D':
                del nums_a[0]
            
            nums_b = []
            for c in other.text():
                if c.isdigit():
                    nums_b.append(c)
            if other.text()[0] == 'D':
                del nums_b[0]
            
            if len(nums_a) < 1 and len(nums_b) < 1:
                if self.text() == locations[0]:
                    return True
                else:
                    return False
            
            a = int("".join(nums_a))
            b = int("".join(nums_b))
            
            if (self.text()[0] == 'D') and (other.text()[0] == 'D'):
                if not len(nums_a) == len(nums_b):
                    return len(nums_a) < len(nums_b)
            
            if (self.text()[0] == 'D') or (other.text()[0] == 'D'):
                if self.text() == locations[0]:
                    return True
                else:
                    return False
                        
            return a < b
        
        except (IndexError, TypeError, ValueError):
            if self.text() == locations[0]:
                return True
            else:
                return False
