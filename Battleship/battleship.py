from fltk import *
import socket, random, json


class togglebut(Fl_Button):
    def __init__(self, x, y, w, h, label, callback):
        '''compacted button creation'''
        super().__init__(x, y, w, h)
        self.color(FL_RED)
        self.callback(callback)
        self.label(label)


class opposing_tile(Fl_Button):
    def __init__(self, x, y, w, h, xpos, ypos, win):
        super().__init__(x, y, w, h)
        self.color(fl_rgb_color(255,50,49))#221
        self.xpos = xpos
        self.ypos = ypos
        self.win = win
        if not(self.xpos == 0 and self.ypos == 0):
            if self.xpos == 0:
                self.label(str(self.win.letters[self.ypos]))
            elif self.ypos == 0:
            
                self.label(str(self.win.numbers[self.xpos]))
        

class tile(Fl_Button):
    def __init__(self, x, y, w, h, xpos, ypos, win):
        super().__init__(x,y,w,h)
        self.color(221)
        self.xpos = xpos
        self.ypos = ypos
        self.win = win#access variables from player_display class
        self.callback(self.placeship)

        #puts number and letters on tiles with a 0 x or y index
        if not(self.xpos == 0 and self.ypos == 0):
            if self.xpos == 0:
                self.callback(None)
                self.label(str(self.win.letters[self.ypos]))
            elif self.ypos == 0:
                self.callback(None)
                self.label(str(self.win.numbers[self.xpos]))
    
            
    def handle(self, event):
        '''determines color to be displayed on tiles based on if the mouse position is a valid ship placement position
        calls changecolor with red if invalid and green if valid'''
        ev = super().handle(event)

        self.size = self.win.shipsize
        self.vertical = self.win.vertical

        if self.win.start:
            if event == FL_ENTER:
                if self.vertical == False:
                    if self.xpos+self.size-1 > len(self.win.grid)-1:#ship will be out of the grid
                        color = FL_RED
                    else:
                        color = FL_GREEN
                        for x in list([self.xpos+i, self.ypos] for i in range(self.size)):
                            if x in convert(self.win.shiplocations) or 0 in x:#if the ship is overlapping another
                                color = FL_RED
                else:
                    if self.ypos+self.size-1 > len(self.win.grid)-1:
                        color = FL_RED
                    else:
                        color = FL_GREEN
                        for x in list([self.xpos, self.ypos+i] for i in range(self.size)):
                            if x in convert(self.win.shiplocations) or 0 in x:
                                color = FL_RED
                self.changecolor(color)
                return 1
            elif event == FL_LEAVE:
                color = 221
                self.changecolor(color)
                return 1
            
        return ev
    def changecolor(self, color):
        '''changes color of tiles with the color specified from handle method'''
        for x in range(self.size):
            if self.vertical == False:
                if not(self.xpos+x > len(self.win.grid)-1) and [self.xpos+x, self.ypos] not in convert(self.win.shiplocations):
                    self.win.grid[self.xpos+x][self.ypos].color(color)
            else:
                if not(self.ypos+x > len(self.win.grid)-1) and [self.xpos, self.ypos+x] not in convert(self.win.shiplocations):
                    self.win.grid[self.xpos][self.ypos+x].color(color)

    def placeship(self, wid):
        '''places ship on board if valid and if only up to 4 exist'''
        ship = []

        if Fl.event_button() == FL_LEFT_MOUSE and self.win.start:
            if self.vertical == False:
                for x in list([self.xpos+i, self.ypos] for i in range(self.size)):
                    if x in convert(self.win.shiplocations) or wid.color() == FL_RED:#if the clicked position is invalid (i.e. it's highlighted in red)
                        return
                for x in range(self.size):
                    self.win.grid[self.xpos+x][self.ypos].color(FL_BLUE)
                    self.win.grid[self.xpos+x][self.ypos].redraw()
                    ship.append([self.xpos+x, self.ypos])

            else:
                for x in list([self.xpos, self.ypos+i] for i in range(self.size)):
                    if x in convert(self.win.shiplocations) or wid.color() == FL_RED:#if the clicked position is invalid (i.e. it's highlighted in red)
                        return
                for x in range(self.size):
                    self.win.grid[self.xpos][self.ypos+x].color(FL_BLUE)
                    self.win.grid[self.xpos][self.ypos+x].redraw()
                    ship.append([self.xpos, self.ypos+x])

            if self.win.shipsize > 0:
                self.win.shiplocations.append(ship)
            if self.win.shipsize == 4:
                self.win.shipsize = 0
                self.win.ready_but.activate()
            elif self.win.shipsize > 0:
                self.win.randomize_but.deactivate()
                self.win.reset_but.activate()
                self.win.shipsize += 1

        if Fl.event_button() == FL_RIGHT_MOUSE:
            self.handle(FL_LEAVE)#clear horizontal/vertical highlighting
            self.win.vertical = not(self.vertical)
            self.handle(FL_ENTER)
            self.redraw()
            

