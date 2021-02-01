from fltk import *
import random, math, pygame
import sqlite3 as sq
from datetime import *


class database(object):
    def __init__(self, file):
        self.connection = sq.connect(file)
        self.cursor = self.connection.cursor()
    def delete(self):#personal use only
        self.cursor.execute("DELETE FROM highscores")
    def create(self):#only called if their is a problem with database
        self.cursor.execute("CREATE TABLE highscores (name VARCHAR(20), score INTEGER, time DATETIME);")
    def fetch(self):
        '''selects all rows in the highscores table in the database and returns it'''
        try:
            self.cursor.execute("""SELECT * FROM highscores;""")
        except sq.OperationalError:
            self.create()
        return(self.cursor.fetchall())
    def add(self, data):
        '''adds data arguement to database'''
        script = """INSERT INTO highscores(name, score, time) VALUES (?, ?, ?);"""
        self.cursor.execute(script, data)


class box(Fl_Box):
    def __init__(self, x, y, w, h, label='', color=49, tooltip='', labelsize=14):
        super().__init__(x, y, w, h)
        self.label(label)
        self.labelsize(labelsize)
        self.color(color)
        self.tooltip(tooltip)
       

class button(Fl_Button):
    def __init__(self, x, y, w, h, color, callback, shortcut=None, tooltip=None, label=None, args=''):
        '''basic button creation class to avoid extra lines such as but.shortcut but.tooltip but.label'''
        super().__init__(x, y, w, h, label)
        if args != '':
            self.callback(callback, args)
        else:
            self.callback(callback)
        self.shortcut(shortcut)
        self.tooltip(tooltip)
        self.color(color)


class audiobutton(button, Fl_Button):
    '''child class of button class with added audio support (for the colored buttons)
    audio arguement is the file that will be played when you click the button by the handle method'''
    def __init__(self, x, y, w, h, color, callback, audio, shortcut=None, tooltip=None, label=None, args=''):
        super().__init__(x, y, w, h, color, callback, shortcut, tooltip, label, args)
        self.audio = audio
    def handle(self, event):
        ev = Fl_Button.handle(self, event)
        if event == FL_PUSH:
            if not memory_game.flashing:
                self.audio.play()
            return 1
        elif event == FL_RELEASE:
            pygame.mixer.stop()
            return 1
        else:
            return ev
    

