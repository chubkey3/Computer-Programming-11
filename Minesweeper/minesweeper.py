from fltk import *
import sqlite3 as sq
import math, random, datetime, sys


class database(object):
    def __init__(self, file):
        '''class functions as a way to save/query from a database file inputed using the arugement file'''
        self.connection = sq.connect(file)
        self.cursor = self.connection.cursor()
    def delete(self, name):
        '''deletes score tuple containing the name arguement from the database'''
        self.cursor.execute(f"DELETE FROM highscores WHERE name=?", (str(name),))
    def create(self):
        '''only called if their is a problem with database'''
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
        try:
            self.cursor.execute(script, data)
        except sq.OperationalError:
            self.create()
            self.cursor.execute(script, data)
    def __del__(self):
        self.connection.commit()
        self.connection.close()


class button(Fl_Button):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.x = x//w#x pos inside of grid matrix
        self.y = y//h#y pos inside of grid matrix
        self.flagged = False
        self.flag_img = Fl_PNG_Image('flag.png').copy(w, h)


class tile(button):
    def __init__(self, x, y, w, h, callback):
        super().__init__(x, y, w, h)
        self.value = 0#the # of adjacent mines
        self.x_img = Fl_PNG_Image('x.png').copy(w, h)
        self.callback = callback
        self.labelsize(20)
        self.revealed = False

    def show(self):
        '''used by recursion method in the main class to reveal the value on the button'''
        self.revealed = True
         
        if self.value == 0:
            self.deactivate()
        else:
            self.label(str(self.value))

        #displays red x at the end if you flag (because this is not a mine)
        if self.flagged:
            self.label(None)
            self.image(self.x_img)

    def handle(self, event):
        ev = super().handle(event)

        if event == FL_RELEASE:
            if Fl.event_button() == FL_LEFT_MOUSE and not self.flagged:
                self.callback(self)#pass in self to get cords later
                return 1
            if Fl.event_button() == FL_MIDDLE_MOUSE and self.value > 0 and self.revealed:
                flags = 0# is number of adjacent flags
                for x2 in range(-1,2):
                    for y2 in range(-1,2):
                        if self.x+x2 < len(game.grid) and self.y+y2 < len(game.grid) and game.grid[self.x+x2][self.y+y2].flagged == True:#self.x or self.y is the buttons pos in the grid and x2 and y2 essentially iterates through the indices around it
                            flags += 1
                if flags == self.value:
                    for x2 in range(-1,2):
                        for y2 in range(-1,2):
                            if self.x+x2 < len(game.grid) and self.y+y2 < len(game.grid) and game.grid[self.x+x2][self.y+y2].flagged != True:#if the adjacent tile is in the grid and isn't flagged (x2 and y2 iterate through adjacent tiles)
                                if game.grid[self.x+x2][self.y+y2].boxtype() == 'mine':
                                    game.lose()
                                    break
                                else:
                                    game.grid[self.x+x2][self.y+y2].show()
                                    
            if Fl.event_button() == FL_RIGHT_MOUSE and game.start:
                if game.flags < game.mines and self.revealed == False:
                    self.flagged = not self.flagged
                    if self.flagged:
                        self.image(self.flag_img)
                        game.flags += 1
                    else:
                        self.image(None)
                        game.flags -= 1

                elif game.flags == game.mines: 
                    if self.flagged:#only decrease flags when at max and not add
                        self.flagged = False
                        self.image(None)
                        game.flags -= 1 
                 
                game.mine_display.label(f'{game.flags}/{game.mines} Mines')
                return 1

        return ev

    def boxtype(self):
        '''used to indentify type of button'''
        return 'tile'
    

class mine(button):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.mine_img = Fl_PNG_Image('mine.png').copy(w, h)

    def show(self):
        '''used to reveal mines upon losing/winning'''
        self.image(self.mine_img)
        if self.flagged:
            self.color(FL_GREEN)
        else:
            self.color(FL_RED)
        self.redraw()

    def handle(self, event):
        ev = super().handle(event)
        if event == FL_RELEASE:
            if Fl.event_button() == FL_LEFT_MOUSE and not self.flagged:
                game.lose()
            if Fl.event_button() == FL_RIGHT_MOUSE and (self.color() != FL_GREEN and self.color() != FL_RED) and game.start:#makes sure but isn't green/red cause that means it's revealed(the user already clicked a mine)

                if game.flags < game.mines:
                    self.flagged = not self.flagged
                    if self.flagged:
                        self.image(self.flag_img)
                        game.flags += 1
                    else:
                        self.image(None)
                        game.flags -= 1

                elif game.flags == game.mines: 
                    if self.flagged:
                        self.flagged = False
                        self.image(None)
                        game.flags -= 1      
                        
                game.mine_display.label(f'{game.flags}/{game.mines} Mines')
                return 1
        return ev

    def boxtype(self):
        '''used to indentify type of button'''
        return 'mine'


