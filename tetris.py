import numpy as np
from time import sleep
import curses
import random
from threading import Thread, Timer
from queue import Queue

class Shape():
	def __init__(self):
		# initial position: approx. halfway across board
		self.pos = [0,int(field_width/2)-1]
		# initial shape: randomly selected from shape array, with random rotation 0-270 degrees
		self.mat = np.rot90(random.choice(shapes),random.randint(0,3))

def main(window):
	window.nodelay(1)
	# initialize play field
	F = np.zeros((field_depth,field_width))
	# initialize new shape
	S = Shape()
	# initialize gravity timer
	q = Queue()
	t = Thread(target=gravity,args=[q])
	t.start()
	# initialize score
	lines_cleared = 0 
	thud = False
	# start game loop
	while(1):
		# display score
		window.addstr(3, 50,"SCORE: "+str(lines_cleared)) 
		# create shape overlay for play field 
		SF = np.zeros((field_depth,field_width))
		SF[S.pos[0]:S.pos[0]+(S.mat).shape[0],S.pos[1]:S.pos[1]+(S.mat).shape[1]] = S.mat
		# display play field with shape
		full_lines = []
		for i in range(0,field_depth):
			if(np.count_nonzero(F[i])==field_width):
				window.addstr(i+5,7,">>>>#"+str(F[i] + SF[i])+"#<<<<")						
				full_lines.append(i)
			else:
				window.addstr(i+5,10,"#"+str(F[i] + SF[i])+"#"+str(i+1))						
		window.refresh()

		#
		# clean up lines
		#
		if(full_lines):
			sleep(1)
			for i in full_lines:
				before = F[0:i]
				after = F[i+1:field_depth]
				F = np.append(np.zeros((1,field_width)),before,axis=0)
				F = np.append(F,after,axis=0)
				lines_cleared+=1
				window.move(i+5,0)
				window.clrtoeol()

		#
		#  player input
		#
		k = window.getch()
		if(k==27): # ESC
			break
		elif(k==260): # left
			if(move_left(S,F)):
				S.pos[1]-=1
		elif(k==261): # right
			if(move_right(S,F)):
				S.pos[1]+=1
		elif(k==258): # down
			if(move_down(S,F)):	
				S.pos[0]+=1
			else:
				thud = True
		elif(k==259): # up
			if(rotate(S,F)):
				S.mat=np.rot90(S.mat)
		elif(k!=-1):
			print(k)

		# gravity timer - move down
		if(not q.empty()):
			q.get()
			# if not at bottom, move down and keep going
			if(move_down(S,F)):	
				S.pos[0]+=1
			else:
				thud = True

		if(thud):
			# audio and flavour text
			print('\a')
			window.addstr(5+field_depth+1,15,"*THUD*")
			# set timer to remove flavour text
			tm = Timer(1.5,erase_thud,args=[window,5+field_depth+1])
			tm.start()			
			thud = False

			# add existing shape to playfield
			F = np.logical_or(F,SF)
			# initialize new shape
			S = Shape()
			# check if new shape collides with anything at top of field
			if (is_collision(S,F)):
				# if collision detected
				# refresh screen one last time with colliding shapes
				SF = np.zeros((field_depth,field_width))
				SF[S.pos[0]:S.pos[0]+(S.mat).shape[0],S.pos[1]:S.pos[1]+(S.mat).shape[1]] = S.mat
				for i in range(0,field_depth):
					window.addstr(i+5,10,"#"+str(F[i] + SF[i])+"#"+str(i+1))
				window.refresh()
				# game over
				break

	return(lines_cleared)

def gameover(window):
	# display "Game over" overlay
	window.move(8,0)
	window.clrtoeol()
	window.move(12,0)
	window.clrtoeol()
	window.addstr(9,10,"#"*35)
	window.addstr(10,10,"#" +(" "*12)+"GAME OVER" + (" "*12)+  "#")
	window.addstr(11,10,"#"*35)
	window.refresh()
	sleep(5)

def gravity(q):
	while(1):
		global stop
		if(stop):
			break
		sleep(1)
		q.put(True)

def is_collision(S,F):
	SF = np.zeros(F.shape)
	SF[S.pos[0]:S.pos[0]+(S.mat).shape[0],S.pos[1]:S.pos[1]+(S.mat).shape[1]] = S.mat
	return ((np.count_nonzero(SF*F))>0)

def move_left(S,F):
	# shape too far left?
	if (S.pos[1]-1) < 0:
		return False
	else:
		# check collisions between new position and existing play field
		SF = np.zeros(F.shape)
		SF[S.pos[0]:S.pos[0]+(S.mat).shape[0],S.pos[1]-1:S.pos[1]-1+(S.mat).shape[1]] = S.mat
		return ((np.count_nonzero(SF*F))==0)

def move_right(S,F):
	# shape too far right?
	if (S.pos[1]+1+(S.mat).shape[1]) > field_width:
		return False
	else:
		# check collisions between new position and existing play field
		SF = np.zeros(F.shape)
		SF[S.pos[0]:S.pos[0]+(S.mat).shape[0],S.pos[1]+1:S.pos[1]+1+(S.mat).shape[1]] = S.mat
		return ((np.count_nonzero(SF*F))==0)

def move_down(S,F):
	# shape hit bottom?
	if (S.pos[0]+1+(S.mat).shape[0]) > field_depth:
		return False
	else:
		# check collisions between new position and existing play field
		SF = np.zeros((field_depth,field_width))
		SF[S.pos[0]+1:S.pos[0]+1+(S.mat).shape[0],S.pos[1]:S.pos[1]+(S.mat).shape[1]] = S.mat
		return ((np.count_nonzero(SF*F))==0)

def rotate(S,F):
	rot_mat = np.rot90(S.mat)
	# would rotated shape go past right wall or bottom?
	if ((S.pos[0]+rot_mat.shape[0]) > field_depth) or ((S.pos[1]+rot_mat.shape[1]) > field_width):
		return False
	else:
		# check collisions between rotated piece and existing play field
		SF = np.zeros((field_depth,field_width))
		SF[S.pos[0]:S.pos[0]+rot_mat.shape[0],S.pos[1]:S.pos[1]+rot_mat.shape[1]] = rot_mat
		return ((np.count_nonzero(SF*F))==0)

def erase_thud(window,pos):
	window.move(pos,0)
	window.clrtoeol()

#
# initialize shapes array
#
shapes = []
# t shape  0
shapes.append(np.array([(0,1,0),(1,1,1)]))
# l1 shape  1
shapes.append(np.array([(0,0,1),(1,1,1)]))
# l2 shape  2
shapes.append(np.array([(1,0,0),(1,1,1)]))
# block shape  3
shapes.append(np.array([(1,1),(1,1)]))
# long shape  4
shapes.append(np.array([(1,1,1,1)]))
# z1 shape  5
shapes.append(np.array([(0,1,1),(1,1,0)]))
# z2 shape  6
shapes.append(np.array([(1,1,0),(0,1,1)]))
# 
# initialize play field
#
field_depth = 15
field_width = 10
#
# initialize variable that stops gravity thread  
#
stop=False

try:
	# display main game window
	score = curses.wrapper(main)
	print(">>>>> FINAL SCORE: ", score, " <<<<<")
	# stop gravity thread
	stop=True
	# display gameover window
	curses.wrapper(gameover)
except KeyboardInterrupt:
	# stop gravity thread
	stop=True