class game(Fl_Double_Window):
    def __init__(self):
        #database
        self.db = database('highscore.db')
        self.highscore = {}#highscore is the content inside highscore.db but in the form of a dictionary
        for score in self.db.fetch():
            self.highscore[score[0]] = (score[1], score[2])#loading data from database and parsing into dictionary

        super().__init__(int(Fl.w()/2)-(660//2),int(Fl.h()/2)-(660//2),660,660,'Simon Says')
        
        self.gamesettings = [[0.5,7.5],[0.25,5.0],[0.1,2.5]]#difficulty: easy 1 sec medium 0.5 sec hard 0.2 sec delay (makes the buttons flash faster the higher difficulty)
        self.butcolors = [FL_RED, FL_BLUE, FL_GREEN, FL_YELLOW]
        self.round = 1
        self.totclicks = 0
        self.flashing = False#used to prevent button clicks while sequence is flashing

        self.but_audio = [pygame.mixer.Sound('red.ogg'), pygame.mixer.Sound('blue.ogg'), pygame.mixer.Sound('green.ogg'), pygame.mixer.Sound('yellow.ogg')]#5 sec
        self.flashaudio = [pygame.mixer.Sound('redflash.ogg'), pygame.mixer.Sound('blueflash.ogg'), pygame.mixer.Sound('greenflash.ogg'), pygame.mixer.Sound('yellowflash.ogg')]#0.5 sec
        self.loseaudio = pygame.mixer.Sound('lose.ogg')
  
        self.begin()
        self.create_buttons()
        self.difchoice = Fl_Choice(280,50,100,50)
        self.difchoice.add('Easy', FL_F + 1, self.difficulty, 1)
        self.difchoice.add('Medium', FL_F + 2, self.difficulty, 2)
        self.difchoice.add('Hard', FL_F + 3, self.difficulty, 3)
        self.difchoice.value(1)
        self.startbut = button(280, 110, 50, 50, FL_BACKGROUND_COLOR, self.startgame, shortcut=FL_ENTER, tooltip='Click to Start the Game', label='Start')
        self.resetbut = button(335, 110, 50, 50, FL_BACKGROUND_COLOR, self.reset, shortcut=ord('n'), tooltip='Click to Reset the Game', label='Reset')
        self.rounddisplay = box(560, 10, 100, 25, label='Round: 1')
        self.hscoredisplay = box(25, 10, 100, 25, labelsize=12)
        self.title = box(280,0,100,50,label='Simon Says', labelsize=24)
        self.allscores = Fl_Browser(0,self.h()-100,self.w(),100)
        self.end()

        self.reset()

        self.allscores.label('All Scores')
        self.allscores.align(FL_ALIGN_TOP)

        self.resizable(self)

    def reset(self, wid=None):
        '''method used to reset the game by setting variables to their original values and deactivating/activating neccessary buttons'''
        Fl_remove_timeout(self.lose)
        Fl_remove_timeout(self.flashwid)
        self.but_order = []
        self.check = []
        self.start = False
        self.totclicks = 0

        #sets default colors of all buttons
        for but in self.buttons:
            but.color(self.butcolors[list(self.buttons.keys()).index(but)]) 
            but.redraw()

        for but in self.buttons.keys():
            but.deactivate()

        self.resetbut.deactivate()
        self.startbut.activate()
        self.difchoice.activate()

        self.allscores.show()
        self.allscores.clear()
        self.allscores.textfont(FL_COURIER_BOLD)

        for item in self.sort(self.highscore).items():
            self.allscores.add(f'{str(item[0][:16])}:{" " * (16-len(str(item[0][:16])))} Score {str(item[1][0])}{" " * (5-len(str(item[1][0])))} Date Achieved {str(item[1][1])}')#long syntax and use of multiplying strings is required to create a uniform monospaced browser
        if len(self.highscore) > 0:
            self.hscoredisplay.label(f'Highest Score: \n{list(self.sort(self.highscore).keys())[0]} : {list(self.sort(self.highscore).values())[0][0]}')
            self.hscoredisplay.redraw()
        self.rounddisplay.label('Round: 1')

    def sort(self, inp):
        '''used to sort dictionaries by values
        inp is the unsorted dictionary passed in and this method returns the sorted dictionary'''
        keys = list(inp.keys())
        values = list(inp.values())
        sortedvals = sorted(values, reverse=True)
        sortedinp = {}
        for x in range(len(values)):#transfers sorted values and their respective key to sortedinp
            sortedinp[keys[values.index(sortedvals[x])]] = sortedvals[x]
            keys.pop(values.index(sortedvals[x]))
            values.pop(values.index(sortedvals[x]))
        return(sortedinp)
            
    def difficulty(self, wid, difficulty):
        '''used to set game difficulty using the difficulty arguement passed in by the fl_choice'''
        self.difficulty = difficulty

    def startgame(self, wid):
        '''creates and starts sequence as well as activates/deactivates all neccessary buttons'''
        self.but_order = self.randomize()
        self.start = True
        wid.deactivate()
        self.difchoice.deactivate()
        self.speed = self.gamesettings[self.difchoice.value()][0]
        self.time_limit = self.gamesettings[self.difchoice.value()][1]
        self.cue_flash()
        for but in self.buttons.keys():
            but.activate()
        self.resetbut.activate()
        self.allscores.hide()

    def randomize(self):
        '''returns a random number'''
        self.but_order.append(random.randrange(1, len(list(self.buttons.keys()))+1))
        return(self.but_order)

    def create_buttons(self):
        '''creates buttons with respective positions, colors, and audio'''
        self.buttons = {}
        count = 1
        for x in range(2):
            for i in range(2):
                self.buttons[audiobutton(155+x*200,170+i*200,150,150,self.butcolors[count-1], self.but_cb, self.but_audio[count-1])] = count
                count += 1
    def but_cb(self, wid):
        '''method used when a colored button is clicked'''
        if self.start and not self.flashing:
            if self.buttons[wid] != self.but_order[len(self.check)]:
                self.lose()
            else:
                Fl_remove_timeout(self.lose)
                self.totclicks += 1
                self.check.append(self.buttons[wid])#correctly clicked buttons are added
                if self.check == self.but_order:
                    self.round += 1
                    self.but_order = self.randomize()
                    self.cue_flash()
                    self.check = []
                    self.rounddisplay.label(f'Round: {str(len(self.but_order))}')
                else:
                    Fl.repeat_timeout(self.time_limit, self.lose)

    
    def lose(self):
        '''only runs when you click incorrect button, not when you reset
        main function of this method is to save high scores to the database'''
        Fl_remove_timeout(self.flashwid)
        Fl_remove_timeout(self.lose)

        if self.start:
            self.start = False
            pygame.mixer.stop()
            self.loseaudio.play()

             #resets all buttons to prevent a button being in the down state after 5 secs
            for but in self.buttons: 
                but.handle(FL_RELEASE) 
                but.redraw()
            
            #high score
            if len(self.highscore) == 0 or self.totclicks > list(self.sort(self.highscore).values())[0][0]:
                fl_message(f'NEW HIGH SCORE\nYou Made It To Round {len(self.but_order)-1} and {self.totclicks} Total Clicks!')
            else:
                fl_message(f'You Made It To Round {len(self.but_order)-1} and {self.totclicks} Total Clicks!')

            #save score
            if fl_ask('Do You Want to Save Your Score?'):
                name = fl_input('Enter Your Name: ')
                if name != None:
                    if name not in list(self.highscore.keys()):
                        self.highscore[name] = (self.totclicks, str(datetime.now()).split('.')[0])
                        self.db.add((name, self.totclicks, str(datetime.now()).split('.')[0]))
                    else:
                        if self.highscore[name][0] > self.totclicks:#if name entered already exists and is higher than current score
                            fl_alert('You Have Already Registered a Higher Score Before')
                        else:
                            self.highscore[name] = (self.totclicks,str(datetime.now()).split('.')[0])
                            self.db.add((name, self.totclicks,str(datetime.now()).split('.')[0]))
        
            self.reset()

    #flashing
    def cue_flash(self):
        '''starts the flash sequence of the buttons'''
        self.flashing = True
        Fl.add_timeout(1+((self.speed*2)*(len(self.but_order))), self.enableclick)
        for x in range(len(self.but_order)):
            for but in self.buttons.keys():
                if self.buttons[but] == self.but_order[x]:
                    Fl.add_timeout(1+(self.speed*2)*x, self.flashwid, but)    

                    
    def enableclick(self):
        self.flashing = False
        Fl_add_timeout(self.time_limit, self.lose)#if player doesn't click for 5 seconds

    def flashwid(self, wid):
        if wid.color() != FL_BACKGROUND_COLOR:
            pygame.mixer.stop()
            self.flashaudio[list(self.buttons.keys()).index(wid)].play()
            self.originalcolor = wid.color()
            wid.color(FL_BACKGROUND_COLOR)
            wid.redraw()
        else:
            wid.color(self.originalcolor)
            wid.redraw()
            return
        Fl_repeat_timeout(self.speed, self.flashwid, wid)


if __name__ == "__main__":
    pygame.mixer.init()
    memory_game = game()
    memory_game.show()
    Fl.run()
    memory_game.db.connection.commit()
    memory_game.db.connection.close()