class player_display(Fl_Group):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        
        self.shots = 0
        self.hits = 0
        self.start = False #if a connection is established
        self.grid = []
        self.grid2 = []
        self.butsize = (self.w()//2//11, (self.h()-200)//11)
        self.shiplocations = []
        self.shipsize = 1
        self.vertical = False
        self.ready = False#if the user pressed the "ready" button
        self.p2ready = False#if the opponent pressed the "ready" button
        self.endgame = False#prevent clicks after a player has won

        self.powerattacks = 1
        self.togglepattack = False
        self.powerup_label = 'Power Attack'
        self.powerup_cb = self.powerattack
        
        self.checkmark = Fl_PNG_Image('checkmark.png').copy(30,30)
        self.turn_indicator = Fl_PNG_Image('dot.png').copy(30,30)

        self.letters = list(chr(x).upper() for x in range(65, 76))
        self.numbers = list(x for x in range(1,11))

        self.letters.insert(0, '')
        self.numbers.insert(0, '')

        self.begin()

        row = []
        for x in range(11):
            for y in range(11):
                row.append(tile(x*self.butsize[0], self.y()+y*self.butsize[1], self.butsize[0], self.butsize[1], x, y, self))#pass in the variables instead and if not, do for the other tile class
            self.grid.append(row)
            row = []
        
        row = []
        for x in range(11):
            for y in range(11):
                row.append(opposing_tile(506+x*self.butsize[0], self.y()+y*self.butsize[1], self.butsize[0], self.butsize[1], x, y, self))#self.send
                row[-1].callback(self.attack)
            self.grid2.append(row)
            row = []

        self.host_display = Fl_Button(0,h-100,self.w()//2,50)
        self.connect_display = Fl_Button(0,h-50,self.w()//2, 50)
        self.shot_display = Fl_Box(0, 0, 100, 50)
        self.hit_display = Fl_Box(0, 50, 100, 50)
        
        self.reset_but = Fl_Button(700, 700, self.w()//4, 60)
        self.ready_but = Fl_Button(700, 770, self.w()//4, 60)
        self.randomize_but = Fl_Button(700, 840, self.w()//4, 60)

        self.p1display = Fl_Box(0, 0, self.w()//2, self.y()-0)
        self.p2display = Fl_Box(self.w()//2, 0, self.w()//2, self.y()-0)
        self.p1ready_display = Fl_Box(130,0,100,100)  
        self.p2ready_display = Fl_Box(130+self.w()//2,0,100,100)
        self.p1turn_display = Fl_Box(self.w()//2-220,0,100,100)
        self.p2turn_display = Fl_Box(self.w()-220,0,100,100)
        
        self.powerup_button = togglebut(0,800,self.w()//2,100, self.powerup_label, self.powerup_cb)

        self.end()

        self.host_display.callback(self.but_cb, 'server')
        self.connect_display.callback(self.but_cb, 'client')
        
        self.host_display.label('Host a Game')
        self.host_display.color(fl_rgb_color(80,214,61))
        self.connect_display.label('Connect to a Game')
        self.connect_display.color(fl_rgb_color(212,61,208))

        self.shot_display.label(f'Shots: {self.shots}')
        self.shot_display.labelsize(20)
        self.shot_display.labelcolor(fl_rgb_color(0,255,255))
        self.hit_display.label(f'Hits: {self.hits}')
        self.hit_display.labelsize(20)
        self.hit_display.labelcolor(fl_rgb_color(0,255,255))

        self.p1display.label('Player 1')
        self.p2display.label('Player 2')
        self.p1display.labelsize(25)
        self.p2display.labelsize(25)

        self.reset_but.label('Reset')
        self.reset_but.color(FL_RED)
        self.reset_but.callback(self.reset)

        self.ready_but.callback(self.ready_up)
        self.ready_but.label('Ready Up')
        self.ready_but.color(FL_GREEN)

        self.randomize_but.label('Randomize')
        self.randomize_but.color(FL_DARK_CYAN)
        self.randomize_but.callback(self.randomize)

        self.ready_but.deactivate() 
        self.reset_but.deactivate()
        self.randomize_but.deactivate()
       
    def but_cb(self, wid, arg):
        '''callback for hosting and connecting to games
        server/client is specified with the arg arguement'''
        if arg == 'server':#if the player chose to be server
            self.turn = True
            self.p1turn_display.image(self.turn_indicator)
        else:
            self.turn = False
            self.p2turn_display.image(self.turn_indicator)

        name = fl_input('Enter Your Username', 'Player 1')
        fl_message_hotspot(0)
        host = fl_input('Enter Your Address', 'localhost')
        port = fl_input('Enter a Port', '12345')
        fl_message_hotspot(1)

        if None not in [name, host, port]:
            self.socket = socketapi(self, name, host, port)
            self.socket.tcpserver(arg)
            self.host_display.deactivate()
            self.connect_display.deactivate()

    def attack(self, wid):
        '''checks if the desired position to attack is valid and sends through the socket'''
        if self.togglepattack:
            if wid.xpos-1 >= 0 and wid.xpos+1 < 11 and wid.ypos-1 >= 0 and wid.ypos+1 < 11:
                msg = ['p', wid.xpos, wid.ypos]
                if self.socket.conntype == 'server':
                    self.socket.serversend(msg)
                else:
                    self.socket.clientsend(msg)
                self.powerattacks = 0
                self.powerup_button.color(FL_DARK3)
                self.powerup_button.deactivate()
                self.togglepattack = False
                self.shots += 9
                self.turn = False
                self.shot_display.label(f'Shots: {self.shots}')
                self.p1turn_display.image(None)
                self.p2turn_display.image(self.turn_indicator)

        elif self.ready and self.p2ready and (wid.xpos != 0 and wid.ypos != 0) and wid.color() != 91 and wid.color() != FL_DARK2 and self.turn and not self.endgame:
            #checks if attack is valid: both players are ready, valid pos, not already attacked, your turn, and game isn't over
            if self.socket.conntype == 'server':
                self.socket.serversend([wid.xpos, wid.ypos])
            else:
                self.socket.clientsend([wid.xpos, wid.ypos])
            self.turn = False
            self.shots += 1
            self.shot_display.label(f'Shots: {self.shots}')
            self.p1turn_display.image(None)
            self.p2turn_display.image(self.turn_indicator)

        elif self.ready and self.p2ready and not self.turn and not self.endgame:
            fl_alert('not your turn')

    def ready_up(self, wid):
        '''disables ship changes and sends other party the users name'''
        self.reset_but.deactivate()
        self.ready_but.deactivate()
        self.randomize_but.deactivate()
        if self.socket.conntype == 'server':
            self.socket.serversend(self.socket.name)
        else:
            self.socket.clientsend(self.socket.name)
        
        self.p1ready_display.image(self.checkmark)
        self.p2ready = True
        

    def reset(self, wid):
        '''remove all ships on board'''
        self.shipsize = 1
        for x in range(len(self.grid)):
            for y in range(len(self.grid)):
                self.grid[x][y].color(221)
        self.shiplocations = []
        self.reset_but.deactivate()
        self.ready_but.deactivate()
        self.randomize_but.activate()

    def randomize(self, wid):
        '''generates and returns a unique set of positions for 4 ships'''
        size = 1
        shippos = []
        taken = []#taken used to distribute position more evenly across the board by only letter unique y positions
        ship = []
        for x in range(4):
            xpos = random.randrange(1,11)
            ypos = random.randrange(1,11)
            while xpos+size-1 > 10 or ypos in taken:
                xpos = random.randrange(1,11)
                ypos = random.randrange(1,11)
            for i in range(size):
                ship.append([xpos+i, ypos])
            taken.append(ypos)
            shippos.append(ship)
            ship = []
            size += 1

        self.randomize_but.deactivate()
        self.shiplocations = shippos
        self.shipsize = 0
        self.ready_but.activate()
        self.reset_but.activate()
        for pos in convert(self.shiplocations):
            self.grid[pos[0]][pos[1]].color(FL_BLUE)

    def powerattack(self, wid):
        '''toggle powerattack variable'''
        if self.powerattacks > 0 and self.ready and self.p2ready and self.turn:
            if not self.togglepattack:
                self.togglepattack = True
                wid.color(FL_GREEN)

            else:
                self.togglepattack = False
                wid.color(FL_RED)


class socketapi(socket.socket):
    def __init__(self, display, name, host, port):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.display = display#change name
        self.name = name
        self.host = host
        self.port = port
    def tcpserver(self, conntype):
        '''create tcpserver as server/client'''
        self.conntype = conntype

        self.display.p1display.label(str(self.name))
        self.port = int(self.port)
        if self.conntype == 'server':
            self.bind((self.host, self.port))
            self.listen()
            fd = self.fileno()
            Fl.add_fd(fd, self.acceptconnections)
            game.callback(self.serverclose)
        else:
            try:
                self.connect((self.host, self.port))
            except ConnectionRefusedError:
                print('Server has not yet connected')
            else:
                self.fd = self.fileno()
                Fl.add_fd(self.fd, self.clientreceive)
                game.callback(self.clientclose)
                self.display.start = True
                self.display.randomize_but.activate()
                    
    def acceptconnections(self, fd):
        '''accept connection through connection'''
        self.conn, addr = self.accept()
        self.fd = self.conn.fileno()
        Fl.add_fd(self.fd, self.serverreceive)
        self.display.start = True#connection established
        self.display.randomize_but.activate()

    def sendconvert(self, inp):
        '''serializing and encodes list/strings'''
        inp = json.dumps(inp)
        inp = inp.encode()
        return inp

    def receiveconvert(self, inp):
        '''converts list/strings back to normal'''
        print(inp, type(inp))
        inp = json.loads(inp)
        return inp

    def serverreceive(self, fd):
        '''handles all data received from client and echoes back'''
        data = self.conn.recv(1024)

        if data.decode() == '': 
            fl_message('You Lose!')
            self.display.endgame = True
            self.conn.close()
            Fl.remove_fd(self.fd)
        else:
            data = self.receiveconvert(data) 
            if not self.display.ready:
                self.display.ready = True
                self.display.p2display.label(data)
                self.display.p2display.redraw()
                self.display.p2ready_display.image(self.display.checkmark)
            elif 'hit' in data or 'miss' in data:
                if data[0] == 'hit':
                    color = 91
                    self.display.hits += 1
                    self.display.hit_display.label(f'Hits: {self.display.hits}')
                    if self.display.hits == 10:
                        fl_message('You Win!')
                        self.display.endgame = True
                        self.serversend('')
                        self.conn.close()
                        Fl.remove_fd(self.fd)

                else:
                    color = FL_DARK2

                self.display.grid2[data[1][0]][data[1][1]].color(color)
                self.display.grid2[data[1][0]][data[1][1]].redraw()

            elif type(data) == list and data[0] == 'p':#power attack
                if len(data) < 9:#receiving the attack and echoing
                    pos = ['p']#return hit/miss for each of the 9 tiles
                    for x in range(-1, 2):
                        for y in range(-1, 2):
                            xpos = data[1]+x
                            ypos = data[2]+y
                            if (xpos > 0 and xpos < 11 and ypos > 0 and ypos < 11):
                                if self.display.grid[xpos][ypos].color() == FL_BLUE:
                                    self.display.grid[xpos][ypos].color(91)
                                    pos.append(['hit', [xpos, ypos]])
                                else:
                                    self.display.grid[xpos][ypos].color(FL_DARK2)
                                    pos.append(['miss', [xpos, ypos]])
                                self.display.grid[xpos][ypos].redraw()
            
                    self.display.turn = True
                    self.display.p1turn_display.image(self.display.turn_indicator)
                    self.display.p2turn_display.image(None)
                    self.serversend(pos)
                        
                elif len(data) == 10:#parsing the outcome of the attack (hits and misses)
                    for x in data[1:]:
                        if x[0] == 'hit':
                            self.display.grid2[x[1][0]][x[1][1]].color(91)
                            self.display.hits += 1
                            self.display.hit_display.label(f'Hits: {self.display.hits}')
                        else:
                            self.display.grid2[x[1][0]][x[1][1]].color(FL_DARK2)
                        self.display.grid2[x[1][0]][x[1][1]].redraw()

            elif type(data) == list and 'destroyed' in data:

                for pos in data[1]:
                    self.display.grid2[pos[0]][pos[1]].color(FL_BLACK)

                self.display.hits += 1
                self.display.hit_display.label(f'Hits: {self.display.hits}')

                if self.display.hits == 10:
                    fl_message('You Win!')
                    self.display.endgame = True
                    self.conn.close()
                    Fl.remove_fd(self.fd)

            else:#regular attack (clicked just one square)
                if type(data) == list:

                    n = -1

                    self.display.grid[data[0]][data[1]].redraw()
                    self.display.turn = True
                    self.display.p1turn_display.image(self.display.turn_indicator)
                    self.display.p2turn_display.image(None)

                    if self.display.grid[data[0]][data[1]].color() == FL_BLUE:
                        self.display.grid[data[0]][data[1]].color(91)
                    else:
                        self.display.grid[data[0]][data[1]].color(FL_DARK2)

                    #check if any ships are fully destroyed and turn them black     
                    for x in range(len(self.display.shiplocations)):
                        if set(list([self.display.grid[y[0]][y[1]].color() for y in self.display.shiplocations[x]])) == {91}:
                            for i in self.display.shiplocations[x]:
                                self.display.grid[i[0]][i[1]].color(FL_BLACK)
                                n = x

                    if n != -1:
                        self.serversend(['destroyed', list([i for i in self.display.shiplocations[n]])])
                        return

                    if data in convert(self.display.shiplocations):
                        self.serversend(['hit', data])
                    else:
                        self.serversend(['miss', data])

    def clientreceive(self, fd):
        '''handles all information sent from server and echoes back'''
        data = self.recv(1024)
        if data == b'':
            fl_message('You Lose!')
            self.display.endgame = True
            self.close()
            Fl.remove_fd(self.fd)
        
        else:
            data = self.receiveconvert(data)

            if not self.display.ready:
                self.display.ready = True
                self.display.p2display.label(data)
                self.display.p2display.redraw()
                self.display.p2ready_display.image(self.display.checkmark)
            elif 'hit' in data or 'miss' in data:
                if data[0] == 'hit':
                    color = 91
                    self.display.hits += 1
                    self.display.hit_display.label(f'Hits: {self.display.hits}')
                    if self.display.hits == 10:
                        fl_message('You Win!')
                        self.display.endgame = True
                        self.close()
                        Fl.remove_fd(self.fd)
                else:
                    color = FL_DARK2
                self.display.grid2[data[1][0]][data[1][1]].color(color)
                self.display.grid2[data[1][0]][data[1][1]].redraw()

            elif type(data) == list and data[0] == 'p':
                if len(data) < 9:
                    pos = ['p']
                    for x in range(-1, 2):
                        for y in range(-1, 2):
                            xpos = data[1]+x
                            ypos = data[2]+y
                            if (xpos > 0 and xpos < 11 and ypos > 0 and ypos < 11):
                                if self.display.grid[xpos][ypos].color() == FL_BLUE:
                                    self.display.grid[xpos][ypos].color(91)
                                    pos.append(['hit', [xpos, ypos]])
                                else:
                                    self.display.grid[xpos][ypos].color(FL_DARK2)
                                    pos.append(['miss', [xpos, ypos]])
                                self.display.grid[xpos][ypos].redraw()
                    self.display.turn = True
                    self.display.p1turn_display.image(self.display.turn_indicator)
                    self.display.p2turn_display.image(None)
                    self.clientsend(pos)

                elif len(data) == 10:
                    for x in data[1:]:
                        if x[0] == 'hit':
                            self.display.grid2[x[1][0]][x[1][1]].color(91)
                            self.display.hits += 1
                            self.display.hit_display.label(f'Hits: {self.display.hits}')
                        else:
                            self.display.grid2[x[1][0]][x[1][1]].color(FL_DARK2)
                        self.display.grid2[x[1][0]][x[1][1]].redraw()

            elif type(data) == list and 'destroyed' in data:
                for pos in data[1]:
                    self.display.grid2[pos[0]][pos[1]].color(FL_BLACK)
            
                self.display.hits += 1
                self.display.hit_display.label(f'Hits: {self.display.hits}')

                if self.display.hits == 10:
                    fl_message('You Win!')
                    self.display.endgame = True
                    self.close()
                    Fl.remove_fd(self.fd)

            else:
                if type(data) == list:

                    n = -1

                    self.display.grid[data[0]][data[1]].redraw()
                    self.display.turn = True
                    self.display.p1turn_display.image(self.display.turn_indicator)
                    self.display.p2turn_display.image(None)

                    if self.display.grid[data[0]][data[1]].color() == FL_BLUE:
                        self.display.grid[data[0]][data[1]].color(91)
                    else:
                        self.display.grid[data[0]][data[1]].color(FL_DARK2)

                    for x in range(len(self.display.shiplocations)):
                        if set(list([self.display.grid[y[0]][y[1]].color() for y in self.display.shiplocations[x]])) == {91}:
                            for i in self.display.shiplocations[x]:
                                self.display.grid[i[0]][i[1]].color(FL_BLACK)
                                n = x

                    if n != -1:
                        self.clientsend(['destroyed', list([i for i in self.display.shiplocations[n]])])
                        return

                    if data in convert(self.display.shiplocations):
                        self.clientsend(['hit', data])
                    else:
                        self.clientsend(['miss', data])
       
    def serversend(self, inp):
        '''sends inp arguement to client'''
        if self.display.ready or type(inp) == str:
            self.conn.sendall(self.sendconvert(inp))
        
    def clientsend(self, inp):
        '''sends inp arguement to server'''
        if self.display.ready or type(inp) == str:
            self.sendall(self.sendconvert(inp))

    def serverclose(self, wid):
        '''ends connection and closes window for server'''
        try:
            self.conn.close()
            print('closing connection')
        except AttributeError:
            print('Thank You For Using My Program!')
        finally:
            game.hide()
        
    def clientclose(self, wid):
        '''ends connection and closes window for client'''
        try:
            self.close()
            print('closing connection')
        except AttributeError:
            print('Thank You For Using My Program!')
        finally:
            game.hide()


class navalbattle(Fl_Double_Window):
    def __init__(self):
        super().__init__(Fl.w()//2-500,Fl.h()//2-400,1001,900,'Battleship')

        self.background_img = Fl_PNG_Image('background.png')
        self.background = Fl_Box(0,0,self.w(),self.h())
        self.background.image(self.background_img)
        
        self.banner = Fl_Box(0,0,self.w(),100)
        self.banner.image(Fl_PNG_Image('banner.png'))
        self.banner2 = Fl_Box(-self.w(),0,self.w()+1,100)
        self.banner2.image(Fl_PNG_Image('banner.png').copy(self.w()+1,100))

        legends = []
        colors = [FL_GREEN, FL_RED, FL_BLUE, 91, FL_DARK2, FL_BLACK]
        messages = ['Ship Outline', 'Invalid Ship Position', 'Existing Ship', 'Destroyed Ship Tile', 'Missed Shot', 'Destroyed Ship']

        self.icon(Fl_PNG_Image('logo.png'))

        fl_message_title_default('Battleship')

        Fl_add_timeout(0.1, self.animate)

        self.begin()

        player1 = player_display(0,100,self.w(),800)

        for x in range(6):
            legends.append(Fl_Button(510,705+x*33,25,25))
            legends[-1].color(colors[x])
            legends[-1].label(messages[x])
            legends[-1].align(FL_ALIGN_RIGHT)
            legends[-1].callback(self.heythere)

        self.end()

    def animate(self):
        '''moves banner and banner2 across the screen every frame'''
        self.banner.position(self.banner.x()+1,self.banner.y())
        self.banner2.position(self.banner2.x()+1,self.banner2.y())
        self.redraw()
        if self.banner.x() > 1000:
            self.banner.position(-self.w()+100,self.banner.y())
        elif self.banner2.x() > 1000:
            self.banner2.position(-self.w()+100,self.banner2.y())
        Fl_repeat_timeout(0, self.animate)

    def heythere(self, wid):
        '''this is an easter egg'''
        fl_alert('why hello there')


def convert(i):
    '''converts 2d list to 1d list'''
    s = []
    for x in i:
        for y in x:
            s.append(y)
    return s


if __name__ == "__main__":       
    Fl_scheme('gtk+')
    game = navalbattle()
    game.show()
    Fl.run()