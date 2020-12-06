from fltk import *
import random, os, sys

class InvalidGridSize(Exception):# # of buttons isn't even, a string, or is more than the amount of images in the "Images" folder
    def __init__(self, buttons):
        super().__init__()
        self.button_count = buttons
    def __str__(self):
        return(f'{self.button_count} is an Invalid Amount of Buttons.')
    
class InvalidResolutionSize(Exception):#res is incorrect format or not 2 int
    def __init__(self, res):
        super().__init__()
        self.res = res
    def __str__(self):
        return(f'{self.res} is an Invalid Resolution for the Game Window')
    
class menu_cb(object):
    def __init__(self, menu_bar):
        self.help_message = '''
    Welcome to my Memory Game!
    How to Play: Click all boxes to uncover their respective images and remeber them so you can pair them up later
    Goal: Match all Pairs of Images Together to Win
    Extra Features: 
        Grid size from 2 - 2073600 boxes (but anything above 50 would not be ideal because it would freeze)
        Menu bar and score display
        High Score Ratio (click/pairs) is remembered after shutting down
        Replayablity
        Able to resize window to any REASONABLE resolution
        Images aren't hard-coded so any images in "Images" folder will be used'''
    def exit(self, wid):
        '''exits window'''
        sys.exit()
    def help(self, wid):
        '''creates window popup explaining program and features'''
        fl_message_hotspot(1)#shows popup win at mouse pos
        fl_message_title('Information About This Program')
        fl_message(self.help_message)
    def change_res(self, wid):
        '''requests resolution from user and changes window and images to that input resolution'''
        input_res = fl_input('Input New Resolution\nformat = 900,650 no spaces')
        try:#is the input resolution valid
            input_res_x = int(input_res.split(',')[0])#new w
            input_res_y = int(input_res.split(',')[1])#new h
            game.window.resize(Fl.w()//2-(input_res_x//2), Fl.h()//2-(input_res_y//2), input_res_x, input_res_y)#center win pos to middle of the screen
        except (ValueError, IndexError, AttributeError):
            raise InvalidResolutionSize(input_res)  
        if input_res_x >= Fl.w() and input_res_y >= Fl.h():#fullscreen if they input max or higher than max screen resolution 
            game.window.fullscreen()
        for but in game.buttons.keys():#iterate thru buttons
            game.unflipped_image = Fl_JPEG_Image('images.jpeg').copy(but.w(), but.h())
            but.image(game.unflipped_image.copy(but.w(), but.h()))
            but.redraw()
        game.buttonw = but.w()#change images when clicked to fit new button size
        game.buttonh = but.h()
        game.buttons_shown = []


class run_game(Fl_Window):
    def __init__(self, buttons, size=()):
        #super().__init__(w,h)
        try:
            self.button_count = int(sys.argv[1])
            print(f'Generating Custom Grid of {int(sys.argv[1])} Boxes...')
        except IndexError:
            print('Generating Default Grid of 24 Boxes...')
            self.button_count = buttons
        if type(self.button_count) != int or (self.button_count % 2 )!= 0:
            raise InvalidGridSize(self.button_count)#check if button # is invalid
        self.tries = 0
        self.w = 900#just used to make window
        self.h = 600#same thing
        
        if size == ():#runs just on just the first game to create the starting window
            self.window = Fl_Double_Window(Fl.w()//2-(self.w//2), Fl.h()//2-(self.h//2), self.w,self.h+50,f'Memory Game (WHAT IS THE GIANT EATING???)')#avoid seizures
        else:#runs so if you resize the window, it stays the same when you restart
            self.window = Fl_Double_Window(Fl.w()//2-(self.w//2), Fl.h()//2-(self.h//2), size[0], size[1], f'Memory Game (WHAT IS THE GIANT EATING???)')#if you resize and win, it still keeps res
            
        self.menu_bar = Fl_Menu_Bar(0,0,self.window.w(),25)
        self.menu_cb = menu_cb(self.menu_bar)
        self.menu_bar.add('Change Resolution', FL_F + 1, self.menu_cb.change_res)
        self.menu_bar.add('Help', FL_F + 2, self.menu_cb.help)
        self.menu_bar.add('Exit', FL_F + 3, self.menu_cb.exit)
        
        with open('highscore.txt', 'r') as file:
            self.current_hs = file.read()
            file.close()
            
        self.score_box = Fl_Box(0, self.window.h()-25, self.w, 25)
        self.score_box.label(f'Score: {self.tries}                  High Score Ratio: {self.current_hs}') #align better
        self.score_box.labelsize(24)
        
        self.nums = []
        for x in range(self.button_count//2):
            self.nums.append(x)#creates pairs
            self.nums.append(x)

        self.image_dict = {}
        self.images = os.listdir(os.getcwd()+'/Images')
        for x in range(self.button_count//2):
            self.image_dict[x] = Fl_PNG_Image('Images/'+self.images[x])
            
        self.buttons = {}
        self.active_shown = 0
        self.buttons_shown = []
        self.window.resizable(self.window)

        Fl.scheme('plastic')

    def run(self):
        '''functions as a main method'''
        self.create_buttons()
        self.display_window()
        
    def display_window(self):
        '''used to initialize fltk window'''
        self.window.redraw()
        self.window.show()
        Fl_run()

    def assign_random_int(self):
        '''returns a random int from 0-11'''
        value = random.choice(self.nums)
        self.nums.remove(value)
        return(value)

    def create_buttons(self):
        '''creates buttons, assigns random int to it, and creates a dictionary with the button object being the key and the random int being the index'''
        for x in range(self.get_median_factors(self.button_count)[1]):
            for i in range(self.get_median_factors(self.button_count)[0]):
                self.buttonw = round(self.window.w()/self.get_median_factors(self.button_count)[1])
                self.buttonh = round((self.window.h()-50)/self.get_median_factors(self.button_count)[0])#replaced self.h with self.window.h()
                self.unflipped_image = Fl_JPEG_Image('images.jpeg').copy(self.buttonw, self.buttonh)#default image when not flipped
                button = Fl_Button(self.buttonw*x, 25+self.buttonh*i, self.buttonw, self.buttonh)
                button.image(self.unflipped_image)
                button.callback(self.but_click)
                self.buttons[button] = self.assign_random_int()#creates dictionary: format = button object: value(image index when clicked)

    def but_click(self, wid):
        '''runs when a button is clicked'''
        if wid not in self.buttons_shown and wid in self.buttons:#if the widget is clicked already and isn't inactive
            self.buttons_shown.append(wid)
            self.active_shown += 1
            self.tries += 1
            self.score_box.label(f'Score: {self.tries}  High Score Ratio: {self.current_hs}')
            assigned_value = self.buttons[wid]
            wid.image(self.image_dict[assigned_value].copy(self.buttonw, self.buttonh))

        if self.active_shown == 2 and self.buttons[self.buttons_shown[0]] == self.buttons[self.buttons_shown[1]]:
            #deactivate image/button then remove from dict
            self.active_shown = 0
            self.buttons_shown[0].image().inactive()
            self.buttons_shown[1].image().inactive()
            self.buttons.pop(self.buttons_shown[0], None)
            self.buttons.pop(self.buttons_shown[1], None)
            self.buttons_shown[0].deactivate()
            self.buttons_shown[1].deactivate()
            self.buttons_shown = []
            #check if you win
            if self.buttons == {}:#no more active buttons
                fl_message_title('YOU WIN!')
                if self.high_score(self.tries) == True:
                    fl_message(f'NEW HIGH SCORE! \nYou Solved {self.button_count} Boxes in {self.tries} Clicks! \nYour Click/Match Ratio: {round(self.tries/(self.button_count//2), 3)}')
                else:
                    fl_message(f'You Won with {self.tries} Clicks! \nYou Solved {self.button_count} Boxes in {self.tries} Clicks! \nYour Click/Match Ratio: {round(self.tries/(self.button_count//2), 3)}')
                #replay; runs init again with window res
                self.__init__(self.button_count, size=(self.window.w(),self.window.h()))
                self.run()

        elif self.active_shown == 3:
            #reset widgets
            for but in self.buttons_shown:
                but.image(self.unflipped_image)
                but.redraw()
            self.buttons_shown = [wid]
            self.active_shown = 1
            wid.image(self.image_dict[assigned_value].copy(self.buttonw, self.buttonh))

    def high_score(self, score): 
            '''checks high_score and if it's lower, than it writes new high score to file'''
            score_ratio = round(self.tries/(self.button_count//2), 3)
            if self.current_hs == '' or score_ratio < float(self.current_hs): #if no high score in file or current score is lower than score in the file
                with open('highscore.txt', 'w') as file:
                    file.write(str(score_ratio))
                    file.close()
                    return(True)
            else:
                return(False)

    def get_median_factors(self, x):
        '''function used to return median factors of an int to create window with custom dimensions. e.g. 12 would be 3 and 4'''
        fac = []
        for i in range(1, x + 1):
            if x % i == 0:
                fac.append(i)
        if len(fac) % 2 == 0: #even?
            return(fac[(len(fac)//2)-1], fac[(len(fac)//2)])#return two center factors to create window (even)
        else:
            return(fac[(len(fac)//2)-1], fac[(len(fac)//2)+1])#return two center factors to create window (odd)


game = run_game(24)
game.run()
#bugs
#when you reveal one image then resize than click the matching pair, the original image isn't visible
#sort variables
#try on dif computer/linux/dif directory/with a zip
#inherit from dif fltk objects like Fl_Window and fl_message for classes and do stuff yeah bruh monke birb
