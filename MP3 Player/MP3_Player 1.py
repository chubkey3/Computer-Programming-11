from fltk import *
import signal, os, sys, json, random
import subprocess as sp
from mutagen.mp3 import MP3

class PlaylistNameExists(Exception):
    def __init__(self, name):
        super().__init__()
        self.name = name
    def __str__(self):
        return(f'{self.name} Exists Already')


class button(Fl_Button):
    def __init__(self, x, y, w, h, callback, shortcut=None, tooltip=None, label=None, args=''):
        super().__init__(x, y, w, h, label)
        if args != '':
            self.callback(callback, args)
        else:
            self.callback(callback)
        self.shortcut(shortcut)
        self.tooltip(tooltip)
    def handle(self, event):
        retval = super().handle(event)
        if event == FL_ENTER:
            self.color(FL_RED)
            self.redraw()
            return 1
        elif event == FL_LEAVE:
            self.color(FL_BACKGROUND_COLOR)
            self.redraw()
            return 1
        else:
            return retval
    

class main(Fl_Double_Window):
    def __init__(self, w=440, h=500):
        '''args = static w, h for window'''
        '''Extra Feature: you can save all songs currently in browser as a playlist and store it to load later'''
        super().__init__(Fl.w()//2-(w//2),Fl.h()//2-(h//2),w,h,'MP3 Player')#x and y used to center screen

        self.choice = 0#stores browser index
        self.pid = 0
        self.playing = 0
        self.files = []#fnames to access song_dict
        self.song_dict = {}
        self.repeat = False
        self.shuffle = False
        self.random = []#random ints for shuffle

        self.begin()
        p = Fl_Pack(0,400,self.w(),self.h()-400)
        p.begin()
        
        previous_but = button(0,0,self.w()//5,0,self.change_pos_cb, label='@|<', args=-1, shortcut=FL_ALT + FL_Left, tooltip='Previous (Alt <-)')
        play_but = Fl_Return_Button(0,0,self.w()//5,0,'@>')
        next_but = button(0,0,self.w()//5,0,self.change_pos_cb, label='@>|',args=1, shortcut=FL_ALT + FL_Right, tooltip='Next (Alt ->)')
        stop_but = button(0,0,self.w()//5,0,self.sig_cb, label='@square', args=signal.SIGTERM, shortcut=32, tooltip='Stop (Space)')
        remove_but = button(0,0,self.w()//5,0,self.remove, label='@redo', shortcut=FL_Delete, tooltip='Remove (Del)')

        p.end()
        p.type(FL_HORIZONTAL)

        play_but.callback(self.play_cb)
        play_but.tooltip('Play (Enter)')

        self.menu_bar = Fl_Menu_Bar(0,0,self.w(),25)
        self.out = Fl_Output(0,25,self.w(),25)
        self.brow = Fl_Hold_Browser(0,50,self.w(),350)

        self.end()

        self.out.color(FL_YELLOW)
        self.out.textcolor(FL_RED)

        self.brow.callback(self.brow_cb)
        self.brow.textcolor(FL_MAGENTA)
        self.brow.textfont(FL_TIMES_BOLD)
        self.brow.color(FL_CYAN)
        self.brow.take_focus()
       
        self.callback(self.close_win)

        self.menu_bar.add('Add/Directory', ord('d'),self.add_mp3)#maybe more efficient
        self.menu_bar.add('Clear/All', FL_CTRL+ord('a'),self.clear_cb)
        self.menu_bar.add('Go/Playing', ord('p'),self.current)
        self.menu_bar.add('Go/First', ord('f'),self.first)
        self.menu_bar.add('Go/Last', ord('l'),self.last)
        self.menu_bar.add("Repeat",  ord('r'), self.repeat_cb, 0, FL_MENU_TOGGLE)
        self.menu_bar.add("Shuffle", ord('s'), self.shuffle_cb, 0, FL_MENU_TOGGLE)
        self.menu_bar.add('Save', FL_CTRL + ord('s'), self.save_cb)
    
        with open(f'playlists.json', 'r') as pfile:
            self.playlists = json.load(pfile)#playlists is a nested dictionary which keys consist of playlist names and indexes are each playlists' respective dictionary of songs/file paths
            pfile.close()

        self.load_playlists()

        self.add_mp3()

        self.resizable(self.brow)
        p.resizable(p)

    ###############json loading/saving playlists
    def save_cb(self, wid):
        '''takes all songs inside of the browser and stores/creates a user generated named dictionary of the songs'''
        pname = fl_input('Pick a Name For Your Playlist')
        if pname not in list(self.playlists.keys()) and pname != None:
            self.playlists[pname] = self.song_dict
        elif pname != None:
            raise PlaylistNameExists(pname)

        self.load_playlists()#reloads load/remove submenus

    def load_playlists(self):
        '''functions as a method used to add all the playlist names in playlists to submenus "load" and "remove"'''
        shortcut = 1
        self.menu_bar.clear_submenu(self.menu_bar.find_index("Load"))
        self.menu_bar.clear_submenu(self.menu_bar.find_index("Remove"))
        for playlist in self.playlists.keys():
            self.menu_bar.add('Load/'+playlist, ord(str(shortcut)), self.load_cb, self.playlists[playlist])
            self.menu_bar.add('Remove/'+playlist, FL_ALT + ord(str(shortcut)), self.remove_playlists, playlist)
            shortcut += 1
        self.redraw()
            
    def load_cb(self, wid, dic):
        '''input the given playlist (dic) from playlists and adds non duplicate songs from it to the current browser (loads playlists)'''
        for key in dic.keys():
            if key not in self.files:
                self.song_dict[key] = dic[key]
                self.files.append(key)
        self.choice = 0
        self.files.sort(key=str.casefold)
        self.song_dict = dict(sorted(self.song_dict.items(), key=lambda tup: tup[0].lower()))
        self.brow.clear()
        for file in self.files:
            self.brow.add(file)

    def remove_playlists(self, wid, playlist):
        '''deletes inputed playlist from playlists'''
        del self.playlists[playlist]
        self.load_playlists()#reloads load/remove submenus
    ###############

    ###############menu bar callbacks
    
    def clear_cb(self, wid):
        '''clears songs from browser and stops the music'''
        self.files = []
        self.song_dict = {}
        self.brow.clear()
        self.sig_cb('arbitrary value', signal.SIGTERM)
        self.choice = 0
        
    def first(self, wid):
        '''sets brow value to first song'''
        self.choice = 1
        self.brow.value(self.choice)

    def last(self, wid):
        '''sets brow value to last song'''
        self.choice = len(self.files)
        self.brow.value(self.choice)

    def current(self, wid):
        '''sets brow value to current song playing'''
        self.brow.value(self.playing)

    def add_mp3(self, wid=''): 
        '''adds songs from chosen directory if they are not already in browser and sorts them'''
        directory = fl_dir_chooser('Choose a Directory with Music','')
        if directory != None:
            for file in os.listdir(directory):
                if file.endswith('.mp3') and file[ :-4] not in self.files:
                    self.files.append(file)
            for x in range(len(self.files)):
                if '.mp3' in self.files[x]:
                    self.files[x] = self.files[x][:-4]
                            
            self.files.sort(key=str.casefold)
            self.brow.clear()
            for file in self.files:
                self.brow.add(file)

            for file in self.files:
                if file not in list(self.song_dict.keys()):
                    self.song_dict[file] = os.path.join(os.path.normpath(directory), f'{file}.mp3')#norm path for cross platform paths

            self.song_dict = dict(sorted(self.song_dict.items(), key=lambda tup: tup[0].lower()))
            self.random = [x+1 for x in range(len(self.files))]

    ###############

    ###############non menu bar callbacks

    def change_pos_cb(self, wid, value=1):
        '''functions as a callback to run change_pos as it was easier not to have "wid" arguement in change_pos so I put it here'''
        self.brow.take_focus()#fix shortcut errors
        self.change_pos(value)

    def generate_ran(self):
        '''popular music players like spotify don't actually make shuffle random because a truely randomized playing will result in same songs being played back to back
           this function basically ensures that the randomization doesn't play a song back to back and returns the brow index in which to play'''
        if len(self.random) == 1:
            ran = self.random[0]
            self.random = []
            self.random = [x+1 for x in range(len(self.files))]
            return(ran)
        else:
            if self.choice in self.random: 
                self.random.remove(self.choice)
            return(random.choice(self.random))#the randomizer so it's still somewhat random

    def change_pos(self, value):
        '''plays a song at the current brow pos + value and makes sure after the last song it loops to the first and vice versa'''
        if value == 0:#to prevent crashing as playing the same song twice freezes the app
            value += 1
        self.choice = self.playing
        if self.pid != 0:
            self.choice += value
            if self.choice < 1:
                self.choice = len(self.files)
            elif self.choice > len(self.files):
                self.choice = 1
            self.brow.value(self.choice)
            self.play_cb('arbitrary value')

    def sig_cb(self, wid, signal):
        '''sends signal to pid'''
        if self.pid != 0:
            self.pid.send_signal(signal)
            if signal == signal.SIGTERM:
                Fl_remove_timeout(self.change_pos)
                self.pid = 0
                self.out.value('')

    def remove(self, wid):
        '''remove the highlighted song from browser and stop playing the song if it's currently playing'''
        if self.playing == self.choice and self.pid != 0:
            self.sig_cb('arbitrary value', signal.SIGTERM)
        if self.choice != 0:
            self.brow.remove(self.choice)
            self.files.remove(self.files[self.choice-1])
            self.choice = 0
        else:
            print('Please Select a File to Remove')

    def brow_cb(self, wid):
        '''sets choice to brow value'''
        self.choice = self.brow.value()
    
    def close_win(self, wid):
        '''stops songs playing upon window exit'''
        if self.pid!=0:
            self.pid.send_signal(signal.SIGTERM)
        wid.hide()
    ###############

    ###############playling
    def shuffle_cb(self, wid, arb):#arb is arbitrary, just 0 always, ignore it
        '''sets shuffle to True or False depending on the shuffle menu bar item's state and makes sure repeat and shuffle can't be activated at the same time'''
        if self.menu_bar.find_item('Shuffle').value() == 4:
            self.shuffle = True
            if self.repeat:
                self.repeat = False
                self.change_pos(1)#skips song to prevent freezing when the same song was played again
            
            self.menu_bar.find_item('Repeat').uncheck()
        else:
            self.shuffle = False

    def repeat_cb(self, wid, arb):#arb is arbitrary, just 0 always, ignore it
        '''sets repeat to True or False depending on the repeat menu bar item's state and makes sure repeat and shuffle can't be activated at the same time'''
        if self.menu_bar.find_item('Repeat').value() == 4:
            self.repeat = True
            self.shuffle = False
            self.menu_bar.find_item('Shuffle').uncheck()
        else:
            self.repeat = False
            self.change_pos(1)#skips song to prevent freezing when the same song was played again

    def play_cb(self, wid):
        '''plays highlighted song and deals with all adding of timeouts from queuing next song to shuffle'''
        if self.pid == 0 or self.choice != self.playing:
            if self.choice == 0:
                print('Please Select a MP3 File')
            else:
                self.sig_cb('', signal.SIGTERM)
                choicepath = self.song_dict[self.files[self.choice-1]]
                choicelen = int(MP3(choicepath).info.length)#returns length of chosen song
                self.pid = sp.Popen(["vlc", "--intf", "dummy", choicepath])
                Fl.remove_timeout(self.change_pos)
                self.playing = self.choice
                self.out.value(self.files[self.choice-1])
                if self.shuffle:
                    Fl_add_timeout(choicelen, self.change_pos, self.generate_ran()-self.choice)#arguement used to find the difference needed to play what self.generate_ran returns
                elif not self.repeat:
                    Fl_add_timeout(choicelen, self.change_pos, 1)
                #if repeat is true, vlc plays the same song again so I just pass
    
                
    ###############
if not os.path.exists("playlists.json"):#writes json file for storing playlists
    pwrite = {}#write empty dictionary to pfile
    with open('playlists.json', 'w') as pfile:
        json.dump(pwrite, pfile)
        pfile.close()

Fl_scheme('plastic')
mp3_player = main()
mp3_player.show()
Fl.run()

#saves playlists
with open('playlists.json', 'w') as pfile:
    json.dump(mp3_player.playlists, pfile)
    pfile.close()