class minesweeper(Fl_Double_Window):
    def __init__(self, difficulty=1):
        #database
        self.db = database('highscore.db')
        
        #window
        super().__init__(Fl.w()//2-250,Fl.h()//2-263,500,575,'Minesweeper')
        self.icon(Fl_PNG_Image("icon.png"))

        self.difficulties = [[64,5],[100,10],[400,50],[1444,100],[1600,200]]#1st item in each list = # total tiles 2nd item in each list = # mines
        self.difficulty = difficulty
        self.tiles = self.difficulties[self.difficulty][0]
        self.mines = self.difficulties[self.difficulty][1]

        self.grid = []#2d list storing all mines and non-mines
        self.flags = 0
        self.start = False
        self.mine_locations = []
        self.time = 0
        self.butsize = math.ceil(self.w()//math.sqrt(self.tiles))
        
        #highscore
        self.highscorelabel = self.highestscore()
    
        self.begin()

        #board
        self.create_mines()
        self.create_grid()
        
        #game displays
        self.mine_display = Fl_Box(50,self.h()-75,100,75)
        self.highscore_display = Fl_Box(200,self.h()-75,100,30)
        self.time_display = Fl_Box(350,self.h()-75,100,75)
        self.difficulty_display = Fl_Choice(200,self.h()-45,100,20)#select grid size using choice menu located above the play button
        self.play_but = Fl_Button(200, self.h()-20,100,20)#loads the grid with selected grid size

        self.end()

        #difficulty choice
        self.difficulty_display.add('Easy',FL_F + 1, self.change_dif, 0)
        self.difficulty_display.add('Normal',FL_F + 2, self.change_dif, 1)
        self.difficulty_display.add('Hard',FL_F + 3, self.change_dif, 2)
        self.difficulty_display.add('Extreme',FL_F + 4, self.change_dif, 3)
        self.difficulty_display.add('Good Luck!',FL_F + 5, self.change_dif, 4)
        self.difficulty_display.value(self.difficulty)

        #labels
        self.mine_display.label(f'{self.flags}/{self.mines} Mines')

        self.highscore_display.label(self.highscorelabel)

        self.time_display.label(f'Time: {self.time}')
        
        self.play_but.label('Load')
        self.play_but.tooltip('Loads new game with specified grid and mine count')
        
        self.play_but.callback(self.reset)

        self.resizable(self)
    
    def draw(self):
        '''change labels to adapt to screen size'''
        for x in range(len(self.grid)):
            for y in range(len(self.grid)):
                self.grid[x][y].labelsize(self.w()//len(self.grid)//2)
        super().draw()

    def create_mines(self):
        row = []
        self.mine_locations = []#indices inside of self.grid to be replaced with mines
        for n in range(self.mines):
            randint = (random.randrange(0,math.sqrt(self.tiles)),random.randrange(0,math.sqrt(self.tiles)))#indice inside of grid matrix

            while randint in self.mine_locations:#keep creating new position until it is unique
                randint = (random.randrange(0,math.sqrt(self.tiles)),random.randrange(0,math.sqrt(self.tiles)))
                
            self.mine_locations.append(randint)

    def create_grid(self):
        row = []
        for x in range(int(math.sqrt(self.tiles))):
            for y in range(int(math.sqrt(self.tiles))):
                if (x,y) in self.mine_locations:
                    row.append(mine(x*self.butsize,y*self.butsize,self.butsize,self.butsize))#change 
                else:
                    row.append(tile(x*self.butsize,y*self.butsize,self.butsize,self.butsize,self.but_cb,))#change 
                
            self.grid.append(row)
            row = []
       
       #gives # of adjacent mines to all non-mine buttons
        for x in range(len(self.grid)):
            for y in range(len(self.grid)):
                if self.grid[x][y].boxtype() == 'mine':
                    for x2 in range(-1, 2):
                        for y2 in range(-1, 2):
                            #x and y are the button's pos and x2 and y2 are added to the x and y to get the 8 tiles around it
                            if not(x+x2 > len(self.grid)-1 or x+x2 < 0 or y+y2 > len(self.grid)-1 or y+y2 < 0 or (x2 == 0 and y2 == 0) or self.grid[x+x2][y+y2].boxtype() == 'mine'):#if the adjacent tile is inside of the board, isn't the original tile, and isn't a mine
                                self.grid[x+x2][y+y2].value += 1       
        
    def timer(self):
        '''displays time while playing game'''
        self.time += 1
        self.time_display.label(f'Time: {self.time}')
        Fl_repeat_timeout(1.0, self.timer)


    def but_cb(self, wid):
        '''starts the game if not already started and runs recursion based on the inputed pos arguement'''
        if not self.start:
            self.start = True
            Fl_add_timeout(1.0, self.timer)
            self.difficulty_display.deactivate()
            self.play_but.deactivate()

        self.reveal((wid.x,wid.y))#wid.x/wid.y = clicked button's position

    def reveal(self, n):
        '''
        this is the recursive search method
        recurssion works by checking if the button on cords of arguement n is a mine or out of bonds
        base case is button is mine or not in grid and then stops calling itself
        if it isn't a mine or out of bonds, it runs the same function but to the 8 adjacent buttons to it until they all are mines/out of the grid
        '''
        box = self.grid[n[0]][n[1]]#gets button instance
        if box.boxtype() != 'mine' and box.revealed == False and box.flagged == False:
            box.show()
            box.revealed = True

            self.checkwin()

            #run same functions to the 8 tiles beside it
            for x in range(-1,2):
                for y in range(-1,2):
                    if not(n[0]+x < 0 or n[1]+y < 0 or n[0]+x > len(self.grid)-1 or n[1]+y > len(self.grid)-1 or (x == 0 and y == 0)) and box.value == 0:#if the adjacent tile is inside of the board, isn't the original tile, and isn't a mine or next to a mine
                        self.reveal((n[0]+x,n[1]+y))
                           
    def checkwin(self):
        '''checks if all non-mines are revealed and runs win method if they are'''
        for x in range(int(math.sqrt(self.tiles))):
            for y in self.grid[x]:
                if y.boxtype() == 'mine':#skip over mines
                    continue
                elif y.revealed == False:#if there is any unrevealed tiles, it doesn't trigger a win
                    return
        self.win()#if all tiles are revealed

    def win(self):
        '''method called when player reveals all neccessary non-mines without clicking on a mine
        stops timer and gives user an option to save their highscore'''
        Fl_remove_timeout(self.timer)
        self.difficulty_display.activate()
        self.play_but.activate()
        
        for x in range(len(self.grid)):
            for y in range(len(self.grid)):
                self.grid[x][y].show()
        
        #highscore
        if self.time < self.highscore:
            fl_message(f'HIGHSCORE!\nYou Finished a {self.tiles} Tile and {self.mines} Mine Game in {self.time} Seconds!')
            name = fl_input('Enter Your Name')
            if name != None:
                #if their name already exists, delete it
                for scorename in self.db.fetch():
                    if scorename[0] == str(name):
                        self.db.delete(scorename[0])
                self.db.add((name, self.time, str(datetime.datetime.now())))

        else:
            fl_message(f'Nice Work! Sadly You Spent {self.time-self.highscore} Extra Second(s) Solving Than the High Score. Obtain a Lower Time Than {self.highscore} Seconds to Save Your Score!☺\nIf You Want to Play Again, Choose Your Difficulty and Press Load.')

    def lose(self):
        '''method called when player clicks on a mine before revealing every non-mine'''
        Fl_remove_timeout(self.timer)
        self.difficulty_display.activate()
        self.play_but.activate()
        for x in range(len(self.grid)):
            for y in range(len(self.grid)):
                self.grid[x][y].show()

    def reset(self, wid):
        '''deletes all widgets and calls the init method with a different difficulty'''
        Fl_remove_timeout(self.timer)
        for x in range(len(self.grid)):
            for y in range(len(self.grid)):
                Fl_delete_widget(self.grid[x][y])
        Fl_delete_widget(self.time_display)
        Fl_delete_widget(self.highscore_display)
        Fl_delete_widget(self.mine_display)
        self.resize(Fl.w()//2-250,Fl.h()//2-263,500,575)#fixes bug when reloading a game with fullscreen by reseting win dimensions to original
        self.__init__(self.difficulty)

    def change_dif(self, wid, dif):
        '''called by difficulty_display to change difficulty to dif aruguement'''
        self.difficulty = dif

    def highestscore(self):
        '''
        sets label of highscore
        returns nothing if the database is empty (e.g. anything will be a highscore)
        returns highest score tuple (containing name, score, and data achieved) if database is not empty
        '''
        databaseinfo = self.db.fetch()
        highestscore = (None, 10000)#10000 is just a large number to be replaced
        if len(databaseinfo) > 0:
            for x in databaseinfo:
                if x[1] < highestscore[1]:
                    highestscore = x
            self.highscore = highestscore[1]#store a global copy to check later in the win function
            return(f'Highscore\n{highestscore[0]} : {highestscore[1]} Seconds')
        else:
            return('Highscore')


sys.setrecursionlimit(int(1.6*10**4))#sets recursion limit higher to render larger grid sizes (40x40)
game = minesweeper()
game.show()
Fl.run()