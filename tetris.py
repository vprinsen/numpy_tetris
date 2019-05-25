# -*- coding: utf-8 -*-
# @Author: V.K. Prinsen
# @Last Modified: 2019-05-25 15:43:44

import numpy as np
from time import sleep
import curses
import random
from os import get_terminal_size
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
	curses.curs_set(0)
	# initialize play field
	F = np.zeros((field_depth,field_width))
	# initialize new shape
	S = Shape()
	# initialize gravity timer
	q = Queue()
	t = Thread(target=gravity,args=[q])
	t.start()
	# initialize other vars
	lines_cleared = 0 
	thud = False
	# display title
	window.addstr(top_offset-2, left_offset, "Numpy Tetris")
	# start game loop
	while(1):
		# display score
		window.addstr(top_offset-2, left_offset+field_width*2,"SCORE: "+str(lines_cleared)) 
		# create shape overlay for play field 
		SF = np.zeros((field_depth,field_width))
		SF[S.pos[0]:S.pos[0]+(S.mat).shape[0],S.pos[1]:S.pos[1]+(S.mat).shape[1]] = S.mat
		# display play field with shape and check for complete lines
		full_lines = []
		for i in range(0,field_depth):
			if(np.count_nonzero(F[i])==field_width):
				window.addstr(i+top_offset,left_offset-3,">>>>|"+("@"*field_width)+"|<<<<")
				full_lines.append(i)
			else:
				window.addch(i+top_offset,left_offset,ord("|"))
				for j in range(0,field_width):
					window.addch(i+top_offset,left_offset+1+j,(ord("@") if bool(F[i,j]+SF[i,j])==True else (ord(".") if show_grid_dots else ord(" "))))
				window.addstr(i+top_offset,left_offset+1+field_width, "| "+str(i))
			window.addstr(field_depth+top_offset,left_offset,("-"*(field_width+2)))						
		window.refresh()

		#
		# clean up lines
		#
		if(full_lines):
			sleep(1)
			for i in full_lines:
				F = np.append(np.zeros((1,field_width)),F[0:i],axis=0)
				F = np.append(F,F[i+1:field_depth],axis=0)
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

		# if a piece stopped
		if(thud):
			# audio and flavour text
			print('\a')
			window.addstr(top_offset+field_depth+1,left_offset+5,"*THUD*")
			# set timer to remove flavour text
			tm = Timer(1.5,erase_thud,args=[window,5+field_depth+1])
			tm.start()			
			thud = False
			# add shape to play field
			F = np.logical_or(F,SF)
			# initialize new shape
			S = Shape()
			# check if new shape collides with anything at top of field
			if (is_collision(S,F)):
				# if collision detected
				# refresh screen one last time with colliding shapes
				SF = np.zeros((field_depth,field_width))
				SF[S.pos[0]:S.pos[0]+(S.mat).shape[0],S.pos[1]:S.pos[1]+(S.mat).shape[1]] = S.mat
				for i in range(0,2):
					window.addch(i+top_offset,left_offset,ord("|"))
					for j in range(0,field_width):
						window.addch(i+top_offset,left_offset+1+j,(ord("#") if bool(F[i,j]+SF[i,j])==True else (ord(".") if show_grid_dots else ord(" "))))
					window.addstr(i+top_offset,left_offset+1+field_width, "| "+str(i))
				window.refresh()
				# game over
				break

	# return final score
	return(lines_cleared)

def gameover(window):
	# display "Game over" overlay
	window.move(8,0)
	window.clrtoeol()
	window.move(12,0)
	window.clrtoeol()
	window.addstr(top_offset+4,left_offset,"#"*35)
	window.addstr(top_offset+5,left_offset,"#" +(" "*12)+"GAME OVER" + (" "*12)+  "#")
	window.addstr(top_offset+6,left_offset,"#"*35)
	window.refresh()
	sleep(5)

def gravity(q):
	# trigger to move pieces down
	while(1):
		global stop
		if(stop):
			break
		sleep(1)
		q.put(True)

def is_collision(S,F):
	# check if collision between shape and existing play field
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
	# called to clear flavour text
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
show_grid_dots = True
top_offset = 5
left_offset = 20
# make sure positions aren't out of bounds
top_offset = min(top_offset,get_terminal_size().lines-field_depth-5)
left_offset = min(left_offset,get_terminal_size().columns-(field_width*3)-5)

#
# initialize variable that stops gravity thread  
#
stop=False

try:
	# display main game window
	score = curses.wrapper(main)
	# display final score
	print(">>>>> FINAL SCORE: ", score, " <<<<<")
	# stop gravity thread
	stop=True
	# display gameover window
	curses.wrapper(gameover)
except KeyboardInterrupt:
	# stop gravity thread
	stop=True
